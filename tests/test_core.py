"""Tests for MedVision AI - DICOM models, loader, detector, reporter, and preprocessor."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from medvision.core.models import (
    DICOMStudy,
    DICOMSeries,
    Finding,
    FindingType,
    FindingSeverity,
    ImagingModality,
    AnalysisResult,
    RadiologyReport,
)
from medvision.core.loader import DICOMLoader
from medvision.core.detector import AnomalyDetector
from medvision.core.reporter import ReportGenerator
from medvision.core.preprocessor import (
    PreprocessingPipeline,
    PreprocessingConfig,
    WindowSettings,
    WindowPreset,
    NormalizationMethod,
)
from medvision.core.engine import DiagnosticEngine


# ─── Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def sample_study():
    """Create a sample DICOM study for testing."""
    return DICOMStudy(
        study_uid="1.2.840.113619.2.55.3.1234567",
        patient_id="P000123",
        patient_name="Test Patient",
        patient_age=45,
        patient_sex="M",
        study_date=datetime(2026, 6, 15),
        modality="CT",
        study_description="CT Chest",
        accession_number="A12345",
        institution_name="Test Hospital",
        referring_physician="Dr. Test",
        series=[
            DICOMSeries(
                series_uid="1.2.840.113619.2.55.3.1234567.1",
                series_number=1,
                modality="CT",
                description="Chest scan",
                slice_count=200,
                slice_thickness=1.0,
            ),
        ],
    )


@pytest.fixture
def empty_dir():
    """Create an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ─── Model Tests ─────────────────────────────────────────────────────────

class TestDICOMStudy:
    """Tests for DICOMStudy."""

    def test_total_slices(self, sample_study):
        assert sample_study.total_slices == 200

    def test_summary(self, sample_study):
        summary = sample_study.summary()
        assert summary["patient_id"] == "P000123"
        assert summary["modality"] == "CT"
        assert summary["series_count"] == 1
        assert summary["total_slices"] == 200


class TestFinding:
    """Tests for Finding."""

    def test_to_dict(self):
        finding = Finding(
            id="F001",
            finding_type=FindingType.NODULE,
            region="right_upper_lobe",
            severity=FindingSeverity.HIGH,
            confidence=0.92,
            description="Suspicious nodule",
            measurements={"diameter_mm": 12.5},
        )
        d = finding.to_dict()
        assert d["type"] == "nodule"
        assert d["severity"] == "high"
        assert d["confidence"] == 0.92


class TestAnalysisResult:
    """Tests for AnalysisResult."""

    def test_critical_findings(self):
        findings = [
            Finding(id="1", finding_type=FindingType.NODULE, region="lung", severity=FindingSeverity.CRITICAL, confidence=0.95),
            Finding(id="2", finding_type=FindingType.CALCIFICATION, region="lung", severity=FindingSeverity.LOW, confidence=0.80),
        ]
        result = AnalysisResult(study_uid="test", findings=findings)
        assert len(result.critical_findings) == 1
        assert result.has_critical

    def test_no_critical(self):
        result = AnalysisResult(study_uid="test", findings=[])
        assert not result.has_critical


class TestRadiologyReport:
    """Tests for RadiologyReport."""

    def test_summary(self, sample_study):
        findings = [
            Finding(id="1", finding_type=FindingType.NODULE, region="right_upper_lobe", severity=FindingSeverity.HIGH, confidence=0.90, description="Suspicious nodule"),
        ]
        report = RadiologyReport(
            study_uid=sample_study.study_uid,
            patient_id=sample_study.patient_id,
            modality="CT",
            study_date="2026-06-15",
            findings=findings,
            impression="Follow-up recommended",
            recommendations=["Follow-up CT in 3 months"],
            generated_at=datetime.now(),
            report_text="Test report",
        )
        summary = report.summary()
        assert "RADIOLOGY REPORT" in summary
        assert "P000123" in summary
        assert "Suspicious nodule" in summary

    def test_save(self, sample_study):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        report = RadiologyReport(
            study_uid=sample_study.study_uid,
            patient_id=sample_study.patient_id,
            modality="CT",
            study_date="2026-06-15",
            findings=[],
            impression="Normal",
            generated_at=datetime.now(),
            report_text="Normal study.",
        )
        report.save(output_path)

        with open(output_path, "r") as f:
            data = json.load(f)
        assert data["impression"] == "Normal"
        Path(output_path).unlink(missing_ok=True)


# ─── Loader Tests ────────────────────────────────────────────────────────

class TestDICOMLoader:
    """Tests for DICOMLoader."""

    def test_load_simulated_study(self, empty_dir):
        loader = DICOMLoader()
        study = loader.load_study(empty_dir)
        assert isinstance(study, DICOMStudy)
        assert study.patient_id
        assert len(study.series) >= 1

    def test_read_metadata(self, empty_dir):
        loader = DICOMLoader()
        metadata = loader.read_metadata("nonexistent.dcm")
        assert len(metadata) >= 10
        assert any(tag[0] == "(0008,0060)" for tag in metadata)

    def test_deterministic_output(self, empty_dir):
        """Same seed should produce same simulated study."""
        l1 = DICOMLoader()
        l2 = DICOMLoader()
        s1 = l1.load_study(empty_dir)
        s2 = l2.load_study(empty_dir)
        assert s1.study_uid == s2.study_uid


# ─── Detector Tests ──────────────────────────────────────────────────────

class TestAnomalyDetector:
    """Tests for AnomalyDetector."""

    def test_detection_returns_findings(self, sample_study):
        detector = AnomalyDetector(seed=42)
        series = sample_study.series[0]
        findings = detector.detect(series, sample_study)
        # Findings count depends on study characteristics
        assert isinstance(findings, list)
        for f in findings:
            assert isinstance(f, Finding)
            assert 0 <= f.confidence <= 1

    def test_deterministic_detection(self, sample_study):
        """Same study should produce identical findings."""
        d1 = AnomalyDetector(seed=42)
        d2 = AnomalyDetector(seed=42)
        f1 = d1.detect(sample_study.series[0], sample_study)
        f2 = d2.detect(sample_study.series[0], sample_study)
        assert len(f1) == len(f2)
        for i in range(len(f1)):
            assert f1[i].id == f2[i].id


# ─── Reporter Tests ──────────────────────────────────────────────────────

class TestReportGenerator:
    """Tests for ReportGenerator."""

    def test_generate_report(self, sample_study):
        engine = DiagnosticEngine()
        result = engine.detect_anomalies(sample_study)
        report = ReportGenerator().generate(sample_study, result)
        assert isinstance(report, RadiologyReport)
        assert report.patient_id == sample_study.patient_id
        assert report.impression

    def test_generate_empty_study(self, sample_study):
        """Report for study with no findings."""
        result = AnalysisResult(study_uid=sample_study.study_uid, findings=[])
        report = ReportGenerator().generate(sample_study, result)
        assert "No significant abnormalities" in report.report_text
        assert report.impression
        assert len(report.recommendations) >= 1


# ─── Preprocessor Tests ─────────────────────────────────────────────────

class TestWindowSettings:
    """Tests for WindowSettings."""

    def test_preset_lung(self):
        ws = WindowSettings.preset(WindowPreset.LUNG)
        assert ws.width == 1500
        assert ws.level == -600

    def test_preset_brain(self):
        ws = WindowSettings.preset(WindowPreset.BRAIN)
        assert ws.width == 80
        assert ws.level == 40


class TestPreprocessingPipeline:
    """Tests for PreprocessingPipeline."""

    def test_process_metadata(self):
        config = PreprocessingConfig(
            window=WindowSettings.preset(WindowPreset.LUNG),
            normalize=NormalizationMethod.MINMAX,
        )
        pipeline = PreprocessingPipeline(config)
        info = pipeline.process_metadata_only(slice_count=200, slice_thickness=1.0)
        assert info["slice_count"] == 200
        assert len(info["steps"]) >= 2

    def test_estimate_memory(self):
        pipeline = PreprocessingPipeline()
        mem = pipeline.estimate_memory(slice_count=300)
        assert mem["slice_count"] == 300
        assert mem["raw_mb"] > 0
        assert mem["total_estimated_mb"] > mem["raw_mb"]

    def test_get_presets(self):
        pipeline = PreprocessingPipeline()
        presets = pipeline.get_presets()
        assert len(presets) >= 5
        assert any(p["name"] == "lung" for p in presets)

    def test_validate_spacing(self):
        valid = PreprocessingPipeline.validate_spacing(
            current_spacing=(1.0, 1.0, 5.0),
            target_spacing=(1.0, 1.0, 3.0),
        )
        assert valid

    def test_invalid_spacing(self):
        valid = PreprocessingPipeline.validate_spacing(
            current_spacing=(1.0, 1.0, 5.0),
            target_spacing=(0.01, 0.01, 50.0),  # Too extreme
        )
        assert not valid


# ─── Engine Tests ───────────────────────────────────────────────────────

class TestDiagnosticEngine:
    """Tests for DiagnosticEngine."""

    def test_load_study(self, empty_dir):
        engine = DiagnosticEngine()
        study = engine.load_study(empty_dir)
        assert isinstance(study, DICOMStudy)
        assert len(study.series) >= 1

    def test_full_analysis(self, empty_dir):
        engine = DiagnosticEngine()
        study, result, report = engine.run_full_analysis(empty_dir)
        assert isinstance(study, DICOMStudy)
        assert isinstance(result, AnalysisResult)
        assert isinstance(report, RadiologyReport)
        assert report.study_uid == study.study_uid

    def test_analysis_export(self, empty_dir):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        engine = DiagnosticEngine()
        study, result, report = engine.run_full_analysis(empty_dir, output_path=output_path)

        with open(output_path, "r") as f:
            data = json.load(f)
        assert "impression" in data
        assert data["study_uid"] == study.study_uid
        Path(output_path).unlink(missing_ok=True)
