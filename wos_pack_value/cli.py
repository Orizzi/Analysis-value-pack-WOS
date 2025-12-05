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
    with_analysis: bool = typer.Option(False, help="Run analysis ranking after pipeline"),
    analysis_config: Optional[Path] = typer.Option(None, help="Path to analysis config YAML/JSON"),
):
    """Run ingestion + valuation + export."""
    configure_logging(log_file=log_file)
    valued, _ = run_pipeline(
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
    if with_analysis and not summary_only:
        from .analysis.ranking import analyze_from_site_data

        analyze_from_site_data(site_dir or None, config_path=analysis_config, output_dir=site_dir or None)


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
def analyze(
    site_dir: Optional[Path] = typer.Option(None, help="Directory containing site_data packs/items"),
    analysis_config: Optional[Path] = typer.Option(None, help="Path to analysis config YAML/JSON"),
    output_dir: Optional[Path] = typer.Option(None, help="Output directory for ranking exports"),
):
    """Run ranking analysis on existing site_data exports."""
    from .analysis.ranking import analyze_from_site_data

    configure_logging()
    analyze_from_site_data(site_dir=site_dir or None, config_path=analysis_config, output_dir=output_dir or site_dir or None)
    typer.echo("Analysis completed")


@app.command()
def plan(
    site_dir: Optional[Path] = typer.Option(None, help="Directory containing site_data exports"),
    budget: float = typer.Option(..., help="Total budget to allocate"),
    currency: str = typer.Option("USD", help="Currency label (for display)"),
    max_count: Optional[int] = typer.Option(None, help="Maximum number of packs to include"),
    include_reference: bool = typer.Option(False, help="Include reference/library packs"),
    output_file: Optional[Path] = typer.Option(None, help="Optional JSON output path for the plan"),
    profile: str = typer.Option("default", help="Planner profile (reserved for future use)"),
):
    """Suggest packs to buy under a budget using existing rankings."""
    from .analysis.budget_planner import load_site_data, plan_budget, export_plan_json

    configure_logging()
    if budget <= 0:
        typer.echo("Budget must be greater than 0.")
        raise typer.Exit(code=1)
    try:
        packs = load_site_data(site_dir or None)
    except FileNotFoundError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1)

    selected, summary = plan_budget(
        packs=packs,
        budget=budget,
        currency=currency,
        max_count=max_count,
        include_reference=include_reference,
    )

    typer.echo(f"Budget planner (profile: {profile}, currency: {currency})")
    typer.echo(f"Budget: {budget:.2f}")
    typer.echo(f"Packs considered: {summary.considered}, excluded: {summary.excluded}")
    if not selected:
        typer.echo("No packs selected within budget.")
    else:
        typer.echo("Selected packs:")
        for idx, p in enumerate(selected, start=1):
            typer.echo(
                f"  {idx}) {p.name} – price: {p.price:.2f}, value: {p.total_value:.2f}, value_per_dollar: {p.value_per_dollar:.2f}, rank: {p.rank_overall or '?'}"
            )
    typer.echo(f"Total spent: {summary.total_spent:.2f}")
    typer.echo(f"Remaining budget: {summary.remaining_budget:.2f}")
    typer.echo(f"Total value: {summary.total_value:.2f}")
    typer.echo(f"Average value_per_dollar (selected): {summary.average_value_per_dollar:.2f}")

    if output_file:
        output_path = output_file
    elif site_dir:
        output_path = site_dir / "budget_plan.json"
    else:
        output_path = Path("site_data") / "budget_plan.json"

    export_plan_json(selected, summary, output_path=output_path, profile=profile)
    typer.echo(f"Plan written to {output_path}")


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
