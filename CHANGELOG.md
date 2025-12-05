# Changelog

## v0.1.0 – Initial public release

### Added
- Ingestion pipeline for Excel/CSV with multi-table detection, merged-cell handling, pack header detection, event-shop support, per-row summaries, and embedded image extraction.
- Optional OCR ingestion for screenshots with configurable reference/library handling via `config/ingestion.yaml`.
- Valuation engine with item base values, price inference (hints + gem_value_per_usd), and tier snapping for USD/EUR store tiers.
- Analysis/ranking layer with configurable weights (`config/analysis.yaml`) producing `pack_ranking_overall.json` and `pack_ranking_by_category.json`.
- Static Pack Explorer frontend (vanilla JS/HTML/CSS) that consumes exports and provides filtering/sorting/detail views.
- CLI (`wos-pack-value`) with commands to ingest, value, export, analyze, and summary-only runs; rich flags for OCR/reference handling.
- Example data under `examples/` and Pack Explorer assets under `pack_explorer/`.
- Documentation set for humans and AI agents (README, QUICKSTART, AI_GUIDE, DATA_MODEL, VALUATION_STRATEGY, IMAGE_ANALYSIS, PACK_EXPLORER, AGENT_OVERVIEW).
- Test suite covering ingestion, valuation, OCR, reference handling, analysis rankings.

### Changed
- Project packaged via `pyproject.toml` with console script entrypoint.

### Fixed
- N/A (initial tagged release).
