# PackWhiteoutSurvivalPackValue

Python toolkit to ingest Whiteout Survival pack data (Excel/CSV), normalize it, assign value scores, and export JSON ready for a static site.

## Quick start

```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pip install -e .  # optional but gives console script
.\.venv\Scripts\python -m wos_pack_value.cli run --config config/item_values.yaml --raw-dir examples
```

Useful commands:

- `python -m wos_pack_value.cli ingest --raw-dir data_raw` - ingestion only.
- `python -m wos_pack_value.cli value --config config/item_values.yaml` - valuation only (uses processed packs).
- `python -m wos_pack_value.cli export` - compute valuation then export site JSON.
- `python -m wos_pack_value.cli sanity` - end-to-end smoke test with a short summary.
- `python -m wos_pack_value.cli run --summary-only` - run without writing outputs; prints/logs summary.
- `pytest` - run tests.

## Project layout

- `wos_pack_value/` - package code (`ingestion`, `valuation`, `export`, CLI, pipeline orchestration).
- `config/` - tweakable valuation inputs (`item_values.yaml`).
- `config/ingestion.yaml` - reference sheet detection/handling.
- `data_raw/` - drop Excel/CSV/JSON inputs here (ingestion scans this folder).
- `data_processed/` - normalized outputs (`packs.json`, `items.json`, `valuations.json`).
- `images_raw/`, `images_processed/` - extracted icons and cleaned variants.
- `site_data/` - JSON exports for the future static site.
- `logs/` - pipeline logs.
- `tests/` - sample data and pytest coverage.
- `examples/` - minimal example workbook to try the pipeline quickly.
- `docs/` - AI guide, data model, valuation strategy, game mechanics, and image-analysis notes.

## Data flow

1. **Ingestion** scans `data_raw/`, reads CSV/Excel (with merged-cell handling), and extracts images when present.
2. **Normalization** stores packs/items in `data_processed/`.
3. **Valuation** loads `config/item_values.yaml`, computes pack totals, ratios, scores, and labels.
4. **Export** writes site-ready JSON to `site_data/`.

See `docs/AI_GUIDE.md` for a deeper, AI-focused explanation and extension guidance. For step-by-step instructions, read `docs/QUICKSTART.md`.

## OCR & reference sheets
- Enable OCR screenshots with `--use-ocr-screenshots` (and optional `--screenshots-dir`, `--ocr-lang`).
- Reference/library sheets are controlled via `config/ingestion.yaml`; override the mode with `--reference-mode tag|exclude|separate`.

## Development
- Install deps: `.\.venv\Scripts\python -m pip install -r requirements.txt`
- Run tests: `.\.venv\Scripts\python -m pytest`
- CLI help: `python -m wos_pack_value.cli --help`
