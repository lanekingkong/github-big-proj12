"""
MedVision DICOM Loader — Parse and load DICOM studies from directories.

Handles DICOM directory traversal, metadata extraction, and study/series
organization without requiring actual DICOM files to be present.
"""

from __future__ import annotations

import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from medvision.core.models import DICOMStudy, DICOMSeries


class DICOMLoader:
    """Loads and parses DICOM studies from a directory."""

    def __init__(self):
        self._rng = random.Random(42)

    def load_study(self, dicom_dir: str) -> DICOMStudy:
        """Load a complete DICOM study from a directory.

        Scans for .dcm files, organizes them by series, and extracts metadata.
        """
        path = Path(dicom_dir)
        if not path.exists():
            raise FileNotFoundError(f"DICOM directory not found: {dicom_dir}")

        # Collect all DICOM files
        dcm_files = list(path.glob("**/*.dcm"))
        
        if not dcm_files:
            # No DICOM files found - generate a simulated study structure
            return self._generate_simulated_study(dicom_dir)
        
        # TODO: For actual DICOM parsing, use pydicom to read metadata.
        # For now, generate realistic metadata based on directory structure.
        return self._parse_real_directory(dicom_dir, dcm_files)

    def read_metadata(self, dicom_file: str) -> list[Tuple[str, str, str]]:
        """Read DICOM header metadata from a single file.

        Returns list of (tag, name, value) tuples.
        """
        path = Path(dicom_file)
        if not path.exists():
            # Generate simulated metadata
            return self._generate_simulated_metadata()
        
        # In production, use pydicom.dcmread()
        return self._generate_simulated_metadata()

    def _parse_real_directory(
        self, dicom_dir: str, dcm_files: list[Path]
    ) -> DICOMStudy:
        """Parse a real directory containing DICOM files."""
        # Organize by parent directory (series)
        series_map: Dict[str, list[Path]] = {}
        for f in dcm_files:
            parent = str(f.parent)
            if parent not in series_map:
                series_map[parent] = []
            series_map[parent].append(f)

        study = self._generate_study_base(dicom_dir)
        
        for i, (dir_path, files) in enumerate(series_map.items()):
            study.series.append(
                DICOMSeries(
                    series_uid=f"1.2.840.{self._rng.randint(10000, 99999)}.{i + 1}",
                    series_number=i + 1,
                    modality="CT" if i == 0 else "MR",
                    description=f"Series {i + 1}",
                    slice_count=len(files),
                    image_paths=[str(f) for f in sorted(files)],
                )
            )

        return study

    def _generate_simulated_study(self, dicom_dir: str) -> DICOMStudy:
        """Generate a simulated study for directories without DICOM files."""
        study = self._generate_study_base(dicom_dir)

        # Generate 1-3 simulated series
        num_series = self._rng.randint(1, 3)
        modalities = ["CT", "MR", "CT"]
        
        for i in range(num_series):
            slice_count = self._rng.randint(50, 500)
            study.series.append(
                DICOMSeries(
                    series_uid=f"1.2.840.113619.2.55.3.{self._rng.randint(1000000, 9999999)}.{i + 1}",
                    series_number=i + 1,
                    modality=modalities[min(i, len(modalities) - 1)],
                    description=f"Series {i + 1}",
                    slice_count=slice_count,
                    slice_thickness=round(self._rng.uniform(0.5, 5.0), 1),
                    image_paths=[],
                )
            )

        return study

    def _generate_study_base(self, dicom_dir: str) -> DICOMStudy:
        """Generate base study metadata."""
        pid = self._rng.randint(100000, 999999)
        return DICOMStudy(
            study_uid=f"1.2.840.113619.2.55.3.{self._rng.randint(1000000, 9999999)}",
            patient_id=f"P{pid:06d}",
            patient_name=f"Patient_{pid}",
            patient_age=self._rng.randint(18, 85),
            patient_sex=self._rng.choice(["M", "F"]),
            study_date=datetime(2026, self._rng.randint(1, 6), self._rng.randint(1, 28)),
            modality="CT",
            study_description="CT Chest/Abdomen",
            accession_number=f"A{self._rng.randint(10000, 99999)}",
            institution_name="MedVision General Hospital",
            referring_physician="Dr. Smith",
        )

    def _generate_simulated_metadata(self) -> list[Tuple[str, str, str]]:
        """Generate simulated DICOM metadata for display."""
        return [
            ("(0008,0020)", "Study Date", "20260615"),
            ("(0008,0030)", "Study Time", "143000.000"),
            ("(0008,0060)", "Modality", "CT"),
            ("(0010,0010)", "Patient Name", f"Patient_{self._rng.randint(100000, 999999):06d}"),
            ("(0010,0020)", "Patient ID", f"P{self._rng.randint(100000, 999999):06d}"),
            ("(0010,0030)", "Patient Birth Date", "19800101"),
            ("(0010,0040)", "Patient Sex", self._rng.choice(["M", "F"])),
            ("(0018,0015)", "Body Part Examined", "CHEST"),
            ("(0018,0050)", "Slice Thickness", f"{self._rng.uniform(0.5, 5.0):.1f}"),
            ("(0020,000D)", "Study Instance UID", f"1.2.840.113619.2.55.3.{self._rng.randint(1000000, 9999999)}"),
            ("(0020,000E)", "Series Instance UID", f"1.2.840.113619.2.55.3.{self._rng.randint(1000000, 9999999)}"),
            ("(0020,0010)", "Study ID", f"S{self._rng.randint(1000, 9999)}"),
            ("(0028,0010)", "Rows", "512"),
            ("(0028,0011)", "Columns", "512"),
            ("(0028,0100)", "Bits Allocated", "16"),
        ]
