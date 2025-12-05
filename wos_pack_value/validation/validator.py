"""Validation utilities for packs and items."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Dict, Iterable, List, Optional

import yaml

from ..settings import DEFAULT_VALIDATION_CONFIG_PATH, DEFAULT_SITE_VALIDATION_REPORT, SITE_DATA_DIR
from ..utils import ensure_dir, save_json


@dataclass
class PackIssue:
    pack_id: str
    pack_name: str
    price: float
    value_per_dollar: float
    detail: str


@dataclass
class ItemIssue:
    item_id: str
    item_name: str
    detail: str
    packs: List[str] = field(default_factory=list)


@dataclass
class ValidationSummary:
    total_packs: int = 0
    total_items: int = 0
    num_packs_missing_price: int = 0
    num_packs_invalid_price: int = 0
    num_packs_extreme_value_per_dollar: int = 0
    num_unknown_items: int = 0
    num_duplicate_packs: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


@dataclass
class ValidationReport:
    summary: ValidationSummary = field(default_factory=ValidationSummary)
    packs_missing_price: List[PackIssue] = field(default_factory=list)
    packs_invalid_price: List[PackIssue] = field(default_factory=list)
    packs_extreme_value_per_dollar: List[PackIssue] = field(default_factory=list)
    unknown_items: List[ItemIssue] = field(default_factory=list)
    duplicate_packs: List[List[str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "packs_missing_price": [issue.__dict__ for issue in self.packs_missing_price],
            "packs_invalid_price": [issue.__dict__ for issue in self.packs_invalid_price],
            "packs_extreme_value_per_dollar": [issue.__dict__ for issue in self.packs_extreme_value_per_dollar],
            "unknown_items": [issue.__dict__ for issue in self.unknown_items],
            "duplicate_packs": self.duplicate_packs,
        }


def load_validation_config(path: Path | None = None) -> Dict[str, Any]:
    cfg_path = path or DEFAULT_VALIDATION_CONFIG_PATH
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {"validation": {"enabled": True, "value_per_dollar_threshold_std": 3.0, "report_filename": "validation_report.json"}}


def _std_threshold(values: List[float], multiplier: float) -> float:
    if len(values) < 2:
        return math.inf
    return mean(values) + multiplier * stdev(values)


def _detect_duplicates(packs: List[Dict[str, Any]]) -> List[List[str]]:
    seen: Dict[str, List[str]] = {}
    for p in packs:
        price = p.get("price", {}).get("amount", 0) if isinstance(p.get("price"), dict) else p.get("price", 0)
        items = tuple(sorted([(it.get("id"), it.get("quantity")) for it in p.get("items", [])]))
        key = (price, items)
        seen.setdefault(str(key), []).append(p.get("id"))
    return [ids for ids in seen.values() if len(ids) > 1]


def validate_packs_and_items(
    packs: Iterable[Dict[str, Any]],
    items: Iterable[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None,
) -> ValidationReport:
    cfg = config or load_validation_config()
    val_cfg = cfg.get("validation", {})
    threshold_std = float(val_cfg.get("value_per_dollar_threshold_std", 3.0) or 3.0)
    report = ValidationReport()

    pack_list = list(packs)
    item_list = list(items)
    report.summary.total_packs = len(pack_list)
    report.summary.total_items = len(item_list)

    vpd_values = []
    for p in pack_list:
        price_field = p.get("price", 0)
        price = price_field.get("amount", 0) if isinstance(price_field, dict) else price_field
        vpd = float(p.get("value_per_dollar", 0) or 0)
        if price in (None, ""):
            report.packs_missing_price.append(
                PackIssue(p.get("id", ""), p.get("name", ""), price=0, value_per_dollar=vpd, detail="Missing price")
            )
        elif price <= 0:
            report.packs_invalid_price.append(
                PackIssue(p.get("id", ""), p.get("name", ""), price=price, value_per_dollar=vpd, detail="Non-positive price")
            )
        else:
            vpd_values.append(vpd)

    if vpd_values:
        threshold = _std_threshold(vpd_values, multiplier=threshold_std)
        for p in pack_list:
            price_field = p.get("price", 0)
            price = price_field.get("amount", 0) if isinstance(price_field, dict) else price_field or 0
            vpd = float(p.get("value_per_dollar", 0) or 0)
            if price and vpd > threshold:
                report.packs_extreme_value_per_dollar.append(
                    PackIssue(
                        p.get("id", ""),
                        p.get("name", ""),
                        price=price,
                        value_per_dollar=vpd,
                        detail=f"VPD above threshold ({vpd:.2f} > {threshold:.2f})",
                    )
                )

    # Unknown items: items with missing or zero base value
    for it in item_list:
        val = it.get("base_value")
        if val in (None, 0, 0.0, ""):
            report.unknown_items.append(
                ItemIssue(
                    item_id=it.get("item_id", ""),
                    item_name=it.get("name", ""),
                    detail="Missing or zero base value",
                    packs=[],
                )
            )

    report.summary.num_packs_missing_price = len(report.packs_missing_price)
    report.summary.num_packs_invalid_price = len(report.packs_invalid_price)
    report.summary.num_packs_extreme_value_per_dollar = len(report.packs_extreme_value_per_dollar)
    report.summary.num_unknown_items = len(report.unknown_items)

    # Duplicates heuristic
    report.duplicate_packs = _detect_duplicates(pack_list)
    report.summary.num_duplicate_packs = len(report.duplicate_packs)

    return report


def export_validation_report(report: ValidationReport, site_dir: Path = SITE_DATA_DIR, filename: Optional[str] = None) -> Path:
    ensure_dir(site_dir)
    out_path = site_dir / (filename or DEFAULT_SITE_VALIDATION_REPORT.name)
    save_json(out_path, report.to_dict())
    return out_path
