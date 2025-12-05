"""Game profiles for per-game config overrides."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml

from ..settings import CONFIG_DIR


@dataclass
class GameProfile:
    key: str
    label: str
    description: str
    config_dir: Path | None


def _default_profile() -> GameProfile:
    return GameProfile(
        key="whiteout_survival",
        label="Whiteout Survival",
        description="Default configuration for Whiteout Survival packs.",
        config_dir=CONFIG_DIR / "games" / "whiteout_survival",
    )


def load_game_profiles(config_root: Path = CONFIG_DIR) -> Dict[str, GameProfile]:
    path = config_root / "game_profiles.yaml"
    if not path.exists():
        default = _default_profile()
        return {default.key: default}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    games = {}
    for key, entry in (data.get("games") or {}).items():
        games[key] = GameProfile(
            key=key,
            label=entry.get("label", key),
            description=entry.get("description", ""),
            config_dir=(config_root / entry.get("config_dir")) if entry.get("config_dir") else None,
        )
    if not games:
        default = _default_profile()
        games[default.key] = default
    return games


def get_game_profile(config_root: Path = CONFIG_DIR, game_key: Optional[str] = None) -> GameProfile:
    games = load_game_profiles(config_root)
    default_key = None
    gp_path = config_root / "game_profiles.yaml"
    if gp_path.exists():
        with gp_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            default_key = data.get("default_game")
    default_key = default_key or "whiteout_survival"

    if game_key is None:
        game_key = default_key
    if game_key not in games:
        raise ValueError(f"Unknown game '{game_key}'. Known: {', '.join(sorted(games))}")
    return games[game_key]


def resolve_config_path(base_name: str, game: GameProfile, config_root: Path = CONFIG_DIR) -> Path:
    """Return the game-specific config path if it exists, else root config."""
    if game.config_dir:
        game_path = Path(game.config_dir) / base_name
        if game_path.exists():
            return game_path
    return config_root / base_name


__all__ = ["GameProfile", "load_game_profiles", "get_game_profile", "resolve_config_path"]
