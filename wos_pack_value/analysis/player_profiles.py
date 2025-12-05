"""Player profile configuration loader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import yaml

from ..settings import DEFAULT_PLAYER_PROFILES_PATH


@dataclass
class PlayerProfile:
    name: str
    description: str
    weights: Dict[str, float]


def load_profiles(path: Path | None = None) -> Dict[str, PlayerProfile]:
    cfg_path = path or DEFAULT_PLAYER_PROFILES_PATH
    if not cfg_path.exists():
        # Minimal default profile
        return {
            "default": PlayerProfile(name="default", description="Baseline profile", weights={}),
        }
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    profiles_raw = data.get("profiles", {})
    profiles: Dict[str, PlayerProfile] = {}
    for name, cfg in profiles_raw.items():
        profiles[name] = PlayerProfile(
            name=name,
            description=cfg.get("description", ""),
            weights=cfg.get("weights", {}) or {},
        )
    if "default" not in profiles:
        profiles["default"] = PlayerProfile(name="default", description="Baseline profile", weights={})
    return profiles


def get_profile(name: str | None, config_path: Path | None = None) -> PlayerProfile:
    profiles = load_profiles(config_path)
    if not name:
        return profiles["default"]
    profile = profiles.get(name)
    if profile:
        return profile
    return profiles["default"]
