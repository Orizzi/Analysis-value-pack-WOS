# Quickstart

## Install
```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pip install -e .  # optional, for console script entry
```

## Run on example data
```bash
.\.venv\Scripts\python -m wos_pack_value.cli run --raw-dir examples
```
Outputs go to `site_data/` by default:
- `packs.json` – packs with valuations.
- `items.json` – deduped items.
- `reference_packs.json` – only when reference mode is `separate`.

## Flags you may need
- `--use-ocr-screenshots` (with `--screenshots-dir`, `--ocr-lang`) to include OCR screenshots.
- `--ingestion-config config/ingestion.yaml` to tweak reference handling; override mode with `--reference-mode tag|exclude|separate`.
- `--summary-only` to run without writing outputs (prints/logs summary).
- `--raw-dir` / `--site-dir` / `--log-file` to point inputs/outputs elsewhere.
