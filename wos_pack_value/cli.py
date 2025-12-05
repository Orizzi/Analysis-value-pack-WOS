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
    ocr_review_dump: Optional[Path] = typer.Option(None, help="Path to write raw OCR review dump JSON"),
    ocr_reviewed_path: Optional[Path] = typer.Option(None, help="Path to reviewed OCR packs JSON"),
    ingestion_config: Optional[Path] = typer.Option(None, help="Path to ingestion config (reference handling)"),
    reference_mode: Optional[str] = typer.Option(None, help="Override reference handling mode (tag/exclude/separate)"),
    summary_only: bool = typer.Option(False, help="Run without writing outputs; print summary"),
    log_file: Optional[Path] = typer.Option(None, help="Optional log file path"),
    with_analysis: bool = typer.Option(False, help="Run analysis ranking after pipeline"),
    analysis_config: Optional[Path] = typer.Option(None, help="Path to analysis config YAML/JSON"),
    no_validation: bool = typer.Option(False, help="Skip validation checks/report"),
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
        enable_validation=not no_validation,
        ocr_review_dump_path=ocr_review_dump,
        ocr_reviewed_path=ocr_reviewed_path,
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
    profile: Optional[str] = typer.Option(None, help="Player profile name for profile-specific ranking"),
    profiles_path: Optional[Path] = typer.Option(None, help="Path to player profiles config"),
):
    """Run ranking analysis on existing site_data exports."""
    from .analysis.ranking import analyze_from_site_data

    configure_logging()
    analyze_from_site_data(
        site_dir=site_dir or None,
        config_path=analysis_config,
        output_dir=output_dir or site_dir or None,
        profile_name=profile,
        profiles_path=profiles_path,
    )
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
    profiles_path: Optional[Path] = typer.Option(None, help="Path to player profiles config"),
):
    """Suggest packs to buy under a budget using existing rankings."""
    from .analysis.budget_planner import load_site_data, plan_budget, export_plan_json
    from .analysis.player_profiles import get_profile

    configure_logging()
    if budget <= 0:
        typer.echo("Budget must be greater than 0.")
        raise typer.Exit(code=1)
    try:
        packs = load_site_data(site_dir or None)
    except FileNotFoundError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1)

    profile_obj = get_profile(profile, config_path=profiles_path)
    selected, summary = plan_budget(
        packs=packs,
        budget=budget,
        currency=currency,
        max_count=max_count,
        include_reference=include_reference,
        profile=profile_obj,
    )

    typer.echo(f"Budget planner (profile: {profile_obj.name}, currency: {currency})")
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
def goal(
    site_dir: Optional[Path] = typer.Option(None, help="Directory containing site_data exports"),
    target: str = typer.Option(..., help="Target item name or id (substring match)"),
    amount: float = typer.Option(..., help="Desired amount of the target item"),
    budget: Optional[float] = typer.Option(None, help="Maximum budget; if omitted, planner minimizes cost to reach target"),
    currency: str = typer.Option("USD", help="Currency label (display only)"),
    profile: str = typer.Option("default", help="Player profile for tie-breaking"),
    include_reference: bool = typer.Option(False, help="Include reference/library packs"),
    output_file: Optional[Path] = typer.Option(None, help="Optional JSON output path for the goal plan"),
    profiles_path: Optional[Path] = typer.Option(None, help="Path to player profiles config"),
):
    """Plan purchases to reach a target item amount within a budget."""
    from .analysis.goal_planner import plan_for_goal, export_goal_plan_json
    from .analysis.player_profiles import get_profile

    configure_logging()
    if not target or amount <= 0:
        typer.echo("Target and amount are required (amount must be > 0).")
        raise typer.Exit(code=1)
    site_dir_path = site_dir or Path("site_data")
    profile_obj = get_profile(profile, config_path=profiles_path)
    try:
        result = plan_for_goal(
            site_dir=site_dir_path,
            target_name=target,
            target_amount=amount,
            budget=budget,
            currency=currency,
            include_reference=include_reference,
            profile=profile_obj,
        )
    except FileNotFoundError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1)

    typer.echo("Goal planner")
    typer.echo(f"  Target item: {target}")
    typer.echo(f"  Requested amount: {amount}")
    typer.echo(f"  Budget: {budget if budget is not None else 'None'} {currency}")
    typer.echo(f"  Profile: {profile_obj.name}")
    typer.echo(f"  Packs considered: {result.summary.considered}, excluded: {result.summary.excluded}")
    if not result.selected:
        typer.echo("No packs selected.")
    else:
        typer.echo("Selected packs:")
        for idx, p in enumerate(result.selected, start=1):
            cpu = p.cost_per_unit if p.cost_per_unit != float("inf") else None
            cpu_display = f"{cpu:.4f}" if cpu is not None else "n/a"
            typer.echo(
                f"  {idx}) {p.name} – price: {p.price:.2f}, target qty: {p.target_quantity:.2f}, cost/unit: {cpu_display}"
            )
    typer.echo("Summary:")
    typer.echo(f"  Total target amount from plan: {result.summary.target_amount_obtained}")
    typer.echo(f"  Total spent: {result.summary.total_spent:.2f}")
    if result.summary.remaining_budget is not None:
        typer.echo(f"  Remaining budget: {result.summary.remaining_budget:.2f}")
    if result.summary.effective_cost_per_unit is not None:
        typer.echo(f"  Effective cost per unit (target): {result.summary.effective_cost_per_unit:.4f} {currency}")
    if result.summary.notes:
        typer.echo("Notes:")
        for n in result.summary.notes:
            typer.echo(f"  - {n}")

    if output_file:
        output_path = output_file
    else:
        output_path = site_dir_path / "goal_plan.json"
    export_goal_plan_json(result, output_path=output_path, profile=profile_obj.name)
    typer.echo(f"Goal plan written to {output_path}")


@app.command()
def announce(
    site_dir: Optional[Path] = typer.Option(None, help="Directory containing site_data exports"),
    top_n: int = typer.Option(5, help="Number of packs to include"),
    profile: Optional[str] = typer.Option(None, help="Optional player profile for sorting"),
    include_reference: bool = typer.Option(False, help="Include reference/library packs"),
    output_file: Optional[Path] = typer.Option(None, help="Optional output Markdown file"),
    title: Optional[str] = typer.Option(None, help="Optional heading override"),
):
    """Generate a Discord/Markdown-friendly announcement of top packs."""
    from .analysis.announcements import load_and_generate_announcement

    configure_logging()
    site_dir_path = site_dir or Path("site_data")
    try:
        text = load_and_generate_announcement(
            site_dir=site_dir_path,
            profile_name=profile,
            top_n=top_n,
            title=title,
            include_reference=include_reference,
        )
    except FileNotFoundError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1)

    if output_file:
        output_path = output_file
        from .utils import save_json

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        typer.echo(f"Announcement written to {output_path}")
    else:
        typer.echo(text)


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
