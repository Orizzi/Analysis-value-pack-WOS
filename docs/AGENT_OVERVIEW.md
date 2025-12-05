# AGENT_OVERVIEW – Read Me First (for AI agents)

## What this project does
- **wos_pack_value** ingests Whiteout Survival pack data (Excel/CSV + optional OCR screenshots), normalizes it, values packs with configurable item prices and tier snapping, runs analysis/ranking, and exports JSON for a static Pack Explorer frontend.
- Main pipeline: **ingestion → valuation → analysis → exports → Pack Explorer**. Everything is CLI-driven; outputs live in `site_data/`, and the Pack Explorer reads them client-side.

## Onboarding checklist (AI)
1. Read `README.md` and `docs/QUICKSTART.md` to grasp commands and layout.
2. Read `docs/DATA_MODEL.md` and `docs/VALUATION_STRATEGY.md` to understand structures and pricing logic.
3. Skim `docs/AI_GUIDE.md`, `docs/IMAGE_ANALYSIS.md`, and `docs/PACK_EXPLORER.md` for ingestion nuances, OCR, and frontend usage.
4. Inspect configs: `config/item_values.yaml`, `config/ingestion.yaml`, `config/analysis.yaml`.
5. Run a summary-only pipeline on examples (no writes): `wos-pack-value run --raw-dir examples --summary-only`.
6. Run full pipeline + analysis on examples and open the Pack Explorer: `wos-pack-value run --raw-dir examples --with-analysis` then open `pack_explorer/pack_explorer.html`.
7. Run tests: `python -m pytest` (inside `.venv`).

## Rules of engagement (for changes)
- Always run tests before/after non-trivial changes.
- Don’t break default CLI behavior or config defaults.
- Ingestion/valuation are core—change carefully and update docs/tests if you adjust them.
- If tuning pricing/tiers/analysis:
  - Update relevant config (`item_values.yaml`, `analysis.yaml`).
  - Update `docs/VALUATION_STRATEGY.md` (and analysis docs if needed).
  - Ensure ranking JSONs still make sense (rerun analysis).
- Don’t delete or break `examples/` or `pack_explorer/` assets.
- Keep changes small and localized; document significant behavior changes in README/AI docs.

## Architecture overview (code & configs)
- **Ingestion**: `wos_pack_value/ingestion/tabular.py` (Excel/CSV parsing, merged cells, headers, images, reference detection), `ingestion/ocr.py` (OCR path), `ingestion/config.py` + `config/ingestion.yaml` (reference handling modes/patterns).
- **Valuation**: `wos_pack_value/valuation/config.py` + `engine.py`; config in `config/item_values.yaml` (item values, price hints, gem_value_per_usd, tier snapping).
- **Analysis**: `wos_pack_value/analysis/ranking.py`; config in `config/analysis.yaml`; outputs `site_data/pack_ranking_overall.json` and `site_data/pack_ranking_by_category.json`.
- **CLI/glue**: `wos_pack_value/cli.py`, `wos_pack_value/pipeline.py`; console script `wos-pack-value`.
- **Frontend**: `pack_explorer/` (HTML/JS/CSS) consumes `site_data` JSONs; base path configurable via `window.PACK_EXPLORER_BASE`.
- **Validation**: `wos_pack_value/validation/validator.py`; config in `config/validation.yaml`; writes `site_data/validation_report.json`.
- Key configs: `config/item_values.yaml`, `config/ingestion.yaml`, `config/analysis.yaml`, `config/player_profiles.yaml`, `config/validation.yaml`.

## Recipes for AI agents
- **Support a new input format/layout**: Update `ingestion/tabular.py` (or add a parser), maybe `COLUMN_ALIASES`; add tests under `tests/` (e.g., new Excel fixture); mention in `docs/IMAGE_ANALYSIS.md` or AI guide.
- **Retune valuation/tiers for another game/server**: Edit `config/item_values.yaml` (item values, hints, tiers); adjust `VALUATION_STRATEGY.md`; rerun pipeline + analysis; ensure tests still pass or add targeted valuation tests.
- **Adjust analysis weights/add ranking category**: Modify `config/analysis.yaml` (category_weights, focus_categories); ensure `analysis/ranking.py` handles new categories; consider small test in `tests/test_analysis_ranking.py`; note changes in README/VALUATION_STRATEGY.
- **Extend Pack Explorer with new filter/metric**: Edit `pack_explorer/pack_explorer.js` (data merging, filters, rendering) and `pack_explorer.html/css`; keep base path configurable; optionally add a comment snippet showing usage; no automated frontend tests, but keep logic small/pure where possible.

## Agent TODO / Future Work
- Improve OCR robustness for new screenshot layouts (see `ingestion/ocr.py`; config knobs could live in a future OCR section).
- Refine item categorization for analysis/ranking (tune `config/analysis.yaml` weights/focus categories; consider extending item categories in valuation).
- Add export variants for different target websites or languages (extend `export/json_export.py`; document paths and naming; ensure Pack Explorer base-path remains configurable).
- Optional: add richer Pack Explorer metrics (e.g., breakdown charts) while keeping it build-free and scoped to `pack_explorer/`.
