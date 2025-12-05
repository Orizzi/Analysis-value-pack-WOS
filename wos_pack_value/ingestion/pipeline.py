"""Ingestion pipeline entry points."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple

from ..models.domain import ItemDefinition, Pack
from ..settings import (
    DATA_PROCESSED_DIR,
    DATA_RAW_DIR,
    DEFAULT_PROCESSED_ITEMS,
    DEFAULT_PROCESSED_PACKS,
    IMAGES_RAW_DIR,
    SCREENSHOTS_DIR,
)
from ..utils import ensure_dir, save_json, timestamp
from .config import load_ingestion_config
from .ocr import ingest_screenshots
from .tabular import parse_file

logger = logging.getLogger(__name__)


def build_item_definitions(packs: List[Pack]) -> List[ItemDefinition]:
    items: dict[str, ItemDefinition] = {}
    for pack in packs:
        for item in pack.items:
            if item.item_id not in items:
                items[item.item_id] = ItemDefinition(
                    item_id=item.item_id,
                    name=item.name,
                    category=item.category,
                    icon=item.icon,
                    base_value=item.base_value,
                )
    return list(items.values())


def ingest_all(
    raw_dir: Path = DATA_RAW_DIR,
    processed_dir: Path = DATA_PROCESSED_DIR,
    images_dir: Path = IMAGES_RAW_DIR,
    default_currency: str = "USD",
    persist: bool = True,
    use_ocr: bool = False,
    screenshots_dir: Path | None = None,
    ocr_lang: str = "eng",
    ingestion_config_path: Path | None = None,
) -> Tuple[List[Pack], List[ItemDefinition]]:
    ensure_dir(raw_dir)
    ensure_dir(processed_dir)
    ensure_dir(images_dir)
    ingestion_config = load_ingestion_config(ingestion_config_path)
    ref_config = ingestion_config.get("reference_handling", {})

    packs: List[Pack] = []
    for path in sorted(raw_dir.iterdir()):
        if not path.is_file():
            continue
        packs.extend(
            parse_file(
                path,
                images_dir=images_dir,
                default_currency=default_currency,
                reference_config=ref_config,
            )
        )

    if use_ocr:
        packs.extend(
            ingest_screenshots(
                screenshots_dir=screenshots_dir or SCREENSHOTS_DIR,
                default_currency=default_currency,
                lang=ocr_lang,
            )
        )

    item_defs = build_item_definitions(packs)
    logger.info("Ingested %s packs (%s items)", len(packs), sum(len(p.items) for p in packs))

    if persist:
        ensure_dir(processed_dir)
        save_json(DEFAULT_PROCESSED_PACKS, {"generated_at": timestamp(), "packs": [p.dict() for p in packs]})
        save_json(DEFAULT_PROCESSED_ITEMS, {"generated_at": timestamp(), "items": [i.dict() for i in item_defs]})

    return packs, item_defs
