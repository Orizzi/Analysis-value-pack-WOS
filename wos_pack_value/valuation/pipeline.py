"""Pipeline helpers for valuation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

from ..models.domain import Pack, ValuedPack
from ..settings import DEFAULT_PROCESSED_PACKS, DEFAULT_PROCESSED_VALUATIONS
from ..utils import load_json, save_json, timestamp
from .config import load_valuation_config
from .engine import value_packs

logger = logging.getLogger(__name__)


def load_packs_from_processed(path: Path = DEFAULT_PROCESSED_PACKS) -> List[Pack]:
    data = load_json(path)
    return [Pack(**raw) for raw in data.get("packs", [])]


def valuate(
    packs: List[Pack] | None = None,
    config_path: Path | None = None,
    persist: bool = True,
    processed_path: Path = DEFAULT_PROCESSED_PACKS,
    valuations_path: Path = DEFAULT_PROCESSED_VALUATIONS,
) -> Tuple[List[ValuedPack], Dict]:
    config = load_valuation_config(config_path or None)
    if packs is None:
        packs = load_packs_from_processed(processed_path)
    valued = value_packs(packs, config=config)

    if persist:
        save_json(
            valuations_path,
            {
                "generated_at": timestamp(),
                "config": config,
                "packs": [vp.pack.dict() for vp in valued],
                "valuations": [vp.valuation.dict() for vp in valued],
            },
        )
    return valued, config

