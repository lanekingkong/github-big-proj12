"""
MedVision Diagnostic Engine — Full medical imaging analysis pipeline.

Orchestrates DICOM loading, preprocessing, anomaly detection, and
radiology report generation.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from medvision.core.models import (
    DICOMStudy,
    AnalysisResult,
    RadiologyReport,
    Finding,
    FindingSeverity,
)
from medvision.core.loader import DICOMLoader
from medvision.core.detector import AnomalyDetector
from medvision.core.reporter import ReportGenerator


class DiagnosticEngine:
    """Main engine for DICOM study analysis."""

    def __init__(self, model_version: str = "1.0.0"):
        self.model_version = model_version
        self.loader = DICOMLoader()
        self.detector = AnomalyDetector()
        self.reporter = ReportGenerator()

    def load_study(self, dicom_dir: str) -> DICOMStudy:
        """Load a DICOM study from a directory."""
        return self.loader.load_study(dicom_dir)

    def detect_anomalies(self, study: DICOMStudy) -> AnalysisResult:
        """Run anomaly detection on a loaded study."""
        start_time = time.time()
        
        findings = []
        for series in study.series:
            if series.slice_count == 0:
                continue
            series_findings = self.detector.detect(series, study)
            findings.extend(series_findings)

        processing_time = time.time() - start_time

        # Compute overall confidence
        if findings:
            overall_confidence = sum(f.confidence for f in findings) / len(findings)
        else:
            overall_confidence = 0.95  # High confidence for "no findings"

        result = AnalysisResult(
            study_uid=study.study_uid,
            findings=findings,
            confidence=round(overall_confidence, 3),
            processing_time_seconds=round(processing_time, 2),
            model_version=self.model_version,
        )

        return result

    def generate_report(
        self,
        study: DICOMStudy,
        result: AnalysisResult,
    ) -> RadiologyReport:
        """Generate a structured radiology report."""
        return self.reporter.generate(study, result)

    def run_full_analysis(
        self,
        dicom_dir: str,
        output_path: Optional[str] = None,
    ) -> tuple[DICOMStudy, AnalysisResult, RadiologyReport]:
        """Run the complete analysis pipeline: load → detect → report."""
        study = self.load_study(dicom_dir)
        result = self.detect_anomalies(study)
        report = self.generate_report(study, result)

        if output_path:
            report.save(output_path)

        return study, result, report
