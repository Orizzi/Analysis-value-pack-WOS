"""Configuration loader for ingestion settings."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from ..settings import DEFAULT_INGESTION_CONFIG_PATH

DEFAULT_CONFIG: Dict[str, Any] = {
    "reference_handling": {
        "mode": "tag",  # options: tag, exclude, separate
        "sheet_name_patterns": ["library", "ref", "lookup", "rate"],
    }
}


def load_ingestion_config(path: Path | None = None) -> Dict[str, Any]:
    cfg_path = path or DEFAULT_INGESTION_CONFIG_PATH
    if cfg_path.exists():
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        merged = DEFAULT_CONFIG.copy()
        merged.update(data)
        # merge nested
        if "reference_handling" in data:
            merged["reference_handling"].update(data["reference_handling"] or {})
        return merged
    return DEFAULT_CONFIG.copy()
