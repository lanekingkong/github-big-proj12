"""
MedVision Anomaly Detector — AI-based medical anomaly detection.

Simulates a multi-model ensemble detection pipeline for identifying
clinically significant findings in medical imaging studies.
"""

from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List, Optional

from medvision.core.models import (
    DICOMStudy,
    DICOMSeries,
    Finding,
    FindingType,
    FindingSeverity,
    ImagingModality,
)


# ─── Anatomical Region Maps by Modality ────────────────────────────────────

_REGIONS = {
    ImagingModality.CT: {
        "chest": [
            "right_upper_lobe", "right_middle_lobe", "right_lower_lobe",
            "left_upper_lobe", "left_lower_lobe", "mediastinum",
            "right_hilum", "left_hilum", "pleura",
        ],
        "abdomen": [
            "liver", "right_kidney", "left_kidney", "spleen",
            "pancreas", "gallbladder", "adrenal_gland", "aorta",
        ],
        "head": [
            "right_frontal_lobe", "left_frontal_lobe", "right_parietal_lobe",
            "left_parietal_lobe", "right_temporal_lobe", "left_temporal_lobe",
            "brainstem", "cerebellum",
        ],
    },
    ImagingModality.MRI: {
        "brain": [
            "right_frontal_lobe", "left_frontal_lobe", "right_parietal_lobe",
            "left_parietal_lobe", "right_temporal_lobe", "left_temporal_lobe",
            "occipital_lobe", "cerebellum", "brainstem", "corpus_callosum",
        ],
        "spine": [
            "cervical_spine", "thoracic_spine", "lumbar_spine",
            "intervertebral_disc", "spinal_cord",
        ],
        "joint": [
            "right_knee", "left_knee", "right_shoulder", "left_shoulder",
            "right_hip", "left_hip",
        ],
    },
    ImagingModality.XRAY: {
        "chest": [
            "right_upper_lobe", "right_middle_lobe", "right_lower_lobe",
            "left_upper_lobe", "left_lower_lobe", "costophrenic_angle",
            "cardiac_silhouette", "trachea",
        ],
    },
}

# ─── Finding Type Distributions by Modality ────────────────────────────────

_FINDING_DISTRIBUTIONS: Dict[ImagingModality, List[tuple[FindingType, float]]] = {
    ImagingModality.CT: [
        (FindingType.NODULE, 0.25),
        (FindingType.MASS, 0.10),
        (FindingType.CALCIFICATION, 0.08),
        (FindingType.LESION, 0.15),
        (FindingType.EDEMA, 0.07),
        (FindingType.EFFUSION, 0.10),
        (FindingType.HEMORRHAGE, 0.05),
        (FindingType.ANEURYSM, 0.05),
        (FindingType.ATELECTASIS, 0.05),
        (FindingType.CONSOLIDATION, 0.05),
        (FindingType.OTHER, 0.05),
    ],
    ImagingModality.MRI: [
        (FindingType.LESION, 0.30),
        (FindingType.MASS, 0.12),
        (FindingType.EDEMA, 0.15),
        (FindingType.HEMORRHAGE, 0.10),
        (FindingType.STENOSIS, 0.10),
        (FindingType.ATELECTASIS, 0.03),
        (FindingType.OTHER, 0.20),
    ],
    ImagingModality.XRAY: [
        (FindingType.NODULE, 0.15),
        (FindingType.FRACTURE, 0.20),
        (FindingType.CONSOLIDATION, 0.15),
        (FindingType.EFFUSION, 0.12),
        (FindingType.PNEUMOTHORAX, 0.08),
        (FindingType.ATELECTASIS, 0.10),
        (FindingType.CALCIFICATION, 0.05),
        (FindingType.MASS, 0.05),
        (FindingType.OTHER, 0.10),
    ],
}

_SEVERITY_WEIGHTS = [
    (FindingSeverity.CRITICAL, 0.05),
    (FindingSeverity.HIGH, 0.10),
    (FindingSeverity.MEDIUM, 0.25),
    (FindingSeverity.LOW, 0.30),
    (FindingSeverity.INCIDENTAL, 0.30),
]


class AnomalyDetector:
    """
    Multi-model ensemble anomaly detector for medical imaging.

    In production, this would integrate:
    - CNN-based lesion detectors (RetinaNet, YOLO-med, nnUNet)
    - Transformer-based classification (ViT-B/16)
    - Ensemble voting with confidence calibration
    """

    def __init__(self, seed: int = 42, models: Optional[List[str]] = None):
        self._rng = random.Random(seed)
        self._models = models or [
            "MedVision-LesionNet-v2",
            "MedVision-NoduleRCNN-v1",
            "MedVision-FractureDet-v1",
        ]

    def detect(self, series: DICOMSeries, study: DICOMStudy) -> list[Finding]:
        """
        Detect anomalies in a single DICOM series.

        Returns list of Findings with confidence scores.
        """
        modality = self._infer_modality(series, study)
        
        # Determine relevant anatomical regions
        regions = self._get_regions(modality)
        if not regions:
            return []

        # Generate findings based on study characteristics
        num_findings = self._determine_finding_count(study, series)
        findings: list[Finding] = []

        for i in range(num_findings):
            finding = self._generate_finding(
                series=series,
                study=study,
                modality=modality,
                regions=regions,
                index=i,
            )
            findings.append(finding)

        return findings

    def _infer_modality(
        self, series: DICOMSeries, study: DICOMStudy
    ) -> ImagingModality:
        """Infer the imaging modality from series metadata."""
        modality_str = (series.modality or study.modality or "CT").upper()
        try:
            return ImagingModality(modality_str)
        except ValueError:
            return ImagingModality.CT

    def _get_regions(self, modality: ImagingModality) -> list[str]:
        """Get anatomical regions for a given modality."""
        all_regions = []
        for region_group in _REGIONS.get(modality, {}).values():
            all_regions.extend(region_group)
        return list(all_regions) if all_regions else ["unspecified"]

    def _determine_finding_count(
        self, study: DICOMStudy, series: DICOMSeries
    ) -> int:
        """Determine expected number of findings using study characteristics."""
        # Use study UID as seed for deterministic results
        seed_val = int(hashlib.md5(series.series_uid.encode()).hexdigest()[:8], 16)
        local_rng = random.Random(seed_val)

        base_prob = 0.3  # 30% chance of each slice having a finding
        if study.patient_age and study.patient_age > 60:
            base_prob += 0.15  # Older patients have higher finding rates

        # Poisson-like distribution
        expected = series.slice_count * base_prob * 0.05  # Scale factor
        count = max(0, int(local_rng.gauss(expected, 1.0)))

        return min(count, 20)  # Cap at 20 findings

    def _generate_finding(
        self,
        series: DICOMSeries,
        study: DICOMStudy,
        modality: ImagingModality,
        regions: list[str],
        index: int,
    ) -> Finding:
        """Generate a single finding with realistic characteristics."""
        seed_val = int(hashlib.md5(f"{series.series_uid}:{index}".encode()).hexdigest()[:8], 16)
        local_rng = random.Random(seed_val)

        # Select finding type based on modality
        type_options, type_weights = zip(*_FINDING_DISTRIBUTIONS.get(modality, [(FindingType.OTHER, 1.0)]))
        finding_type = local_rng.choices(list(type_options), weights=list(type_weights), k=1)[0]

        # Select region
        region = local_rng.choice(regions)

        # Select severity
        sev_options, sev_weights = zip(*_SEVERITY_WEIGHTS)
        severity = local_rng.choices(list(sev_options), weights=list(sev_weights), k=1)[0]

        # Confidence
        confidence = round(local_rng.uniform(0.65, 0.99), 3)

        # Measurements
        measurements = {}
        if finding_type in (FindingType.NODULE, FindingType.MASS, FindingType.LESION):
            diameter = round(local_rng.uniform(3.0, 45.0), 1)
            measurements["diameter_mm"] = diameter
            measurements["volume_mm3"] = round((4/3) * 3.14159 * (diameter/2)**3, 1)
        elif finding_type == FindingType.EFFUSION:
            measurements["depth_mm"] = round(local_rng.uniform(5.0, 50.0), 1)
        elif finding_type == FindingType.STENOSIS:
            measurements["percentage"] = round(local_rng.uniform(10.0, 95.0), 1)

        # Description
        description = self._generate_description(finding_type, region, measurements, severity)

        finding_id = f"F{seed_val:06d}"

        return Finding(
            id=finding_id,
            finding_type=finding_type,
            region=region,
            severity=severity,
            confidence=confidence,
            description=description,
            measurements=measurements,
            series_uid=series.series_uid,
            slice_index=local_rng.randint(0, max(0, series.slice_count - 1)),
        )

    def _generate_description(
        self,
        finding_type: FindingType,
        region: str,
        measurements: Dict[str, float],
        severity: FindingSeverity,
    ) -> str:
        """Generate a natural language description of a finding."""
        region_display = region.replace("_", " ").title()

        type_descriptions = {
            FindingType.NODULE: f"Suspicious nodule detected in {region_display}",
            FindingType.MASS: f"Soft tissue mass identified in {region_display}",
            FindingType.CALCIFICATION: f"Calcification noted in {region_display}",
            FindingType.FRACTURE: f"Fracture line observed in {region_display}",
            FindingType.HEMORRHAGE: f"Acute hemorrhage in {region_display}",
            FindingType.LESION: f"Hyperintense lesion in {region_display}",
            FindingType.EDEMA: f"Cerebral edema in {region_display}",
            FindingType.EFFUSION: f"Pleural effusion in {region_display}",
            FindingType.PNEUMOTHORAX: f"Pneumothorax evident in {region_display}",
            FindingType.ATELECTASIS: f"Atelectasis present in {region_display}",
            FindingType.CONSOLIDATION: f"Pulmonary consolidation in {region_display}",
            FindingType.ANEURYSM: f"Aneurysmal dilation of {region_display}",
            FindingType.STENOSIS: f"Stenosis detected in {region_display}",
            FindingType.OTHER: f"Abnormality in {region_display}",
        }

        desc = type_descriptions.get(finding_type, f"Finding in {region_display}")

        if measurements:
            parts = []
            for key, value in measurements.items():
                label = key.replace("_", " ")
                parts.append(f"{value}{'%' if 'percentage' in key else 'mm'}")
            desc += f" ({', '.join(parts)})"

        desc += f" — severity: {severity.value}"

        return desc
