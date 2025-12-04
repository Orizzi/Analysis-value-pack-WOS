# Image Analysis Notes

## Current behavior
- Excel embedded images are auto-extracted during ingestion via `openpyxl` and saved under `images_raw/` with the pattern `{workbook}_{sheet}_img_{n}.png`.
- Extraction attempts to map images to worksheet rows (using anchors). If a row mapping is found, the corresponding `PackItem.icon` is populated with the saved file path.
- No transformation/cleanup is performed yet; `images_processed/` is reserved for future normalized icons.

## Future improvements
- **OCR for screenshots**: If pack screenshots (non-embedded) are dropped into `images_raw/`, add a detector that:
  - runs `pytesseract` or `easyocr` to extract text,
  - heuristically parses item names/quantities,
  - writes interim JSON to `data_processed/ocr_candidates.json` for review.
- **Icon normalization**: deduplicate icons by hashing file contents; move cleaned copies to `images_processed/` with slugified names.
- **Metadata linking**: store hashes and inferred item names in `ItemDefinition.meta` to map repeated icons across packs/events.

## Operational hints
- Large spreadsheets with many embedded images can slow ingestion; extractions are logged in `logs/run.log`.
- When OCR is added, keep it optional behind a CLI flag (e.g., `--with-ocr`) to avoid heavy dependencies in minimal runs.
