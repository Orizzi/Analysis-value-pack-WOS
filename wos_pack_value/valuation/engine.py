"""Valuation engine for packs."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

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
    elif item.base_value is not None:
        value = float(item.base_value) * float(item.quantity)
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


def _get_gem_total(pack: Pack) -> Optional[float]:
    """Return gem_total either from meta or row totals if present."""
    meta_total = pack.meta.get("gem_total")
    if meta_total not in (None, "", 0):
        try:
            return float(meta_total)
        except Exception:
            return None
    row_totals = [item.meta.get("row_total") for item in pack.items if item.meta.get("row_total") not in (None, "")]
    if row_totals:
        try:
            return float(sum(float(x) for x in row_totals))
        except Exception:
            return None
    return None


def _snap_price(price: float, currency: str, config: Dict, gem_total: Optional[float]) -> Tuple[float, Optional[str]]:
    """Snap inferred price to nearest configured tier."""
    inf_cfg = config.get("price_inference", {}) or {}
    if not inf_cfg.get("snap_to_tiers", True) or price <= 0:
        return price, None

    tiers = inf_cfg.get("tiers") or []
    snap_max = inf_cfg.get("snap_max_delta")
    currency = (currency or config.get("price_defaults", {}).get("currency", "USD")).upper()

    # Prefer gem_total-based matching if ranges are defined.
    gem_candidates: List[Tuple[float, float, str]] = []
    if gem_total is not None:
        for tier in tiers:
            if tier.get("currency", currency).upper() != currency:
                continue
            gem_map = tier.get("gem_totals") or {}
            for amt_key, gt in gem_map.items():
                try:
                    amt = float(amt_key)
                    diff = abs(float(gt) - gem_total)
                    norm = diff / max(float(gt), 1.0)
                    gem_candidates.append((norm, amt, tier.get("name", "tier")))
                except Exception:
                    continue
        if gem_candidates:
            gem_candidates.sort(key=lambda t: t[0])
            best_norm, best_price, tier_name = gem_candidates[0]
            if snap_max is None or best_norm * best_price <= float(snap_max):
                return best_price, tier_name

    candidates: List[Tuple[float, float, str]] = []
    for tier in tiers:
        if tier.get("currency", currency).upper() != currency:
            continue
        for amt in tier.get("prices") or tier.get("amounts") or []:
            try:
                amt_f = float(amt)
            except Exception:
                continue
            diff = abs(price - amt_f)
            if snap_max is not None and diff > float(snap_max):
                continue
            candidates.append((diff, amt_f, tier.get("name", "tier")))
    if not candidates:
        return price, None
    candidates.sort(key=lambda t: t[0])
    _, snapped, tier_name = candidates[0]
    return snapped, tier_name


def _infer_price(pack: Pack, config: Dict) -> Tuple[float, str]:
    price = float(pack.price or 0.0)
    source = "pack"
    if price <= 0:
        hints = config.get("pack_price_hints", {}) or {}
        name_lower = pack.name.lower()
        for key, hint_price in hints.items():
            if key.lower() in name_lower:
                if isinstance(hint_price, dict):
                    price = float(hint_price.get("amount", 0.0))
                else:
                    price = float(hint_price)
                source = f"hint:{key}"
                break

    if price <= 0:
        inference_cfg = config.get("price_inference", {}) or {}
        if inference_cfg.get("use_gem_total_when_missing"):
            gem_total = _get_gem_total(pack)
            rate = float(inference_cfg.get("gem_value_per_usd", 0) or 0)
            if gem_total and rate:
                price = float(gem_total) / rate
                source = "gem_total"

    if price <= 0:
        price = float(config.get("price_defaults", {}).get("fallback_price", 0.0))
        source = "fallback"

    snapped, tier_name = _snap_price(price, pack.currency, config, gem_total=_get_gem_total(pack))
    if tier_name:
        source = f"{source}|snap:{tier_name}"
        price = snapped

    pack.meta["price_source"] = source
    return price, source


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
        price, _ = _infer_price(pack, config)
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
