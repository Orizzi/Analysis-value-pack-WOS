# PackWhiteoutSurvivalPackValue

One-stop toolkit to ingest, value, rank, and explore Whiteout Survival packs (Excel/CSV/OCR) with static JSON exports and a browser-based Pack Explorer.

## Features
- **Ingestion**: Excel/CSV with multi-table detection, merged-cell handling, event-shop support, image extraction, optional OCR screenshots, and reference/library tagging.
- **Valuation**: Config-driven item values, price inference (hints + gem_value_per_usd + tier snapping), per-pack totals and scores.
- **Analysis/Ranking**: Configurable weights produce overall and category-focused rankings (`pack_ranking_overall.json`, `pack_ranking_by_category.json`).
- **CLI**: `wos-pack-value` to run ingestion -> valuation -> export -> analysis; summary-only mode and rich flags for OCR/reference handling.
- **Pack Explorer**: Static HTML/JS/CSS (no build) that reads JSON exports for filtering/sorting/detail browsing.
- **Player profiles & planning**: Profile weights (f2p/mid/whale, etc.) influence analysis and the budget planner (`wos-pack-value plan`), plus a goal planner to reach target items.
- **Docs & tests**: Human and AI guides, sample data in `examples/`, and pytest coverage.

## Quickstart
```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pip install -e .  # optional console script
wos-pack-value run --raw-dir examples --with-analysis
```

- Open `pack_explorer/pack_explorer.html` after the run to browse packs (set `window.PACK_EXPLORER_BASE` if JSON lives elsewhere).
- Dry run without writes: `wos-pack-value run --raw-dir examples --summary-only`
- Analyze existing exports: `wos-pack-value analyze --site-dir site_data --analysis-config config/analysis.yaml`

## Project layout (high level)
- `wos_pack_value/` – ingestion, valuation, analysis, CLI, exports.
- `config/` – `item_values.yaml`, `ingestion.yaml`, `analysis.yaml`.
- `site_data/` – JSON exports (packs/items/rankings).
- `examples/` – sample workbook and OCR text.
- `pack_explorer/` – static frontend (HTML/JS/CSS).
- `docs/` – QUICKSTART, AI_GUIDE, DATA_MODEL, VALUATION_STRATEGY, IMAGE_ANALYSIS, PACK_EXPLORER, AGENT_OVERVIEW, GAMEPLAY_GUIDE.

## For contributors / AI agents
- Start with `docs/AGENT_OVERVIEW.md` for navigation, rules, and recipes.
- Dev setup: `python -m venv .venv && .\.venv\Scripts\python -m pip install -e .[ocr]`
- Run tests: `python -m pytest`
- Keep default CLI/config behavior intact; update docs and configs when changing valuation/analysis assumptions.

## For players
- After generating exports, open `pack_explorer/pack_explorer.html` to browse rankings (set `window.PACK_EXPLORER_BASE` if JSON lives elsewhere).
- See `docs/GAMEPLAY_GUIDE.md` for interpreting value per dollar, ranks, category-focused views, and practical buying tips.
- To get a quick shopping list under a budget, run `wos-pack-value plan --site-dir site_data --budget 50 --currency EUR --profile f2p` (profiles are defined in `config/player_profiles.yaml`).
- To reach a target item amount, use `wos-pack-value goal --site-dir site_data --target \"Hero X Shard\" --amount 100 --budget 80 --currency EUR --profile f2p`.
- Basic validation runs during the pipeline and writes `site_data/validation_report.json`; check logs and the report for anomalies.

## License
- License selection is pending. Until a LICENSE is added, treat the repository as "all rights reserved" and coordinate with the maintainer before reuse.

## Changelog
- See `CHANGELOG.md` for release history.
