# Contributing

## Setup
- Create a venv: `python -m venv .venv`
- Install deps: `.\.venv\Scripts\python -m pip install -e .[ocr]`
- Optional quick install: `.\.venv\Scripts\python -m pip install -r requirements.txt`

## Tests
- Run the suite: `python -m pytest`
- Keep tests green before submitting changes.

## Expectations
- Don’t break default CLI/config behavior.
- Update docs and configs when changing ingestion, valuation, analysis, or Pack Explorer behavior.
- Keep changes small and focused; include tests for significant features.
