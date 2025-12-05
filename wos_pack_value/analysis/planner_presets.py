"""Planner presets loader (per game)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .game_profiles import GameProfile
from ..settings import CONFIG_DIR


@dataclass
class PlannerPreset:
    key: str
    label: str
    type: str  # "budget" or "goal"
    description: Optional[str] = None
    budget: Optional[float] = None
    currency: Optional[str] = None
    profile: Optional[str] = None
    include_reference: Optional[bool] = None
    target_name: Optional[str] = None
    target_amount: Optional[float] = None


def load_planner_presets(config_root: Path = CONFIG_DIR, game: GameProfile | None = None) -> List[PlannerPreset]:
    path = config_root / "planner_presets.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    game_key = game.key if game else None
    game_section = data.get("games", {})
    entries = game_section.get(game_key, {}).get("presets", []) if game_key else []
    presets: List[PlannerPreset] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        presets.append(
            PlannerPreset(
                key=str(entry.get("key", "")),
                label=entry.get("label", entry.get("key", "")),
                type=entry.get("type", "budget"),
                description=entry.get("description"),
                budget=entry.get("budget"),
                currency=entry.get("currency"),
                profile=entry.get("profile"),
                include_reference=entry.get("include_reference"),
                target_name=entry.get("target_name"),
                target_amount=entry.get("target_amount"),
            )
        )
    return presets


def find_preset(presets: List[PlannerPreset], key: str) -> Optional[PlannerPreset]:
    for preset in presets:
        if preset.key == key:
            return preset
    return None


__all__ = ["PlannerPreset", "load_planner_presets", "find_preset"]
