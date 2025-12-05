"""Pack analysis and ranking layer built on top of site_data exports."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from ..settings import (
    DEFAULT_ANALYSIS_CONFIG_PATH,
    DEFAULT_SITE_ANALYSIS_BY_CATEGORY,
    DEFAULT_SITE_ANALYSIS_OVERALL,
    DEFAULT_SITE_ITEMS,
    DEFAULT_SITE_PACKS,
    SITE_DATA_DIR,
)
from ..utils import ensure_dir, load_json, save_json

logger = logging.getLogger(__name__)


def load_analysis_config(path: Path | None = None) -> Dict:
    cfg_path = path or DEFAULT_ANALYSIS_CONFIG_PATH
    if cfg_path.exists():
        return load_json(cfg_path) if cfg_path.suffix.lower() == ".json" else __load_yaml(cfg_path)
    return {
        "analysis": {
            "exclude_reference": True,
            "min_price": 0.0,
            "max_value_per_dollar": 20.0,
            "category_weights": {},
            "focus_categories": [],
        }
    }


def __load_yaml(path: Path) -> Dict:
    import yaml

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _extract_pack_records(packs: List[Dict], config: Dict) -> List[Dict]:
    settings = config.get("analysis", {})
    min_price = float(settings.get("min_price", 0.0) or 0.0)
    exclude_reference = bool(settings.get("exclude_reference", False))
    records = []
    for p in packs:
        if exclude_reference and p.get("is_reference"):
            continue
        price = float(p.get("price", {}).get("amount", 0) or 0)
        if price < min_price:
            continue
        records.append(p)
    return records


def _compute_metrics(pack: Dict, category_weights: Dict, focus_categories: List[str], max_vpd: float) -> Dict:
    price = float(pack.get("price", {}).get("amount", 0) or 0)
    total_value = float(pack.get("value", 0) or 0)
    value_per_dollar = total_value / price if price else 0.0
    category_values: Dict[str, float] = {}
    for item in pack.get("items", []):
        cat = item.get("category", "unknown")
        val = float(item.get("value", 0) or 0)
        category_values[cat] = category_values.get(cat, 0.0) + val

    overall_score = min(100.0, (value_per_dollar / max_vpd) * 100.0) if max_vpd else 0.0
    focus_scores: Dict[str, float] = {}
    for cat in focus_categories:
        cat_val = category_values.get(cat, 0.0)
        score = min(100.0, (cat_val / price) / max_vpd * 100.0) if price and max_vpd else 0.0
        focus_scores[cat] = round(score, 2)

    weighted = 0.0
    weight_sum = 0.0
    for cat, w in category_weights.items():
        weight_sum += float(w)
        weighted += float(w) * category_values.get(cat, 0.0)
    weighted_score = 0.0
    if weight_sum and price and max_vpd:
        weighted_score = min(100.0, (weighted / weight_sum) / price / max_vpd * 100.0)

    return {
        "id": pack.get("id"),
        "name": pack.get("name"),
        "price": price,
        "currency": pack.get("price", {}).get("currency", "USD"),
        "source": pack.get("source", {}),
        "total_value": round(total_value, 2),
        "value_per_dollar": round(value_per_dollar, 2),
        "category_values": {k: round(v, 2) for k, v in category_values.items()},
        "overall_score": round(overall_score, 2),
        "weighted_score": round(weighted_score, 2),
        "focus_scores": focus_scores,
        "is_reference": pack.get("is_reference", False),
    }


def analyze_packs(packs: List[Dict], config: Dict) -> Tuple[List[Dict], Dict[str, List[Dict]]]:
    settings = config.get("analysis", {})
    category_weights = settings.get("category_weights", {})
    focus_categories = settings.get("focus_categories", [])
    max_vpd = float(settings.get("max_value_per_dollar", 20.0) or 20.0)

    records = _extract_pack_records(packs, config)
    analyses: List[Dict] = []
    for p in records:
        analyses.append(_compute_metrics(p, category_weights, focus_categories, max_vpd))

    analyses.sort(key=lambda a: a["value_per_dollar"], reverse=True)
    for idx, rec in enumerate(analyses, start=1):
        rec["rank_overall"] = idx

    # category rankings based on focus scores
    by_category: Dict[str, List[Dict]] = {}
    for cat in focus_categories:
        cat_sorted = sorted(analyses, key=lambda a: a["focus_scores"].get(cat, 0), reverse=True)
        for idx, rec in enumerate(cat_sorted, start=1):
            rec[f"rank_{cat}"] = idx
        by_category[cat] = [
            {
                "id": rec["id"],
                "name": rec["name"],
                "price": rec["price"],
                "value_per_dollar": rec["value_per_dollar"],
                "score": rec["focus_scores"].get(cat, 0),
                "rank": rec[f"rank_{cat}"],
            }
            for rec in cat_sorted
        ]

    return analyses, by_category


def analyze_from_site_data(
    site_dir: Path = SITE_DATA_DIR,
    config_path: Path | None = None,
    output_dir: Path | None = None,
) -> Tuple[Path, Path]:
    config = load_analysis_config(config_path)
    packs_data = load_json((site_dir / DEFAULT_SITE_PACKS.name))
    packs = packs_data.get("packs", [])
    analyses, by_category = analyze_packs(packs, config)

    out_dir = output_dir or site_dir
    ensure_dir(out_dir)
    overall_path = out_dir / DEFAULT_SITE_ANALYSIS_OVERALL.name
    cat_path = out_dir / DEFAULT_SITE_ANALYSIS_BY_CATEGORY.name
    save_json(overall_path, {"packs": analyses})
    save_json(cat_path, {"by_category": by_category})
    logger.info("Analysis exported to %s and %s", overall_path, cat_path)
    return overall_path, cat_path
