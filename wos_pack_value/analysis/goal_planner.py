"""Goal-oriented pack planner: reach a target item amount within budget."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .player_profiles import PlayerProfile
from .ranking import compute_profile_score
from ..settings import DEFAULT_SITE_PACKS, DEFAULT_SITE_ITEMS, DEFAULT_SITE_ANALYSIS_OVERALL, SITE_DATA_DIR
from ..utils import ensure_dir, load_json, save_json


@dataclass
class GoalCandidate:
    pack_id: str
    name: str
    price: float
    value_per_dollar: float
    target_quantity: float
    is_reference: bool
    category_values: Dict[str, float] = field(default_factory=dict)
    profile_score: Optional[float] = None

    @property
    def cost_per_unit(self) -> float:
        if self.target_quantity <= 0:
            return float("inf")
        return self.price / self.target_quantity if self.price > 0 else float("inf")

    def to_dict(self) -> Dict:
        return {
            "id": self.pack_id,
            "name": self.name,
            "price": self.price,
            "value_per_dollar": self.value_per_dollar,
            "target_quantity": self.target_quantity,
            "cost_per_unit": self.cost_per_unit if self.cost_per_unit != float("inf") else None,
            "profile_score": self.profile_score,
            "is_reference": self.is_reference,
        }


@dataclass
class GoalPlanSummary:
    target: str
    target_amount_requested: float
    target_amount_obtained: float
    budget: Optional[float]
    currency: str
    total_spent: float
    remaining_budget: Optional[float]
    effective_cost_per_unit: Optional[float]
    considered: int
    excluded: int
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "target": self.target,
            "target_amount_requested": self.target_amount_requested,
            "target_amount_obtained": self.target_amount_obtained,
            "budget": self.budget,
            "currency": self.currency,
            "total_spent": self.total_spent,
            "remaining_budget": self.remaining_budget,
            "effective_cost_per_unit": self.effective_cost_per_unit,
            "considered": self.considered,
            "excluded": self.excluded,
            "notes": self.notes,
        }


@dataclass
class GoalPlanResult:
    selected: List[GoalCandidate]
    summary: GoalPlanSummary


def _load_site_data(site_dir: Path = SITE_DATA_DIR) -> Tuple[List[Dict], Dict]:
    packs_path = site_dir / DEFAULT_SITE_PACKS.name
    ranking_path = site_dir / DEFAULT_SITE_ANALYSIS_OVERALL.name
    if not packs_path.exists():
        raise FileNotFoundError("No packs found; run `wos-pack-value run --with-analysis` first.")
    if not ranking_path.exists():
        raise FileNotFoundError("No ranking data found; run `wos-pack-value run --with-analysis` first.")
    packs = load_json(packs_path).get("packs", [])
    ranking = load_json(ranking_path)
    return packs, ranking


def _match_target(item: Dict, target: str) -> bool:
    name = str(item.get("name", "")).lower()
    item_id = str(item.get("id", "")).lower()
    t = target.lower()
    return t in name or t == name or t == item_id


def _merge_goal_candidates(
    packs: List[Dict],
    ranking_overall: Dict,
    target: str,
    include_reference: bool,
    profile: Optional[PlayerProfile],
) -> Tuple[List[GoalCandidate], int]:
    ranking_map = {p.get("id"): p for p in ranking_overall.get("packs", [])}
    candidates: List[GoalCandidate] = []
    excluded = 0
    for pack in packs:
        if pack.get("is_reference") and not include_reference:
            excluded += 1
            continue
        price = float(pack.get("price", {}).get("amount", 0) or 0)
        items = pack.get("items", [])
        target_qty = sum(float(it.get("quantity", 0) or 0) for it in items if _match_target(it, target))
        if price <= 0 or target_qty <= 0:
            excluded += 1
            continue
        rank_info = ranking_map.get(pack.get("id"), {})
        value_per_dollar = float(
            rank_info.get("value_per_dollar")
            or (pack.get("value", 0) / price if price else 0)
            or 0.0
        )
        cat_values = rank_info.get("category_values", {}) or pack.get("category_values", {}) or {}
        candidate = GoalCandidate(
            pack_id=pack.get("id", ""),
            name=pack.get("name", "Unknown Pack"),
            price=price,
            value_per_dollar=value_per_dollar,
            target_quantity=target_qty,
            is_reference=bool(pack.get("is_reference", False)),
            category_values=cat_values,
        )
        if profile and profile.weights:
            candidate.profile_score = compute_profile_score(
                {
                    "price": {"amount": candidate.price},
                    "category_values": candidate.category_values,
                    "value_per_dollar": candidate.value_per_dollar,
                },
                profile,
            )
        candidates.append(candidate)
    return candidates, excluded


def plan_for_goal(
    *,
    site_dir: Path,
    target_name: str,
    target_amount: float,
    budget: Optional[float] = None,
    currency: str = "USD",
    include_reference: bool = False,
    profile: Optional[PlayerProfile] = None,
) -> GoalPlanResult:
    packs, ranking = _load_site_data(site_dir)
    candidates, excluded = _merge_goal_candidates(packs, ranking, target_name, include_reference, profile)
    if not candidates:
        summary = GoalPlanSummary(
            target=target_name,
            target_amount_requested=target_amount,
            target_amount_obtained=0.0,
            budget=budget,
            currency=currency,
            total_spent=0.0,
            remaining_budget=budget,
            effective_cost_per_unit=None,
            considered=0,
            excluded=excluded,
            notes=[f"No packs contain item matching '{target_name}'."],
        )
        return GoalPlanResult(selected=[], summary=summary)

    def sort_key(c: GoalCandidate):
        tie_break = c.profile_score if profile and profile.weights else c.value_per_dollar
        return (c.cost_per_unit, -(tie_break or 0))

    candidates.sort(key=sort_key)

    selected: List[GoalCandidate] = []
    total_qty = 0.0
    spent = 0.0
    for c in candidates:
        if budget is not None and spent + c.price > budget + 1e-9:
            continue
        selected.append(c)
        spent += c.price
        total_qty += c.target_quantity
        if total_qty >= target_amount:
            break

    remaining_budget = budget - spent if budget is not None else None
    eff_cpu = (spent / total_qty) if total_qty > 0 else None
    notes: List[str] = []
    if total_qty >= target_amount:
        notes.append("Target amount reached.")
    else:
        notes.append("Target amount not reached with available packs.")
    if budget is not None and remaining_budget is not None and remaining_budget < 0:
        notes.append("Budget exceeded.")

    summary = GoalPlanSummary(
        target=target_name,
        target_amount_requested=target_amount,
        target_amount_obtained=round(total_qty, 2),
        budget=budget,
        currency=currency,
        total_spent=round(spent, 2),
        remaining_budget=round(remaining_budget, 2) if remaining_budget is not None else None,
        effective_cost_per_unit=round(eff_cpu, 4) if eff_cpu is not None else None,
        considered=len(candidates),
        excluded=excluded,
        notes=notes,
    )
    return GoalPlanResult(selected=selected, summary=summary)


def export_goal_plan_json(result: GoalPlanResult, output_path: Path, profile: str = "default") -> Path:
    ensure_dir(output_path.parent)
    payload = {
        "profile": profile,
        "summary": result.summary.to_dict(),
        "selected_packs": [c.to_dict() for c in result.selected],
    }
    save_json(output_path, payload)
    return output_path

