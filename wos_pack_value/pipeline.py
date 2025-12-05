"""High-level pipeline orchestrating ingestion, valuation, and export."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

from .export.json_export import export_site_json
from .ingestion.config import load_ingestion_config
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
    ingestion_config_path: Path | None = None,
    reference_mode_override: str | None = None,
    summary_only: bool = False,
) -> Tuple[List[ValuedPack], Dict]:
    configure_logging(log_file=log_file)
    logger.info("Starting pipeline")
    ingestion_config = load_ingestion_config(ingestion_config_path)
    ref_handling = ingestion_config.get("reference_handling", {})
    ref_mode = reference_mode_override or ref_handling.get("mode", "tag")
    packs, item_defs = ingest_all(
        raw_dir=raw_dir or DATA_RAW_DIR,
        processed_dir=processed_dir or DATA_PROCESSED_DIR,
        images_dir=images_dir or IMAGES_RAW_DIR,
        use_ocr=use_ocr,
        screenshots_dir=screenshots_dir or SCREENSHOTS_DIR,
        ocr_lang=ocr_lang,
        ingestion_config_path=ingestion_config_path,
        ingestion_config_data=ingestion_config,
        persist=not summary_only,
    )
    reference_packs = [p for p in packs if p.is_reference]
    normal_packs = [p for p in packs if not p.is_reference]
    valuation_input = normal_packs if ref_mode in {"exclude", "separate"} else packs
    valuations_path = (processed_dir or DATA_PROCESSED_DIR) / DEFAULT_PROCESSED_VALUATIONS.name
    valued, config = valuate(
        packs=valuation_input,
        config_path=config_path,
        valuations_path=valuations_path,
        processed_path=(processed_dir or DATA_PROCESSED_DIR) / DEFAULT_PROCESSED_PACKS.name,
    )
    if not summary_only:
    export_site_json(
        valued_packs=valued,
        items=item_defs,
        site_dir=site_dir or SITE_DATA_DIR,
        reference_mode=ref_mode,
        reference_packs=reference_packs,
    )

    summary = {
        "packs_total": len(packs),
        "packs_reference": len(reference_packs),
        "packs_valuated": len(valuation_input),
        "items_total": sum(len(p.items) for p in packs),
        "reference_mode": ref_mode,
        "use_ocr": use_ocr,
    }
    logger.info(
        "Run summary: packs=%s (reference=%s, valuated=%s) items=%s ref_mode=%s ocr=%s",
        summary["packs_total"],
        summary["packs_reference"],
        summary["packs_valuated"],
        summary["items_total"],
        ref_mode,
        use_ocr,
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
