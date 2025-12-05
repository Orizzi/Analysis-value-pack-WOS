"""Rule-based summaries for packs based on existing metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional


@dataclass
class SummaryContext:
    overall_percentiles: Dict[str, float]
    category_percentiles: Dict[str, Dict[str, float]]
    profile_name: str | None = None


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * pct
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    fraction = pos - low
    return ordered[low] + (ordered[high] - ordered[low]) * fraction


def _compute_percentiles(values: Iterable[float]) -> Dict[str, float]:
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return {"p90": 0.0, "p75": 0.0, "p50": 0.0, "p25": 0.0}
    return {
        "p90": _percentile(vals, 0.9),
        "p75": _percentile(vals, 0.75),
        "p50": _percentile(vals, 0.5),
        "p25": _percentile(vals, 0.25),
    }


def _describe_overall(value_per_dollar: float, percentiles: Mapping[str, float]) -> str | None:
    if value_per_dollar is None or value_per_dollar <= 0:
        return None
    p90 = percentiles.get("p90", 0.0)
    p75 = percentiles.get("p75", 0.0)
    p50 = percentiles.get("p50", 0.0)
    if value_per_dollar >= p90 and p90 > 0:
        return "exceptional overall value"
    if value_per_dollar >= p75 and p75 > 0:
        return "very strong overall value"
    if value_per_dollar >= p50 and p50 > 0:
        return "solid overall value"
    return "average or situational value"


def _human_label(category: str) -> str:
    return category.replace("_", " ").strip().title() or "General"


def _describe_category(
    category_values: Mapping[str, float],
    price: float,
    category_percentiles: Mapping[str, Dict[str, float]],
) -> str | None:
    if not category_values or price <= 0:
        return None
    best_cat = None
    best_vpd = 0.0
    for cat, val in category_values.items():
        vpd = float(val or 0) / price if price else 0.0
        if vpd > best_vpd:
            best_cat = cat
            best_vpd = vpd
    if not best_cat or best_vpd <= 0:
        return None
    thresholds = category_percentiles.get(best_cat, {})
    p80 = thresholds.get("p80", 0.0)
    p60 = thresholds.get("p60", 0.0)
    label = _human_label(best_cat)
    if p80 and best_vpd >= p80:
        return f"especially strong for {label}"
    if p60 and best_vpd >= p60:
        return f"notably good for {label}"
    return f"leans toward {label.lower()}"


PROFILE_HINTS = {
    "default": "Suitable for general spending.",
    "f2p": "Good fit for F2P players focused on efficiency.",
    "mid_spender": "Balanced choice for moderate spenders.",
    "whale": "Appeals to whales seeking specific rare items.",
}


def generate_pack_summary(
    pack_metrics: Dict[str, Any],
    *,
    context: SummaryContext,
) -> str:
    price = float(pack_metrics.get("price", 0) or 0.0)
    total_value = float(pack_metrics.get("total_value", 0) or 0.0)
    value_per_dollar = float(pack_metrics.get("value_per_dollar", 0) or 0.0)

    if price <= 0 or total_value <= 0 or value_per_dollar <= 0:
        return "This pack's value is hard to estimate with current data."

    sentences: List[str] = []

    overall_desc = _describe_overall(value_per_dollar, context.overall_percentiles)
    if overall_desc:
        sentences.append(f"This pack offers {overall_desc}.")

    cat_desc = _describe_category(
        pack_metrics.get("category_values", {}) or {},
        price,
        context.category_percentiles,
    )
    if cat_desc:
        sentences.append(f"It is {cat_desc}.")

    profile = (context.profile_name or "default").lower()
    if profile in PROFILE_HINTS:
        sentences.append(PROFILE_HINTS[profile])

    if not sentences:
        return "This pack's value is hard to estimate with current data."
    return " ".join(sentences)


def generate_all_pack_summaries(
    packs: List[Dict[str, Any]],
    *,
    profile_name: str | None = None,
) -> Dict[str, str]:
    overall_percentiles = _compute_percentiles(p.get("value_per_dollar") for p in packs)
    category_percentiles: Dict[str, Dict[str, float]] = {}
    for pack in packs:
        price = float(pack.get("price", 0) or 0.0)
        if price <= 0:
            continue
        for cat, val in (pack.get("category_values") or {}).items():
            vpd = float(val or 0) / price if price else 0.0
            category_percentiles.setdefault(cat, []).append(vpd)
    for cat, values in list(category_percentiles.items()):
        category_percentiles[cat] = {
            "p80": _percentile(values, 0.8),
            "p60": _percentile(values, 0.6),
        }

    context = SummaryContext(
        overall_percentiles=overall_percentiles,
        category_percentiles=category_percentiles,
        profile_name=profile_name,
    )
    return {
        pack.get("id", f"pack-{idx}"): generate_pack_summary(pack, context=context)
        for idx, pack in enumerate(packs)
    }


__all__ = ["generate_pack_summary", "generate_all_pack_summaries", "SummaryContext"]
