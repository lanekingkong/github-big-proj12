"""
MedVision AI Core Models — Medical imaging domain models.

Defines DICOM study, series, image data, analysis results, and
structured radiology report entities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ImagingModality(str, Enum):
    CT = "CT"
    MRI = "MR"
    XRAY = "XR"
    ULTRASOUND = "US"
    PET = "PT"
    MAMMOGRAPHY = "MG"
    ANGIOGRAPHY = "XA"
    NUCLEAR = "NM"
    UNKNOWN = "OT"


class FindingSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INCIDENTAL = "incidental"


class FindingType(str, Enum):
    NODULE = "nodule"
    MASS = "mass"
    CALCIFICATION = "calcification"
    FRACTURE = "fracture"
    HEMORRHAGE = "hemorrhage"
    LESION = "lesion"
    EDEMA = "edema"
    EFFUSION = "effusion"
    PNEUMOTHORAX = "pneumothorax"
    ATELECTASIS = "atelectasis"
    CONSOLIDATION = "consolidation"
    ANEURYSM = "aneurysm"
    STENOSIS = "stenosis"
    OTHER = "other"


@dataclass
class DICOMSeries:
    """A DICOM series within a study."""
    series_uid: str
    series_number: int = 0
    modality: str = ""
    description: str = ""
    slice_count: int = 0
    slice_thickness: Optional[float] = None
    image_paths: List[str] = field(default_factory=list)


@dataclass
class DICOMStudy:
    """A complete DICOM study containing one or more series."""
    study_uid: str
    patient_id: str = ""
    patient_name: str = ""
    patient_age: Optional[int] = None
    patient_sex: str = ""
    study_date: Optional[datetime] = None
    modality: str = ""
    study_description: str = ""
    accession_number: str = ""
    institution_name: str = ""
    referring_physician: str = ""
    series: List[DICOMSeries] = field(default_factory=list)

    @property
    def total_slices(self) -> int:
        return sum(s.slice_count for s in self.series)

    def summary(self) -> Dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "study_uid": self.study_uid,
            "modality": self.modality,
            "study_date": str(self.study_date) if self.study_date else "Unknown",
            "series_count": len(self.series),
            "total_slices": self.total_slices,
        }


@dataclass
class Finding:
    """A single finding detected in the imaging study."""
    id: str
    finding_type: FindingType
    region: str  # Anatomical region (e.g., "right_upper_lobe", "left_kidney")
    severity: FindingSeverity
    confidence: float  # 0-1
    description: str = ""
    bbox: Optional[Dict[str, int]] = None  # {"x": 0, "y": 0, "w": 0, "h": 0}
    measurements: Dict[str, float] = field(default_factory=dict)  # e.g., {"diameter_mm": 12.5}
    series_uid: Optional[str] = None
    slice_index: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.finding_type.value,
            "region": self.region,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "description": self.description,
            "measurements": self.measurements,
        }


@dataclass
class AnalysisResult:
    """Complete analysis result for a DICOM study."""
    study_uid: str
    findings: List[Finding] = field(default_factory=list)
    confidence: float = 0.0  # Overall analysis confidence
    processing_time_seconds: float = 0.0
    model_version: str = "1.0.0"
    warnings: List[str] = field(default_factory=list)

    @property
    def critical_findings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == FindingSeverity.CRITICAL]

    @property
    def has_critical(self) -> bool:
        return len(self.critical_findings) > 0


@dataclass
class RadiologyReport:
    """Structured radiology report."""
    study_uid: str
    patient_id: str = ""
    modality: str = ""
    study_date: str = ""
    findings: List[Finding] = field(default_factory=list)
    impression: str = ""
    recommendations: List[str] = field(default_factory=list)
    generated_at: Optional[datetime] = None
    radiologist_review: bool = False
    report_text: str = ""

    def summary(self) -> str:
        lines = [
            f"RADIOLOGY REPORT",
            f"{'='*60}",
            f"Patient ID: {self.patient_id}",
            f"Modality: {self.modality}",
            f"Study Date: {self.study_date}",
            f"Generated: {self.generated_at}",
            f"",
            f"FINDINGS ({len(self.findings)}):",
        ]
        for f in self.findings:
            lines.append(f"  [{f.severity.value.upper()}] {f.region}: {f.description}")
        lines.append(f"")
        lines.append(f"IMPRESSION:")
        lines.append(f"  {self.impression}")
        if self.recommendations:
            lines.append(f"RECOMMENDATIONS:")
            for r in self.recommendations:
                lines.append(f"  - {r}")
        lines.append(f"{'='*60}")
        lines.append(f"[AI-Generated] {'✓ Reviewed' if self.radiologist_review else '⚠ Pending Radiologist Review'}")
        return "\n".join(lines)

    def save(self, output_path: str):
        """Save report as JSON."""
        import json
        report_data = {
            "study_uid": self.study_uid,
            "patient_id": self.patient_id,
            "modality": self.modality,
            "study_date": self.study_date,
            "findings": [f.to_dict() for f in self.findings],
            "impression": self.impression,
            "recommendations": self.recommendations,
            "generated_at": str(self.generated_at),
            "report_text": self.report_text,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

    def export_pdf(self, output_path: str):
        """Export report as PDF (text-based fallback)."""
        from pathlib import Path
        out = Path(output_path)
        if out.suffix.lower() == ".pdf":
            # Generate a simple text-based PDF
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                c = canvas.Canvas(str(out), pagesize=A4)
                y = 800
                for line in self.summary().split("\n"):
                    c.drawString(50, y, line)
                    y -= 14
                    if y < 50:
                        c.showPage()
                        y = 800
                c.save()
            except ImportError:
                # Fallback to text
                text_path = out.with_suffix(".txt")
                text_path.write_text(self.summary(), encoding="utf-8")
