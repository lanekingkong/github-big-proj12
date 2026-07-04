"""
MedVision CLI — Command-line interface for medical imaging analysis.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="MedVision AI")
def cli():
    """MedVision AI: Medical Imaging Diagnostic Assistant."""
    pass


@cli.command()
@click.argument("dicom_dir", type=click.Path(exists=True))
@click.option("--output", "-o", default="report.json", help="Output report path.")
@click.option("--modality", default=None, help="Imaging modality (CT, MRI, XR, etc.). Auto-detect if not specified.")
def analyze(dicom_dir: str, output: str, modality: str):
    """Analyze a DICOM study directory and generate diagnostic findings."""
    from medvision.core.engine import DiagnosticEngine

    engine = DiagnosticEngine()
    console.print(f"[bold]Analyzing DICOM study:[/bold] {dicom_dir}")

    with Progress() as progress:
        task = progress.add_task("[cyan]Loading DICOM series...", total=None)
        study = engine.load_study(dicom_dir)
        progress.update(task, completed=100, description="[green]DICOM loaded")

    console.print(f"  Patient ID: {study.patient_id}")
    console.print(f"  Study UID: {study.study_uid}")
    console.print(f"  Modality: {study.modality}")
    console.print(f"  Series count: {len(study.series)}")
    console.print(f"  Total slices: {study.total_slices}")

    with Progress() as progress:
        task = progress.add_task("[cyan]Running anomaly detection...", total=None)
        result = engine.detect_anomalies(study)
        progress.update(task, completed=100, description="[green]Detection complete")

    # Display findings
    table = Table(title="Analysis Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Anomalies detected", str(len(result.findings)))
    table.add_row("Critical findings", str(len([f for f in result.findings if f.severity == "critical"])))
    table.add_row("Confidence score", f"{result.confidence:.3f}")

    if result.findings:
        f_table = Table(title="Findings")
        f_table.add_column("ID", style="cyan")
        f_table.add_column("Region", style="yellow")
        f_table.add_column("Type", style="magenta")
        f_table.add_column("Severity", style="red")
        f_table.add_column("Confidence")

        for i, finding in enumerate(result.findings, 1):
            f_table.add_row(
                str(i), finding.region, finding.finding_type,
                finding.severity.upper(), f"{finding.confidence:.3f}"
            )
        console.print(f_table)

    # Generate report
    report = engine.generate_report(study, result)
    report.save(output)
    console.print(f"[bold green]Report saved → {output}[/bold green]")


@cli.command()
@click.argument("dicom_file", type=click.Path(exists=True))
def info(dicom_file: str):
    """Display DICOM header metadata for a single file."""
    from medvision.core.loader import DICOMLoader

    loader = DICOMLoader()
    metadata = loader.read_metadata(dicom_file)

    table = Table(title=f"DICOM Metadata: {dicom_file}")
    table.add_column("Tag", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Value", style="yellow")

    for tag, name, value in metadata:
        table.add_row(tag, name, str(value))

    console.print(table)


@cli.command()
@click.argument("dicom_dir", type=click.Path(exists=True))
@click.option("--output", "-o", default="dicom_report.pdf", help="Output PDF report path.")
def report(dicom_dir: str, output: str):
    """Generate a structured radiology report (PDF) from a DICOM study."""
    from medvision.core.engine import DiagnosticEngine

    engine = DiagnosticEngine()
    console.print(f"[bold]Generating radiology report for:[/bold] {dicom_dir}")

    study = engine.load_study(dicom_dir)
    result = engine.detect_anomalies(study)
    report = engine.generate_report(study, result)
    report.export_pdf(output)
    console.print(f"[bold green]PDF report saved → {output}[/bold green]")
    console.print(report.summary())


@cli.command()
@click.argument("dicom_dir", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="./preprocessed", help="Output directory.")
def preprocess(dicom_dir: str, output_dir: str):
    """Preprocess DICOM images: normalize, resize, window/level adjustment."""
    import os
    from medvision.core.preprocessor import DICOMPreprocessor

    os.makedirs(output_dir, exist_ok=True)
    preprocessor = DICOMPreprocessor()
    console.print(f"[bold]Preprocessing DICOM from:[/bold] {dicom_dir}")

    stats = preprocessor.process_directory(dicom_dir, output_dir)
    console.print(f"[bold green]Preprocessing complete.[/bold green]")
    console.print(f"  Files processed: {stats['processed']}")
    console.print(f"  Normalized: {stats['normalized']}")
    console.print(f"  Resized: {stats['resized']}")
    console.print(f"  Output: {output_dir}")


if __name__ == "__main__":
    cli()
