"""High-level pipeline orchestrating ingestion, valuation, and export."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

from .export.json_export import export_site_json
from .ingestion.pipeline import ingest_all
from .logging_utils import configure_logging
from .models.domain import ValuedPack
from .settings import (
    DATA_PROCESSED_DIR,
    DATA_RAW_DIR,
    DEFAULT_CONFIG_PATH,
    DEFAULT_PROCESSED_ITEMS,
    DEFAULT_PROCESSED_PACKS,
    DEFAULT_PROCESSED_VALUATIONS,
    DEFAULT_SITE_ITEMS,
    DEFAULT_SITE_PACKS,
    IMAGES_RAW_DIR,
    SCREENSHOTS_DIR,
    SITE_DATA_DIR,
)
from .valuation.pipeline import valuate

logger = logging.getLogger(__name__)


def run_pipeline(
    config_path: Path | None = None,
    log_file: Path | None = None,
    raw_dir: Path | None = None,
    processed_dir: Path | None = None,
    images_dir: Path | None = None,
    site_dir: Path | None = None,
    use_ocr: bool = False,
    screenshots_dir: Path | None = None,
    ocr_lang: str = "eng",
) -> Tuple[List[ValuedPack], Dict]:
    configure_logging(log_file=log_file)
    logger.info("Starting pipeline")
    packs, item_defs = ingest_all(
        raw_dir=raw_dir or DATA_RAW_DIR,
        processed_dir=processed_dir or DATA_PROCESSED_DIR,
        images_dir=images_dir or IMAGES_RAW_DIR,
        use_ocr=use_ocr,
        screenshots_dir=screenshots_dir or SCREENSHOTS_DIR,
        ocr_lang=ocr_lang,
    )
    valuations_path = (processed_dir or DATA_PROCESSED_DIR) / DEFAULT_PROCESSED_VALUATIONS.name
    valued, config = valuate(
        packs=packs,
        config_path=config_path,
        valuations_path=valuations_path,
        processed_path=(processed_dir or DATA_PROCESSED_DIR) / DEFAULT_PROCESSED_PACKS.name,
    )
    export_site_json(
        valued_packs=valued,
        items=item_defs,
        site_dir=site_dir or SITE_DATA_DIR,
    )
    logger.info("Pipeline finished")
    return valued, config


__all__ = [
    "run_pipeline",
    "export_site_json",
    "ingest_all",
    "valuate",
    "DEFAULT_PROCESSED_ITEMS",
    "DEFAULT_PROCESSED_PACKS",
    "DEFAULT_SITE_ITEMS",
    "DEFAULT_SITE_PACKS",
    "DEFAULT_CONFIG_PATH",
]
