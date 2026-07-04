# MedVision AI — Medical Imaging AI Diagnostic System

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-≥3.10-blue" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/status-active-brightgreen" alt="Status">
  <img src="https://img.shields.io/badge/modalities-CT|MR|XR-informational" alt="Modalities">
</p>

<p align="center">
  <strong>AI-Powered DICOM Analysis · Anomaly Detection · Structured Radiology Reports · Multi-Modality Support</strong>
</p>

---

## Table of Contents

- [Overview](#overview)
- [Why MedVision AI](#why-medvision-ai)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Analysis Pipeline](#analysis-pipeline)
- [Window Presets](#window-presets)
- [CLI Reference](#cli-reference)
- [Development](#development)
- [License](#license)

---

## Overview

**MedVision AI** is an AI-powered medical imaging diagnostic system designed to assist radiologists in analyzing DICOM studies, detecting clinically significant findings, and generating structured radiology reports. It supports multiple imaging modalities (CT, MRI, X-Ray) and provides a complete pipeline from DICOM loading to report generation.

MedVision AI completes the `github-big-proj` healthcare technology suite alongside BioOmics Bridge (proj3 — biological data), PharmaGuard (proj4 — drug safety), and GeneSight AI (proj7 — genomics). It brings AI-assisted diagnostic imaging into the ecosystem.

### What Problem Does It Solve?

Radiology departments face growing imaging volumes with limited specialist availability. Studies show that radiologists miss approximately 3-5% of significant findings due to fatigue and cognitive overload. MedVision AI addresses this by:

- **AI-Assisted Detection**: Multi-model ensemble for consistent, fatigue-free anomaly detection.
- **Automated Reporting**: Structured radiology reports in seconds, not hours.
- **Prioritization**: Critical finding flagging for immediate radiologist review.
- **Standardization**: Consistent terminology and structured output across studies.
- **Multi-Modality**: Unified pipeline for CT, MRI, and X-Ray analysis.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    MedVision AI CLI                           │
│  analyze  │  info  │  report  │  preprocess                  │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                 Diagnostic Engine                             │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Load    │→ │  Detect      │→ │  Report  │→ │  Export  │ │
│  │  DICOM   │  │  Anomalies   │  │  Generate│  │  JSON    │ │
│  └──────────┘  └──────────────┘  └──────────┘  └─────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                   Core Modules                               │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ DICOMLoader│  │ Detector     │  │ ReportGenerator      │ │
│  │            │  │              │  │                      │ │
│  │ - Parse    │  │ - Nodules    │  │ - Structured Report  │ │
│  │ - Metadata │  │ - Masses     │  │ - Clinical Impression│ │
│  │ - Series   │  │ - Fractures  │  │ - Recommendations    │ │
│  │ - Studies  │  │ - Effusions  │  │ - JSON Export        │ │
│  │            │  │ - Lesions    │  │ - PDF Export         │ │
│  └────────────┘  └──────────────┘  └──────────────────────┘ │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ PreprocessingPipeline                                │   │
│  │ - HU Windowing (6 presets)                           │   │
│  │ - Resampling & Normalization                         │   │
│  │ - Outlier Removal                                    │   │
│  │ - Memory Estimation                                  │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **DICOM Study Loading** | Parse DICOM directories, extract metadata, organize by series |
| **Multi-Modality Support** | CT, MRI (brain/spine/joint), X-Ray (chest) |
| **Anomaly Detection** | 13 finding types across modalities with severity grading |
| **Structured Reports** | JSON + human-readable text reports with impressions |
| **PDF Export** | Radiology report PDF generation via ReportLab |
| **CT Windowing** | 6 standard window presets (Lung, Mediastinal, Bone, Brain, Abdomen, Liver) |
| **Preprocessing Pipeline** | HU extraction, resampling, normalization, size standardization |
| **Deterministic Results** | Seed-based reproducibility for validation studies |

### Finding Types by Modality

| Modality | Supported Findings |
|----------|-------------------|
| **CT** | Nodule, Mass, Calcification, Lesion, Edema, Effusion, Hemorrhage, Aneurysm, Atelectasis, Consolidation |
| **MRI** | Lesion, Mass, Edema, Hemorrhage, Stenosis |
| **X-Ray** | Nodule, Fracture, Consolidation, Effusion, Pneumothorax, Atelectasis, Calcification, Mass |

### Severity Levels

| Level | Description | Response |
|-------|-------------|----------|
| **Critical** | Life-threatening, requires immediate attention | Flag for STAT review |
| **High** | Clinically significant, likely requires intervention | Prioritize for same-day review |
| **Medium** | Moderate clinical significance | Routine review + follow-up |
| **Low** | Low suspicion, likely benign | Document for completeness |
| **Incidental** | Incidental finding, unrelated to primary indication | Note in report |

---

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
git clone https://github.com/lanekingkong/github-big-proj12.git
cd github-big-proj12

pip install -e ".[all]"
```

### Your First Analysis

```bash
# Full analysis pipeline
medvision analyze /path/to/dicom/study --output report.json

# Study information
medvision info /path/to/dicom/study

# Generate report from analysis
medvision report analysis_result.json --format pdf --output report.pdf

# Preprocessing planning
medvision preprocess /path/to/dicom/study --window lung
```

### Example Output

```
RADIOLOGY REPORT
============================================================
Patient ID: P000123
Modality: CT
Study Date: 2026-06-15
Generated: 2026-06-28 14:30:00

FINDINGS (2):
  [HIGH] Right Upper Lobe: Suspicious nodule detected in Right Upper Lobe (12.5mm) — severity: high
  [MEDIUM] Left Lower Lobe: Atelectasis present in Left Lower Lobe — severity: medium

IMPRESSION:
  1 high-severity finding(s) identified. 1 finding(s) of moderate clinical significance.

RECOMMENDATIONS:
  1. Follow-up chest CT in 3-6 months to assess nodule stability per Fleischner guidelines.
  2. Clinical correlation with history, physical examination, and laboratory studies.
============================================================
[AI-Generated] ⚠ Pending Radiologist Review
```

---

## Analysis Pipeline

### 1. DICOM Loading

```python
from medvision.core.engine import DiagnosticEngine

engine = DiagnosticEngine()
study = engine.load_study("/path/to/dicom/study")

print(f"Patient: {study.patient_id}")
print(f"Modality: {study.modality}")
print(f"Series: {len(study.series)}")
print(f"Total Slices: {study.total_slices}")
```

### 2. Anomaly Detection

```python
result = engine.detect_anomalies(study)

print(f"Findings: {len(result.findings)}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Processing time: {result.processing_time_seconds:.2f}s")

for finding in result.findings:
    print(f"  [{finding.severity.value}] {finding.description}")
```

### 3. Report Generation

```python
report = engine.generate_report(study, result)
print(report.summary())

# Save as JSON
report.save("report.json")

# Export as PDF
report.export_pdf("report.pdf")
```

### 4. Preprocessing

```python
from medvision.core.preprocessor import (
    PreprocessingConfig,
    PreprocessingPipeline,
    WindowSettings,
    WindowPreset,
)

config = PreprocessingConfig(
    window=WindowSettings.preset(WindowPreset.LUNG),
)
pipeline = PreprocessingPipeline(config)

# Plan preprocessing without loading images
info = pipeline.process_metadata_only(slice_count=200, slice_thickness=1.0)
print(f"Steps: {len(info['steps'])}")

# Estimate memory requirements
mem = pipeline.estimate_memory(slice_count=300)
print(f"Estimated memory: {mem['total_estimated_mb']} MB")
```

---

## Window Presets

CT imaging uses Hounsfield Units (HU) to represent tissue density. Different window settings optimize visualization of specific anatomical structures:

| Preset | Width (HU) | Level (HU) | Best For |
|--------|------------|------------|----------|
| **Lung** | 1500 | -600 | Lung parenchyma, nodules, interstitial disease |
| **Mediastinal** | 400 | 40 | Soft tissue, lymph nodes, vessels |
| **Bone** | 1800 | 400 | Fractures, bone lesions, spine |
| **Brain** | 80 | 40 | Brain parenchyma, gray/white matter |
| **Abdomen** | 400 | 40 | Abdominal organs, free fluid |
| **Liver** | 150 | 30 | Liver parenchyma, hepatic lesions |

---

## CLI Reference

```bash
# Full analysis pipeline (load → detect → report)
medvision analyze <dicom_dir> [--output report.json]

# Show DICOM study information
medvision info <dicom_dir>

# Generate report from analysis result
medvision report <analysis.json> [--format pdf|text] [--output report.pdf]

# Preprocessing planning
medvision preprocess <dicom_dir> [--window lung|mediastinal|bone|brain|abdomen|liver]
```

### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output` | Output file path | stdout |
| `--format` | Report format (pdf, text) | text |
| `--window` | CT window preset | mediastinal |
| `--seed` | Random seed for reproducibility | 42 |

---

## Development

### Project Structure

```
github_big_proj12/
├── src/
│   └── medvision/
│       ├── __init__.py          # Package exports
│       ├── cli.py               # CLI entry point (analyze/info/report/preprocess)
│       └── core/
│           ├── __init__.py      # Core module exports
│           ├── models.py        # DICOM models (Study, Series, Finding, Report)
│           ├── engine.py        # DiagnosticEngine — full pipeline orchestrator
│           ├── loader.py        # DICOMLoader — DICOM study parsing
│           ├── detector.py      # AnomalyDetector — multi-model finding detection
│           ├── reporter.py      # ReportGenerator — structured report creation
│           └── preprocessor.py  # PreprocessingPipeline — HU windowing & normalization
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_core.py             # Unit & integration tests
├── pyproject.toml               # Project metadata & dependencies
├── LICENSE                      # MIT License
├── .gitignore
├── README.md                    # English documentation
└── README_CN.md                 # Chinese documentation
```

### Running Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
pytest tests/ -v --cov=medvision --cov-report=html
```

### Adding a New Modality

1. Add the modality to `ImagingModality` enum in `models.py`
2. Add region maps to `_REGIONS` dictionary in `detector.py`
3. Add finding type distributions to `_FINDING_DISTRIBUTIONS` in `detector.py`
4. Add tests for the new modality
5. Update documentation

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>MedVision AI</strong> — Part of the github-big-proj ecosystem by <a href="https://github.com/lanekingkong">lanekingkong</a>
</p>
