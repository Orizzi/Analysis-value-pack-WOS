"""OCR-based ingestion for pack screenshots.

This module is optional: if OCR dependencies are missing, calls that require
OCR will raise a clear error. Unit tests can exercise the text-to-pack parser
without needing OCR binaries.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from ..models.domain import Pack, PackItem
from ..utils import slugify

logger = logging.getLogger(__name__)


def _try_import_pytesseract():
    try:
        import pytesseract  # type: ignore
    except Exception as exc:  # pragma: no cover - import guard
        raise RuntimeError(
            "pytesseract is not installed. Install it or disable --use-ocr-screenshots."
        ) from exc
    return pytesseract


def _extract_text(path: Path, lang: str = "eng") -> str:
    pytesseract = _try_import_pytesseract()
    try:
        from PIL import Image  # pillow is already a dependency
    except Exception as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("Pillow is required for OCR ingestion.") from exc
    image = Image.open(path)
    return pytesseract.image_to_string(image, lang=lang)


def _parse_price(line: str) -> Tuple[Optional[float], Optional[str]]:
    currency = None
    if "$" in line:
        currency = "USD"
    elif "€" in line or "eur" in line.lower():
        currency = "EUR"
    match = re.search(r"([0-9]+(?:[.,][0-9]+)?)", line)
    if not match:
        return None, currency
    amount = float(match.group(1).replace(",", "."))
    return amount, currency


def _parse_item_line(line: str) -> Optional[Tuple[str, float]]:
    # Examples:
    # "300 Fire Crystals"
    # "Fire Crystal x300"
    # "Speedup 60m 2"
    patterns = [
        r"^(?P<qty>[0-9]+(?:[.,][0-9]+)?)\s*[xX]?\s*(?P<name>.+)$",
        r"^(?P<name>.+?)\s*[xX]\s*(?P<qty>[0-9]+(?:[.,][0-9]+)?)$",
    ]
    for pat in patterns:
        m = re.match(pat, line.strip())
        if m:
            qty = float(m.group("qty").replace(",", "."))
            name = m.group("name").strip()
            return name, qty
    return None


def parse_ocr_text_to_pack(text: str, source_file: Path, default_currency: str = "USD") -> Pack:
    """Parse raw OCR text into a Pack with PackItems."""
    lines = [ln.strip() for ln in text.splitlines() if ln and ln.strip()]
    pack_name = lines[0] if lines else source_file.stem
    price = 0.0
    currency = default_currency
    items: List[PackItem] = []

    for line in lines[1:]:
        # Try to detect price
        if "$" in line or "€" in line or "usd" in line.lower() or "eur" in line.lower():
            maybe_price, maybe_currency = _parse_price(line)
            if maybe_price is not None:
                price = maybe_price
            if maybe_currency:
                currency = maybe_currency
            continue
        parsed = _parse_item_line(line)
        if parsed:
            name, qty = parsed
            items.append(
                PackItem(
                    item_id=slugify(name),
                    name=name,
                    quantity=qty,
                    category="unknown",
                )
            )

    pack_id = slugify(f"{pack_name}-{price}-{source_file.stem}")
    return Pack(
        pack_id=pack_id,
        name=pack_name,
        price=price,
        currency=currency,
        source_file=str(source_file),
        source_sheet=None,
        tags=[],
        items=items,
        meta={"price_source": "ocr" if price else "ocr|unpriced", "ingestion_source": "ocr"},
    )


def ingest_screenshots(
    screenshots_dir: Path,
    default_currency: str = "USD",
    lang: str = "eng",
) -> List[Pack]:
    """Run OCR over all screenshots in a directory and return Pack objects."""
    if not screenshots_dir.exists():
        logger.info("Screenshot directory %s missing; skipping OCR ingestion", screenshots_dir)
        return []
    packs: List[Pack] = []
    for img_path in sorted(screenshots_dir.iterdir()):
        if img_path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        try:
            text = _extract_text(img_path, lang=lang)
            pack = parse_ocr_text_to_pack(text, img_path, default_currency=default_currency)
            packs.append(pack)
        except Exception as exc:
            logger.warning("Failed OCR for %s: %s", img_path.name, exc)
    logger.info("OCR ingestion produced %s packs from %s", len(packs), screenshots_dir)
    return packs


def ingest_ocr_text_blocks(blocks: Iterable[Tuple[str, str]], default_currency: str = "USD") -> List[Pack]:
    """Helper to ingest pre-supplied OCR text blocks (for tests)."""
    packs: List[Pack] = []
    for filename, text in blocks:
        packs.append(parse_ocr_text_to_pack(text, Path(filename), default_currency=default_currency))
    return packs
