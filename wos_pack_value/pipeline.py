"""High-level pipeline orchestrating ingestion, valuation, and export."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

from .export.json_export import export_site_json
from .analysis.game_profiles import get_game_profile, GameProfile
from .ingestion.config import load_ingestion_config
from .ingestion.pipeline import ingest_all
from .logging_utils import configure_logging
from .models.domain import ValuedPack
from .validation.validator import validate_packs_and_items, export_validation_report, load_validation_config
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
    enable_validation: bool = True,
    ocr_review_dump_path: Path | None = None,
    ocr_reviewed_path: Path | None = None,
    history_root: Path | None = None,
    game_key: str | None = None,
) -> Tuple[List[ValuedPack], Dict]:
    configure_logging(log_file=log_file)
    logger.info("Starting pipeline")
    ingestion_config = load_ingestion_config(ingestion_config_path)
    ref_handling = ingestion_config.get("reference_handling", {})
    ref_mode = reference_mode_override or ref_handling.get("mode", "tag")
    game_profile: GameProfile = get_game_profile(game_key=game_key)
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
        ocr_review_dump_path=ocr_review_dump_path,
        ocr_reviewed_path=ocr_reviewed_path,
    )
    reference_packs = [p for p in packs if p.is_reference]
    normal_packs = [p for p in packs if not p.is_reference]
    valuation_input = normal_packs if ref_mode in {"exclude", "separate"} else packs
    valuations_path = (processed_dir or DATA_PROCESSED_DIR) / DEFAULT_PROCESSED_VALUATIONS.name
    valued, config = valuate(
        packs=valuation_input,
        config_path=config_path,
        game=game_profile,
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
            game=game_profile,
        )
        if enable_validation:
            validation_cfg = load_validation_config()
            if validation_cfg.get("validation", {}).get("enabled", True):
                report = validate_packs_and_items(
                    packs=[vp.pack.dict() for vp in valued],
                    items=[i.dict() for i in item_defs],
                    config=validation_cfg,
                )
                report_path = export_validation_report(
                    report,
                    site_dir=site_dir or SITE_DATA_DIR,
                    filename=validation_cfg.get("validation", {}).get("report_filename"),
                )
                logger.info(
                    "Validation summary: packs=%s missing_price=%s invalid_price=%s extreme_vpd=%s unknown_items=%s duplicates=%s. Report: %s",
                    report.summary.total_packs,
                    report.summary.num_packs_missing_price,
                    report.summary.num_packs_invalid_price,
                    report.summary.num_packs_extreme_value_per_dollar,
                    report.summary.num_unknown_items,
                    report.summary.num_duplicate_packs,
                    report_path,
                )
        # Optional history snapshot
        if history_root:
            from .history.snapshot import snapshot_site_data

            snapshot_path = snapshot_site_data(site_dir=site_dir or SITE_DATA_DIR, history_root=history_root)
            logger.info("Snapshot of site_data written to %s", snapshot_path)

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
