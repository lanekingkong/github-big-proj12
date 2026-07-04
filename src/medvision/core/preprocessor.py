"""
MedVision Image Preprocessor — DICOM image preprocessing pipeline.

Handles HU windowing, resampling, normalization, and augmentation
for preparing medical images for AI model inference.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class WindowPreset(str, Enum):
    LUNG = "lung"
    MEDIASTINAL = "mediastinal"
    BONE = "bone"
    BRAIN = "brain"
    ABDOMEN = "abdomen"
    LIVER = "liver"
    CUSTOM = "custom"


@dataclass
class WindowSettings:
    """CT window width/level settings."""
    width: int
    level: int
    name: str = ""

    @staticmethod
    def preset(preset: WindowPreset) -> "WindowSettings":
        """Return standard window settings for common presets."""
        presets = {
            WindowPreset.LUNG: WindowSettings(width=1500, level=-600, name="Lung"),
            WindowPreset.MEDIASTINAL: WindowSettings(width=400, level=40, name="Mediastinal"),
            WindowPreset.BONE: WindowSettings(width=1800, level=400, name="Bone"),
            WindowPreset.BRAIN: WindowSettings(width=80, level=40, name="Brain"),
            WindowPreset.ABDOMEN: WindowSettings(width=400, level=40, name="Abdomen"),
            WindowPreset.LIVER: WindowSettings(width=150, level=30, name="Liver"),
        }
        return presets.get(preset, WindowSettings(width=400, level=40, name="Default"))


class ResampleMode(str, Enum):
    NEAREST = "nearest"
    LINEAR = "linear"
    CUBIC = "cubic"


class NormalizationMethod(str, Enum):
    MINMAX = "minmax"
    ZSCORE = "zscore"
    PERCENTILE = "percentile"


@dataclass
class PreprocessingConfig:
    """Configuration for the preprocessing pipeline."""
    window: Optional[WindowSettings] = None
    target_spacing: Optional[Tuple[float, float, float]] = None  # (x, y, z) in mm
    resample_mode: ResampleMode = ResampleMode.LINEAR
    normalize: NormalizationMethod = NormalizationMethod.MINMAX
    target_size: Optional[Tuple[int, int]] = None  # (width, height)
    clip_range: Optional[Tuple[int, int]] = None  # Min/max HU values
    remove_outliers: bool = True
    outlier_std: float = 3.0


class PreprocessingPipeline:
    """
    Image preprocessing pipeline for DICOM images.

    Handles common preprocessing steps:
    1. HU value extraction (for CT)
    2. Windowing
    3. Resampling to target spacing
    4. Normalization
    5. Size standardization
    6. Outlier removal
    """

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()

    def get_presets(self) -> list[dict]:
        """Return available window presets and their parameters."""
        return [
            {"name": "lung", "width": 1500, "level": -600, "description": "Lung parenchyma"},
            {"name": "mediastinal", "width": 400, "level": 40, "description": "Mediastinal soft tissue"},
            {"name": "bone", "width": 1800, "level": 400, "description": "Bone windows"},
            {"name": "brain", "width": 80, "level": 40, "description": "Brain tissue"},
            {"name": "abdomen", "width": 400, "level": 40, "description": "Abdominal soft tissue"},
            {"name": "liver", "width": 150, "level": 30, "description": "Liver parenchyma"},
        ]

    def process_metadata_only(self, slice_count: int, slice_thickness: Optional[float] = None) -> dict:
        """
        Generate preprocessing metadata without requiring actual image data.
        Used for preview/planning when images are not loaded into memory.
        """
        info = {
            "slice_count": slice_count,
            "slice_thickness_mm": slice_thickness or 1.0,
            "window_preset": None,
            "window_width": None,
            "window_level": None,
            "normalization": self.config.normalize.value,
            "resample_mode": self.config.resample_mode.value,
            "target_spacing": self.config.target_spacing,
            "target_size": self.config.target_size,
            "steps": [],
        }

        # Build processing steps
        if self.config.window:
            info["window_preset"] = self.config.window.name
            info["window_width"] = self.config.window.width
            info["window_level"] = self.config.window.level
            info["steps"].append({
                "step": 1,
                "operation": "HU Windowing",
                "params": {
                    "width": self.config.window.width,
                    "level": self.config.window.level,
                },
            })

        if self.config.target_spacing:
            info["steps"].append({
                "step": len(info["steps"]) + 1,
                "operation": "Resampling",
                "params": {
                    "target_spacing_mm": self.config.target_spacing,
                    "mode": self.config.resample_mode.value,
                },
            })

        info["steps"].append({
            "step": len(info["steps"]) + 1,
            "operation": "Normalization",
            "params": {"method": self.config.normalize.value},
        })

        if self.config.target_size:
            info["steps"].append({
                "step": len(info["steps"]) + 1,
                "operation": "Resize",
                "params": {"target_size": self.config.target_size},
            })

        return info

    def compute_hu_bounds(self, ct_header: Optional[dict] = None) -> Tuple[float, float]:
        """Compute effective HU value range from DICOM metadata."""
        if ct_header:
            rescale_slope = ct_header.get("rescale_slope", 1.0)
            rescale_intercept = ct_header.get("rescale_intercept", 0.0)
            bits_stored = ct_header.get("bits_stored", 12)
            min_val = -(2 ** (bits_stored - 1))
            max_val = (2 ** (bits_stored - 1)) - 1
            return (
                min_val * rescale_slope + rescale_intercept,
                max_val * rescale_slope + rescale_intercept,
            )
        return (-1024.0, 3071.0)  # Default CT range

    @staticmethod
    def validate_spacing(
        current_spacing: Tuple[float, float, float],
        target_spacing: Tuple[float, float, float],
    ) -> bool:
        """Validate that resampling is feasible (within reasonable ratio)."""
        ratios = [t / c for c, t in zip(current_spacing, target_spacing)]
        return all(0.1 <= r <= 10.0 for r in ratios)

    def estimate_memory(
        self,
        slice_count: int,
        width: int = 512,
        height: int = 512,
        bytes_per_voxel: int = 2,
    ) -> Dict[str, float]:
        """Estimate memory requirements for preprocessing."""
        per_slice_bytes = width * height * bytes_per_voxel
        total_bytes = per_slice_bytes * slice_count

        # Estimates for intermediate arrays
        intermediate_mb = (total_bytes * 3) / (1024 * 1024)  # 3x for processing buffers

        return {
            "raw_mb": round(total_bytes / (1024 * 1024), 2),
            "processing_mb": round(intermediate_mb, 2),
            "total_estimated_mb": round(intermediate_mb * 1.5, 2),
            "slice_count": slice_count,
        }
