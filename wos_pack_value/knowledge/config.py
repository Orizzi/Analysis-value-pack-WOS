"""Load external sources configuration (game-aware)."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict

from ..settings import CONFIG_DIR
from ..analysis.game_profiles import GameProfile


def load_external_sources_config(config_root: Path = CONFIG_DIR, game: GameProfile | None = None) -> Dict[str, Any]:
    path = config_root / "external_sources.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    game_key = game.key if game else None
    return (data.get("games", {}) or {}).get(game_key, {})


__all__ = ["load_external_sources_config"]
