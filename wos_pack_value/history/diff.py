"""Compute diffs between pack snapshots."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ..utils import load_json


def _pack_key(pack: Dict[str, Any]) -> str:
    if "id" in pack and pack.get("id"):
        return str(pack.get("id"))
    name = str(pack.get("name", "")).lower()
    price_field = pack.get("price", {})
    price = price_field.get("amount") if isinstance(price_field, dict) else price_field
    return f"{name}|{price}"


def _pack_summary_fields(pack: Dict[str, Any]) -> Dict[str, Any]:
    price_field = pack.get("price", {})
    price = price_field.get("amount") if isinstance(price_field, dict) else price_field
    currency = price_field.get("currency") if isinstance(price_field, dict) else ""
    return {
        "pack_id": pack.get("id"),
        "pack_name": pack.get("name"),
        "price": price,
        "currency": currency,
        "value_per_dollar": pack.get("value_per_dollar"),
        "value": pack.get("value"),
        "is_reference": pack.get("is_reference", False),
    }


def diff_packs(
    previous_packs_path: Path,
    current_packs_path: Path,
    *,
    value_tol: float = 1e-6,
) -> Dict[str, Any]:
    prev_data = load_json(previous_packs_path)
    curr_data = load_json(current_packs_path)
    prev_packs = prev_data.get("packs", prev_data if isinstance(prev_data, list) else [])
    curr_packs = curr_data.get("packs", curr_data if isinstance(curr_data, list) else [])

    prev_map = {_pack_key(p): p for p in prev_packs}
    curr_map = {_pack_key(p): p for p in curr_packs}

    new_keys = set(curr_map) - set(prev_map)
    removed_keys = set(prev_map) - set(curr_map)
    common_keys = set(curr_map) & set(prev_map)

    new_packs = [_pack_summary_fields(curr_map[k]) for k in sorted(new_keys)]
    removed_packs = [_pack_summary_fields(prev_map[k]) for k in sorted(removed_keys)]

    changed_packs = []
    for k in sorted(common_keys):
        prev = prev_map[k]
        curr = curr_map[k]
        price_prev = prev.get("price", {}).get("amount") if isinstance(prev.get("price"), dict) else prev.get("price")
        price_curr = curr.get("price", {}).get("amount") if isinstance(curr.get("price"), dict) else curr.get("price")
        vpd_prev = prev.get("value_per_dollar")
        vpd_curr = curr.get("value_per_dollar")
        value_prev = prev.get("value")
        value_curr = curr.get("value")
        if (
            price_prev != price_curr
            or (vpd_prev is not None and vpd_curr is not None and abs(vpd_prev - vpd_curr) > value_tol)
            or (value_prev is not None and value_curr is not None and abs(value_prev - value_curr) > value_tol)
        ):
            changed_packs.append(
                {
                    "pack_id": curr.get("id"),
                    "pack_name": curr.get("name"),
                    "before": {"price": price_prev, "value_per_dollar": vpd_prev, "value": value_prev},
                    "after": {"price": price_curr, "value_per_dollar": vpd_curr, "value": value_curr},
                }
            )

    summary = {
        "num_packs_previous": len(prev_packs),
        "num_packs_current": len(curr_packs),
        "num_new_packs": len(new_packs),
        "num_removed_packs": len(removed_packs),
        "num_changed_packs": len(changed_packs),
    }

    return {
        "previous_snapshot": str(previous_packs_path),
        "current_snapshot": str(current_packs_path),
        "summary": summary,
        "new_packs": new_packs,
        "removed_packs": removed_packs,
        "changed_packs": changed_packs,
    }

