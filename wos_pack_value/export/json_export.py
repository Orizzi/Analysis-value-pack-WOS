"""Export valued data to static JSON for the future site."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List, Optional

from ..models.domain import ItemDefinition, Pack, ValuedPack
from ..settings import DEFAULT_SITE_ITEMS, DEFAULT_SITE_PACKS, DEFAULT_SITE_REFERENCES, SITE_DATA_DIR
from ..utils import ensure_dir, save_json, timestamp

logger = logging.getLogger(__name__)


def _derive_items_from_packs(valued_packs: Iterable[ValuedPack]) -> List[ItemDefinition]:
    seen: dict[str, ItemDefinition] = {}
    for vp in valued_packs:
        for item in vp.pack.items:
            if item.item_id not in seen:
                seen[item.item_id] = ItemDefinition(
                    item_id=item.item_id,
                    name=item.name,
                    category=item.category,
                    icon=item.icon,
                    base_value=item.base_value,
                )
    return list(seen.values())


def export_site_json(
    valued_packs: List[ValuedPack],
    items: Optional[List[ItemDefinition]] = None,
    site_dir: Path = SITE_DATA_DIR,
    reference_mode: str = "tag",
    reference_packs: Optional[List[Pack]] = None,
) -> tuple[Path, Path]:
    ensure_dir(site_dir)
    reference_packs = reference_packs or []
    packs_payload = []
    for vp in valued_packs:
        pack = vp.pack
        valuation = vp.valuation
        packs_payload.append(
            {
                "id": pack.pack_id,
                "name": pack.name,
                "price": {"amount": pack.price, "currency": pack.currency},
                "source": {"file": pack.source_file, "sheet": pack.source_sheet},
                "tags": pack.tags,
                "is_reference": pack.is_reference,
                "items": [
                    {
                        "id": item.item_id,
                        "name": item.name,
                        "quantity": item.quantity,
                        "category": item.category,
                        "icon": item.icon,
                        "value": valuation.breakdown.get(item.item_id, 0.0),
                    }
                    for item in pack.items
                ],
                "value": valuation.total_value,
                "price_to_value": valuation.ratio,
                "score": valuation.score,
                "label": valuation.label,
                "color": valuation.color,
            }
        )

    items_payload = (items or _derive_items_from_packs(valued_packs))

    packs_path = site_dir / DEFAULT_SITE_PACKS.name
    items_path = site_dir / DEFAULT_SITE_ITEMS.name
    save_json(packs_path, {"generated_at": timestamp(), "packs": packs_payload})
    save_json(items_path, {"generated_at": timestamp(), "items": [item.dict() for item in items_payload]})
    reference_path = None
    if reference_mode == "separate" and reference_packs:
        ref_payload = [
            {
                "id": p.pack_id,
                "name": p.name,
                "source": {"file": p.source_file, "sheet": p.source_sheet},
                "tags": p.tags,
                "items": [item.dict() for item in p.items],
                "meta": p.meta,
            }
            for p in reference_packs
        ]
        reference_path = site_dir / DEFAULT_SITE_REFERENCES.name
        save_json(reference_path, {"generated_at": timestamp(), "reference_packs": ref_payload})
    logger.info("Exported site data to %s and %s", packs_path, items_path)
    return packs_path, items_path
