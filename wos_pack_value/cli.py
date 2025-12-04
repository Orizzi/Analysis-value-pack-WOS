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
):
    """Run ingestion + valuation + export."""
    configure_logging()
    run_pipeline(config_path=config, raw_dir=raw_dir, site_dir=site_dir)


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
