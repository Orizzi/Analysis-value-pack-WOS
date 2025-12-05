"""Centralized item categorization based on config."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..analysis.game_profiles import GameProfile, resolve_config_path
from ..settings import CONFIG_DIR, DEFAULT_ITEM_CATEGORIES_PATH


@dataclass
class CategoryRule:
    name_contains: List[str] = field(default_factory=list)
    name_exact: List[str] = field(default_factory=list)


@dataclass
class ItemCategoryConfig:
    categories: Dict[str, CategoryRule] = field(default_factory=dict)


def load_item_category_config(path: Path | None = None, game: GameProfile | None = None) -> ItemCategoryConfig:
    cfg_path = path or (resolve_config_path("item_categories.yaml", game, CONFIG_DIR) if game else DEFAULT_ITEM_CATEGORIES_PATH)
    if not cfg_path.exists():
        return ItemCategoryConfig()
    with cfg_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    cats = {}
    for key, entry in (data.get("categories") or {}).items():
        match = entry.get("match", {}) if isinstance(entry, dict) else {}
        cats[key] = CategoryRule(
            name_contains=[s.lower() for s in match.get("name_contains", [])],
            name_exact=[s.lower() for s in match.get("name_exact", [])],
        )
    return ItemCategoryConfig(categories=cats)


def classify_item(item: Dict[str, Any], config: ItemCategoryConfig) -> List[str]:
    """Return category keys for an item using name-based rules."""
    if not config.categories:
        return []
    name = str(item.get("name", "")).lower()
    item_id = str(item.get("item_id", "")).lower()
    matched: List[str] = []
    for cat, rule in config.categories.items():
        if any(token in name for token in rule.name_contains):
            matched.append(cat)
            continue
        if any(name == exact or item_id == exact for exact in rule.name_exact):
            matched.append(cat)
    return matched


def aggregate_category_values(
    items: List[Any],
    breakdown: Dict[str, float],
    config: ItemCategoryConfig,
) -> Dict[str, float]:
    """Sum item values into category buckets using classification."""
    totals: Dict[str, float] = {}
    for it in items:
        key = getattr(it, "item_id", None) or it.get("item_id")
        value = breakdown.get(key, 0.0)
        base_category = getattr(it, "category", None) or it.get("category")
        categories = classify_item(
            {"name": getattr(it, "name", None) or it.get("name"), "item_id": key},
            config,
        )
        if base_category and base_category not in categories:
            categories.append(base_category)
        if not categories:
            categories = []
        for cat in categories:
            totals[cat] = totals.get(cat, 0.0) + value
    return totals


__all__ = ["ItemCategoryConfig", "CategoryRule", "load_item_category_config", "classify_item", "aggregate_category_values"]
