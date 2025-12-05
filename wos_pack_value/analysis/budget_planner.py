"""Budget planning over existing pack rankings.

Loads site_data exports, merges ranking info, and selects a pack combination
under a given budget using a simple greedy strategy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..settings import DEFAULT_SITE_PACKS, DEFAULT_SITE_ANALYSIS_OVERALL, SITE_DATA_DIR
from ..utils import load_json, save_json, ensure_dir


@dataclass
class PlannedPack:
    pack_id: str
    name: str
    price: float
    total_value: float
    value_per_dollar: float
    rank_overall: Optional[int] = None
    is_reference: bool = False

    def to_dict(self) -> Dict:
        return {
            "id": self.pack_id,
            "name": self.name,
            "price": self.price,
            "total_value": self.total_value,
            "value_per_dollar": self.value_per_dollar,
            "rank_overall": self.rank_overall,
            "is_reference": self.is_reference,
        }


@dataclass
class PlanSummary:
    budget: float
    currency: str
    total_spent: float
    remaining_budget: float
    total_value: float
    average_value_per_dollar: float
    considered: int
    excluded: int

    def to_dict(self) -> Dict:
        return {
            "budget": self.budget,
            "currency": self.currency,
            "total_spent": self.total_spent,
            "remaining_budget": self.remaining_budget,
            "total_value": self.total_value,
            "average_value_per_dollar": self.average_value_per_dollar,
            "considered": self.considered,
            "excluded": self.excluded,
        }


def _merge_packs_with_rankings(packs: List[Dict], ranking_overall: Dict) -> List[PlannedPack]:
    ranking_map = {p.get("id"): p for p in ranking_overall.get("packs", [])}
    merged: List[PlannedPack] = []
    for p in packs:
        price = float(p.get("price", {}).get("amount", 0) or 0)
        total_value = float(p.get("value", 0) or 0)
        rank_info = ranking_map.get(p.get("id"), {})
        value_per_dollar = float(
            rank_info.get("value_per_dollar")
            or (total_value / price if price else 0.0)
            or 0.0
        )
        merged.append(
            PlannedPack(
                pack_id=p.get("id", ""),
                name=p.get("name", "Unknown Pack"),
                price=price,
                total_value=total_value,
                value_per_dollar=value_per_dollar,
                rank_overall=rank_info.get("rank_overall"),
                is_reference=bool(p.get("is_reference", False)),
            )
        )
    return merged


def load_site_data(site_dir: Path = SITE_DATA_DIR) -> List[PlannedPack]:
    packs_path = site_dir / DEFAULT_SITE_PACKS.name
    ranking_path = site_dir / DEFAULT_SITE_ANALYSIS_OVERALL.name
    if not packs_path.exists():
        raise FileNotFoundError("No packs found; run `wos-pack-value run --with-analysis` first.")
    if not ranking_path.exists():
        raise FileNotFoundError("No ranking data found; run `wos-pack-value run --with-analysis` first.")
    packs = load_json(packs_path).get("packs", [])
    ranking = load_json(ranking_path)
    return _merge_packs_with_rankings(packs, ranking)


def plan_budget(
    packs: List[PlannedPack],
    budget: float,
    currency: str = "USD",
    max_count: Optional[int] = None,
    include_reference: bool = False,
) -> Tuple[List[PlannedPack], PlanSummary]:
    eligible = []
    excluded = 0
    for p in packs:
        if p.price <= 0 or p.value_per_dollar <= 0:
            excluded += 1
            continue
        if p.is_reference and not include_reference:
            excluded += 1
            continue
        eligible.append(p)
    eligible.sort(key=lambda p: p.value_per_dollar, reverse=True)

    selected: List[PlannedPack] = []
    spent = 0.0
    total_value = 0.0
    for p in eligible:
        if max_count is not None and len(selected) >= max_count:
            break
        if spent + p.price <= budget + 1e-9:
            selected.append(p)
            spent += p.price
            total_value += p.total_value
    remaining = max(0.0, budget - spent)
    avg_vpd = (total_value / spent) if spent > 0 else 0.0
    summary = PlanSummary(
        budget=budget,
        currency=currency,
        total_spent=round(spent, 2),
        remaining_budget=round(remaining, 2),
        total_value=round(total_value, 2),
        average_value_per_dollar=round(avg_vpd, 2),
        considered=len(eligible),
        excluded=excluded,
    )
    return selected, summary


def export_plan_json(
    selected: List[PlannedPack],
    summary: PlanSummary,
    output_path: Path,
    profile: str = "default",
) -> Path:
    ensure_dir(output_path.parent)
    payload = {
        "profile": profile,
        "summary": summary.to_dict(),
        "packs": [p.to_dict() for p in selected],
    }
    save_json(output_path, payload)
    return output_path
