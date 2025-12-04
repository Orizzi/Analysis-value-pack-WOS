"""Valuation engine for packs."""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from ..models.domain import Pack, PackValuation, ValuedPack

logger = logging.getLogger(__name__)


def _item_value(item, config: Dict) -> Tuple[float, str]:
    items_cfg = config.get("items", {})
    categories = config.get("categories", {})

    category = item.category or "unknown"
    item_cfg = items_cfg.get(item.name) or items_cfg.get(item.item_id)
    value = 0.0

    if item_cfg:
        category = item_cfg.get("category", category) or category
        base_value = float(item_cfg.get("base_value", 0.0))
        value = base_value * float(item.quantity)
    else:
        cat_cfg = categories.get(category, {}) or categories.get("unknown", {})
        base_value = cat_cfg.get("base_value")
        if base_value is not None:
            value = float(base_value) * float(item.quantity)

    multiplier = categories.get(category, {}).get("multiplier", 1.0)
    value *= float(multiplier)
    return value, category


def _score_from_ratio(ratio: float, config: Dict) -> float:
    ratio_cfg = config.get("valuation", {}).get("ratio_scale", {})
    max_ratio = float(ratio_cfg.get("max_ratio", 10.0))
    bounded = max(0.0, min(ratio, max_ratio))
    score = (bounded / max_ratio) * 100.0
    return round(score, 2)


def _label_for_score(score: float, config: Dict) -> Tuple[str, str]:
    bands = sorted(config.get("valuation", {}).get("score_bands", []), key=lambda b: b.get("min", 0))
    selected = bands[0] if bands else {"label": "Unknown", "color": "#999999", "min": 0}
    for band in bands:
        if score >= float(band.get("min", 0)):
            selected = band
    return selected.get("label", "Unknown"), selected.get("color", "#999999")


def value_packs(packs: List[Pack], config: Dict) -> List[ValuedPack]:
    valued: List[ValuedPack] = []
    for pack in packs:
        breakdown: Dict[str, float] = {}
        total = 0.0
        for item in pack.items:
            val, category = _item_value(item, config)
            item.meta["valuation_category"] = category
            breakdown[item.item_id] = val
            total += val
        price = float(pack.price or config.get("price_defaults", {}).get("fallback_price", 0.0))
        ratio = total / price if price else 0.0
        score = _score_from_ratio(ratio, config)
        label, color = _label_for_score(score, config)
        valuation = PackValuation(
            pack_id=pack.pack_id,
            total_value=round(total, 2),
            price=price,
            ratio=round(ratio, 2),
            score=score,
            label=label,
            color=color,
            breakdown=breakdown,
        )
        valued.append(ValuedPack(pack=pack, valuation=valuation))
    logger.info("Valuated %s packs", len(valued))
    return valued

