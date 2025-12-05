"""Helpers for exporting and loading OCR review data."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable, List

from ..models.domain import Pack, PackItem
from ..settings import DEFAULT_OCR_REVIEWED, DEFAULT_OCR_REVIEW_RAW, DATA_REVIEW_DIR
from ..utils import ensure_dir, load_json, save_json, slugify, timestamp

logger = logging.getLogger(__name__)


def dump_raw_ocr_packs(packs: Iterable[Pack], lang: str = "eng", path: Path | None = None) -> Path:
    """Write raw OCR-detected packs to a review JSON file."""
    ensure_dir(DATA_REVIEW_DIR)
    out_path = path or DEFAULT_OCR_REVIEW_RAW
    payload = []
    for idx, pack in enumerate(packs, start=1):
        payload.append(
            {
                "id": pack.pack_id or f"ocr_pack_{idx:03}",
                "source_image": pack.source_file,
                "name_ocr": pack.name,
                "price_ocr": pack.price,
                "currency_ocr": pack.currency,
                "items_ocr": [{"name": it.name, "quantity": it.quantity} for it in pack.items],
                "metadata": {"ocr_language": lang, "timestamp": timestamp()},
            }
        )
    save_json(out_path, payload)
    logger.info("Wrote raw OCR review dump to %s (%s packs)", out_path, len(payload))
    return out_path


def load_reviewed_ocr_packs(path: Path | None = None) -> List[Pack]:
    """Load reviewed OCR packs JSON into Pack objects."""
    review_path = path or DEFAULT_OCR_REVIEWED
    if not review_path.exists():
        return []
    data = load_json(review_path)
    # The reviewed file can be an array or an object with "packs"
    entries: List[Dict] = data if isinstance(data, list) else data.get("packs", [])
    packs: List[Pack] = []
    for entry in entries:
        if entry.get("discarded"):
            continue
        name = entry.get("name") or entry.get("name_ocr") or "Unnamed Pack"
        pack_id = entry.get("id") or slugify(name)
        price = float(entry.get("price", 0) or 0)
        currency = entry.get("currency") or "USD"
        items_data = entry.get("items") or entry.get("items_ocr") or []
        items = [
            PackItem(
                item_id=slugify(it.get("name", f"item-{idx}")),
                name=it.get("name", f"Item {idx}"),
                quantity=float(it.get("quantity", 0) or 0),
                category="unknown",
            )
            for idx, it in enumerate(items_data, start=1)
            if float(it.get("quantity", 0) or 0) > 0
        ]
        packs.append(
            Pack(
                pack_id=pack_id,
                name=name,
                price=price,
                currency=currency,
                source_file=entry.get("source_image"),
                source_sheet=None,
                tags=[],
                items=items,
                meta={"ingestion_source": "ocr_review"},
            )
        )
    logger.info("Loaded %s reviewed OCR packs from %s", len(packs), review_path)
    return packs


__all__ = ["dump_raw_ocr_packs", "load_reviewed_ocr_packs"]
