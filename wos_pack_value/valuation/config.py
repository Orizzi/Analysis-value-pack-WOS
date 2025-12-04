"""Load valuation configuration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

import yaml

from ..settings import DEFAULT_CONFIG_PATH

logger = logging.getLogger(__name__)


DEFAULT_CONFIG: Dict[str, Any] = {
    "items": {},
    "categories": {
        "unknown": {"base_value": 0.0, "multiplier": 1.0},
    },
    "price_defaults": {"currency": "USD", "fallback_price": 0.0},
    "pack_price_hints": {},
    "price_inference": {"use_gem_total_when_missing": True, "gem_value_per_usd": 300},
    "valuation": {
        "ratio_scale": {"target_ratio": 5.0, "max_ratio": 10.0},
        "score_bands": [
            {"min": 0, "label": "Trash", "color": "#d11141"},
            {"min": 25, "label": "Bad", "color": "#f37735"},
            {"min": 50, "label": "Okay", "color": "#ffc425"},
            {"min": 70, "label": "Good", "color": "#00b159"},
            {"min": 85, "label": "Excellent", "color": "#00a388"},
        ],
    },
}


def _deep_update(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def load_valuation_config(path: Path | None = None) -> Dict[str, Any]:
    cfg_path = path or DEFAULT_CONFIG_PATH
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        config = _deep_update(DEFAULT_CONFIG.copy(), {k: v for k, v in data.items() if v is not None})
        return config
    logger.warning("Config file %s missing; using defaults", cfg_path)
    return DEFAULT_CONFIG
