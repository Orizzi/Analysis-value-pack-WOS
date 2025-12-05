# AI Guide – PackWhiteoutSurvivalPackValue

If context ever disappears, load this file first. It contains enough detail for an AI to recreate or extend the project.

## Purpose

Analyse Whiteout Survival paid packs. Ingest mixed raw sources (Excel/CSV with merged cells and embedded icons), normalize packs/items, compute value scores based on configurable item values, and export JSON for a static website.

## Repository layout

- `wos_pack_value/`
- `ingestion/` – file scanning and tabular parsers (`tabular.py`, `pipeline.py`).
- `ingestion/ocr.py` – optional OCR ingestion of screenshots (pytesseract).
- `ingestion/config.py` – ingestion config loader (reference handling).
- `docs/QUICKSTART.md` – concise steps from clone to first run.
  - `valuation/` – config loader and scoring engine (`config.py`, `engine.py`, `pipeline.py`).
  - `export/` – site-facing JSON writer (`json_export.py`).
  - `pipeline.py` – top-level run orchestrator.
  - `cli.py`, `__main__.py` – Typer CLI entrypoints.
  - `logging_utils.py`, `settings.py`, `utils.py` – shared helpers.
- `config/item_values.yaml` - tweakable base values, categories, and scoring bands.
- `docs/VALUATION_STRATEGY.md`, `docs/GAME_MECHANICS.md`, `docs/IMAGE_ANALYSIS.md` - human context on pricing, game loops, and image handling.
- `data_raw/` – drop Excel/CSV here (ingestion scans this folder).
- `data_raw/screenshots/` – optional screenshot drop-zone for OCR ingestion.
- `data_processed/` – normalized packs/items + valuations JSON.
- `site_data/` – static-site JSON exports.
- `images_raw/`, `images_processed/` – extracted and cleaned icons.
- `data_raw/screenshots/` – optional screenshot drop-zone for OCR ingestion.
- `logs/` – rotating log files.
- `tests/` – fixtures (`tests/data/sample_packs.csv`) and pytest coverage.

## Core data model

- `Pack` – `pack_id`, `name`, `price`, `currency`, `source_file`, `source_sheet`, `tags`, `items`, `meta`.
- `PackItem` – `item_id`, `name`, `quantity`, `category`, `icon`, `base_value`, `source_row`, `meta`.
- `ItemDefinition` – deduped item metadata (id, name, category, icon, base_value).
- `PackValuation` – totals per pack (`total_value`, `price`, `ratio`, `score`, `label`, `color`, `breakdown`).
- `ValuedPack` – bundle of `Pack` + `PackValuation`.

IDs are slugified from names (lowercase, hyphenated).

## Ingestion flow (`wos_pack_value.ingestion`)

1. `ingest_all()` (pipeline) scans `data_raw/` for files.
2. `parse_file()` dispatches to CSV or Excel.
   - Excel parser splits sheets into multiple tables by detecting header rows (keywords like Item/Quantity/Total/Cost). Pack headers immediately above a table are used as default pack names.
   - Embedded images are extracted to `images_raw/FILE_sheet_img_N.png` and row-mapped where anchors allow.
   - Merged cells are resolved virtually (without mutating the workbook) so merged headers are propagated.
3. `_normalize_dataframe()` harmonizes columns (pack/item/price/quantity/category/currency/tags, gem-per-unit, token cost, equivalent gem cost) and fills defaults, preferring event/shop names when present.
4. `_pack_from_rows()`:
   - Skips summary rows (Gem Total, Pack %, True Pack Value %), but stores summaries in `pack.meta`.
   - Builds `PackItem`s, capturing `base_value` from gem-per-unit, gem-value, weighted gem value, or `equivalent_gem_cost / quantity`. Token cost and row totals land in `item.meta`.
5. `build_item_definitions()` dedupes items. Normalized data persists to `data_processed/packs.json` and `items.json` with timestamps.

Column aliases of interest: `pack|bundle|pack_name` -> `pack_name`; `item|items|reward|item_name` -> `item_name`; `qty|quantity|amount` -> `quantity`; `cost|price_usd|price($)` -> `price`; `type|category` -> `category`; `tag|tags` -> `tags`.

## Valuation (`wos_pack_value.valuation`)

- `load_valuation_config()` loads YAML (deep-merged with defaults) including:
  - `items`, `categories`, `pack_price_hints`, `price_inference` (gem_value_per_usd, tier snapping), `price_defaults`, `valuation` bands/scale.
- `load_ingestion_config()` loads `config/ingestion.yaml` (reference handling): `mode` (`tag`/`exclude`/`separate`) and `sheet_name_patterns` used to detect library/reference tables. Packs parsed from sheets matching patterns are tagged (`is_reference=True`), optionally excluded from valuation/exports or written to `site_data/reference_packs.json` when `mode=separate`.
- `value_packs()` resolution order: per-item override → ingested `base_value` → category default (+ multiplier). Price inference uses pack price → `pack_price_hints` (substring) → gem_total/`gem_value_per_usd` → fallback, then snaps to the nearest configured tier when enabled. Price source (with snap info) is recorded in `pack.meta["price_source"]`.
- OCR path: `ingestion/ocr.py` can convert screenshot text into packs. CLI flag `--use-ocr-screenshots` (with optional `--screenshots-dir`, `--ocr-lang`) enables this path. Without OCR libs installed, enablement will raise a clear error. Parsed items/price/pack names are fed into the same valuation/export pipeline.
- Reference handling: sheets/blocks with names matching patterns (default: library/ref/lookup/rate) are tagged as reference. Depending on `reference_handling.mode`, they are excluded, tagged in main exports, or written separately.

## How to navigate (for AI agents)
- Need end-to-end picture? Read `README.md` then `docs/QUICKSTART.md`.
- Need technical internals? Read `docs/AI_GUIDE.md` (this file) then `docs/DATA_MODEL.md` and `docs/VALUATION_STRATEGY.md`.
- Need OCR/reference specifics? See `docs/IMAGE_ANALYSIS.md` and `config/ingestion.yaml`.
- `valuate()` wrapper loads processed packs when needed and optionally persists `valuations.json`.

## Export (`wos_pack_value.export`)

- `export_site_json()` writes:
  - `site_data/packs.json`: pack metadata, items, valuation totals, ratio, score, label, color.
  - `site_data/items.json`: deduped item definitions (from ingestion or derived on the fly).
- Each file carries `generated_at` timestamps. Shapes are designed for static consumption with a red→green mapping via `label/color/score`.

## Pipeline orchestration

- `run_pipeline()` wires ingestion → valuation → export with logging configured.
- CLI (`python -m wos_pack_value.cli`):
  - `run` – full pipeline.
  - `ingest` – ingestion only (supports `--raw-dir` override).
  - `value` – valuation only (uses processed packs).
  - `export` – valuation + export.
  - `sanity` – end-to-end smoke test printing top scores.

## Testing

- Pytest configured via `pyproject.toml`.
- Fixtures in `tests/data/sample_packs.csv`.
- Tests cover ingestion grouping, valuation scoring >0, and JSON export creation.
- Run with `pytest` (uses tmp dirs; no real data needed).

## Extension tips

- To add new item valuations, edit `config/item_values.yaml` (`items` or `categories`).
- To support new file formats, extend `parse_file()` dispatch or add specialized parsers.
- If Excel headers differ, adjust `COLUMN_ALIASES` or enhance `_normalize_dataframe`.
- For more precise scoring, refine `_score_from_ratio` or add event-based multipliers in config.
- To persist more metadata (e.g., event tags), extend `Pack.meta` and update exports accordingly.

## Operational notes

- Logs rotate at `logs/run.log` (console + file).
- Directories are created on demand (`ensure_dir`).
- `data_raw/`, `data_processed/`, and `logs/` are ignored by git except for `.gitkeep` markers to avoid committing large artifacts.
- For quick runs, point the CLI at `tests/data` (`--raw-dir tests/data`) instead of heavy Excel inputs.
- When new sheets appear with pack headers above tables, ingestion should auto-detect them; add a regression test mirroring the layout if not.
