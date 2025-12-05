# Image Analysis & OCR Notes

## Current behavior
- Excel embedded images are auto-extracted during ingestion via `openpyxl` and saved under `images_raw/` with the pattern `{workbook}_{sheet}_img_{n}.png`.
- Extraction attempts to map images to worksheet rows (using anchors). If a row mapping is found, the corresponding `PackItem.icon` is populated with the saved file path.
- OCR screenshots (optional) are parsed via `wos_pack_value/ingestion/ocr.py`:
  - Drop screenshots under `data_raw/screenshots/`.
  - Run the pipeline with `--use-ocr-screenshots` (optionally `--screenshots-dir` and `--ocr-lang`).
  - Raw OCR packs are dumped to `data_review/ocr_packs_raw.json`.
  - Use `ocr_review/ocr_review.html` to load/edit that file and download `ocr_packs_reviewed.json`.
  - Place the reviewed file under `data_review/`; on the next run, reviewed packs are preferred over raw OCR.

## Future improvements
- **Icon normalization**: deduplicate icons by hashing file contents; move cleaned copies to `images_processed/` with slugified names.
- **Metadata linking**: store hashes and inferred item names in `ItemDefinition.meta` to map repeated icons across packs/events.

## Operational hints
- Large spreadsheets with many embedded images can slow ingestion; extractions are logged in `logs/run.log`.
- OCR remains optional; if dependencies are missing, the CLI raises a clear error.
- Reviewed OCR packs (`data_review/ocr_packs_reviewed.json`) override raw OCR for the same sources; raw OCR packs without a reviewed counterpart are still ingested and dumped for review.
