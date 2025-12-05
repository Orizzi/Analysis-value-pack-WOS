"""CLI entrypoint using Typer."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import typer

from .export.json_export import export_site_json
from .ingestion.pipeline import ingest_all
from .logging_utils import configure_logging
from .pipeline import run_pipeline
from .valuation.pipeline import valuate

app = typer.Typer(add_completion=False, help="Whiteout Survival pack value toolkit")


@app.command()
def run(
    config: Optional[Path] = typer.Option(None, help="Path to valuation config YAML"),
    raw_dir: Optional[Path] = typer.Option(None, help="Override raw data directory"),
    site_dir: Optional[Path] = typer.Option(None, help="Override site_data output directory"),
    use_ocr_screenshots: bool = typer.Option(False, help="Enable OCR ingestion from screenshots directory"),
    screenshots_dir: Optional[Path] = typer.Option(None, help="Path to screenshots for OCR"),
    ocr_lang: str = typer.Option("eng", help="Language code for OCR (pytesseract)"),
    ingestion_config: Optional[Path] = typer.Option(None, help="Path to ingestion config (reference handling)"),
    reference_mode: Optional[str] = typer.Option(None, help="Override reference handling mode (tag/exclude/separate)"),
    summary_only: bool = typer.Option(False, help="Run without writing outputs; print summary"),
    log_file: Optional[Path] = typer.Option(None, help="Optional log file path"),
):
    """Run ingestion + valuation + export."""
    configure_logging(log_file=log_file)
    run_pipeline(
        config_path=config,
        raw_dir=raw_dir,
        site_dir=site_dir,
        use_ocr=use_ocr_screenshots,
        screenshots_dir=screenshots_dir,
        ocr_lang=ocr_lang,
        ingestion_config_path=ingestion_config,
        reference_mode_override=reference_mode,
        summary_only=summary_only,
        log_file=log_file,
    )


@app.command()
def ingest(raw_dir: Path = typer.Option(None, help="Override raw data directory")):
    """Run only ingestion."""
    configure_logging()
    kwargs = {}
    if raw_dir:
        kwargs["raw_dir"] = raw_dir
    packs, _ = ingest_all(**kwargs)
    typer.echo(f"Ingested {len(packs)} packs")


@app.command()
def value(
    config: Optional[Path] = typer.Option(None, help="Path to valuation config"),
    processed: Optional[Path] = typer.Option(None, help="Path to processed packs JSON"),
):
    """Run valuation from processed packs."""
    configure_logging()
    kwargs = {}
    if processed:
        kwargs["processed_path"] = processed
    valued, _ = valuate(config_path=config, **kwargs)
    typer.echo(f"Valuated {len(valued)} packs")


@app.command()
def export(
    config: Optional[Path] = typer.Option(None, help="Path to valuation config"),
    processed: Optional[Path] = typer.Option(None, help="Path to processed packs JSON"),
    site_dir: Optional[Path] = typer.Option(None, help="Override site_data output directory"),
):
    """Value and export packs to site_data JSON."""
    configure_logging()
    kwargs = {}
    if processed:
        kwargs["processed_path"] = processed
    valued, _ = valuate(config_path=config, **kwargs)
    export_site_json(valued_packs=valued, items=None, site_dir=site_dir or None)
    typer.echo("Exported site JSON")


@app.command()
def sanity():
    """Quick sanity run with console logging."""
    configure_logging(level=logging.INFO)
    valued, _ = run_pipeline()
    top = sorted(valued, key=lambda p: p.valuation.score, reverse=True)[:3]
    typer.echo("Top packs:")
    for vp in top:
        typer.echo(f"- {vp.pack.name}: score={vp.valuation.score}, ratio={vp.valuation.ratio}")


def main():
    app()


if __name__ == "__main__":
    main()
