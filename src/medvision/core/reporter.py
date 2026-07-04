"""
MedVision Report Generator — Structured radiology report generation.

Generates human-readable radiology reports from detected findings,
with impression synthesis and clinical recommendations.
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from medvision.core.models import (
    DICOMStudy,
    AnalysisResult,
    RadiologyReport,
    Finding,
    FindingSeverity,
    FindingType,
)


class ReportGenerator:
    """Generates structured radiology reports with AI assistance."""

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def generate(
        self,
        study: DICOMStudy,
        result: AnalysisResult,
        include_recommendations: bool = True,
    ) -> RadiologyReport:
        """Generate a complete radiology report."""
        
        findings_text = self._format_findings(result.findings)
        impression = self._generate_impression(result.findings)
        recommendations = self._generate_recommendations(result.findings) if include_recommendations else []

        report_text_parts = [
            f"Patient ID: {study.patient_id}",
            f"Modality: {study.modality}",
            f"Study Date: {study.study_date.strftime('%Y-%m-%d') if study.study_date else 'Unknown'}",
            f"Study Description: {study.study_description}",
            f"",
            f"FINDINGS:",
            findings_text,
            f"",
            f"IMPRESSION:",
            impression,
        ]
        if recommendations:
            report_text_parts.append("")
            report_text_parts.append("RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                report_text_parts.append(f"  {i}. {rec}")

        return RadiologyReport(
            study_uid=study.study_uid,
            patient_id=study.patient_id,
            modality=study.modality,
            study_date=str(study.study_date) if study.study_date else "Unknown",
            findings=result.findings,
            impression=impression,
            recommendations=recommendations,
            generated_at=datetime.now(),
            report_text="\n".join(report_text_parts),
        )

    def _format_findings(self, findings: list[Finding]) -> str:
        """Format findings into structured text."""
        if not findings:
            return "  No significant abnormalities detected."

        # Sort by severity (critical first)
        severity_order = {
            FindingSeverity.CRITICAL: 0,
            FindingSeverity.HIGH: 1,
            FindingSeverity.MEDIUM: 2,
            FindingSeverity.LOW: 3,
            FindingSeverity.INCIDENTAL: 4,
        }
        sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.severity, 99))

        lines = []
        for finding in sorted_findings:
            prefix = {
                FindingSeverity.CRITICAL: "[CRITICAL]",
                FindingSeverity.HIGH: "[HIGH]",
                FindingSeverity.MEDIUM: "[MEDIUM]",
                FindingSeverity.LOW: "[LOW]",
                FindingSeverity.INCIDENTAL: "[INCIDENTAL]",
            }.get(finding.severity, "[UNKNOWN]")
            
            confidence_pct = f"{finding.confidence * 100:.0f}%"
            lines.append(f"  {prefix} {finding.description} (confidence: {confidence_pct})")

        return "\n".join(lines)

    def _generate_impression(self, findings: list[Finding]) -> str:
        """Generate a clinical impression based on findings."""
        if not findings:
            return "No significant abnormalities. Normal study."

        critical = [f for f in findings if f.severity == FindingSeverity.CRITICAL]
        high = [f for f in findings if f.severity == FindingSeverity.HIGH]
        medium = [f for f in findings if f.severity == FindingSeverity.MEDIUM]
        low = [f for f in findings if f.severity == FindingSeverity.LOW]

        impressions = []

        if critical:
            critical_types = {f.finding_type.value for f in critical}
            impressions.append(
                f"ACUTE FINDING: {len(critical)} critical finding(s) including "
                f"{', '.join(sorted(critical_types))}. Requires immediate clinical attention."
            )

        if high:
            high_types = {f.finding_type.value for f in high}
            impressions.append(
                f"{len(high)} high-severity finding(s) identified ({', '.join(sorted(high_types))}). "
                "Clinical correlation recommended."
            )

        if medium:
            impressions.append(
                f"{len(medium)} finding(s) of moderate clinical significance. "
                "Consider follow-up imaging."
            )

        if low:
            impressions.append(
                f"{len(low)} low-severity finding(s), likely benign. "
                "Routine follow-up as clinically indicated."
            )

        if not impressions:
            impressions.append("Findings are of uncertain clinical significance.")

        return " ".join(impressions)

    def _generate_recommendations(self, findings: list[Finding]) -> list[str]:
        """Generate clinical recommendations based on findings."""
        recommendations: list[str] = []

        critical = [f for f in findings if f.severity == FindingSeverity.CRITICAL]
        high = [f for f in findings if f.severity == FindingSeverity.HIGH]

        if critical:
            recommendations.append(
                "IMMEDIATE: Notify referring physician of critical findings. "
                "Consider urgent specialist consultation."
            )

        nodule_findings = [f for f in findings if f.finding_type == FindingType.NODULE]
        if nodule_findings and any(
            f.measurements.get("diameter_mm", 0) > 8 for f in nodule_findings
        ):
            recommendations.append(
                "Follow-up chest CT in 3-6 months to assess nodule stability per Fleischner guidelines."
            )

        if high and not critical:
            recommendations.append(
                "Clinical correlation with history, physical examination, and laboratory studies."
            )

        fracture_findings = [f for f in findings if f.finding_type == FindingType.FRACTURE]
        if fracture_findings:
            recommendations.append(
                "Orthopedic consultation recommended for fracture management."
            )

        mass_findings = [f for f in findings if f.finding_type == FindingType.MASS]
        if mass_findings:
            recommendations.append(
                "Consider biopsy or further characterization with contrast-enhanced imaging."
            )

        if findings and not recommendations:
            recommendations.append(
                "Correlation with clinical findings. Follow-up as clinically indicated."
            )

        if not findings:
            recommendations.append(
                "No further imaging recommended at this time."
            )

        return recommendations
