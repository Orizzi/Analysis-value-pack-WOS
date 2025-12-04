"""Tabular ingestion for CSV and Excel sources."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd
from openpyxl import load_workbook

from ..models.domain import Pack, PackItem
from ..utils import ensure_dir, slugify

logger = logging.getLogger(__name__)


COLUMN_ALIASES = {
    "pack": "pack_name",
    "bundle": "pack_name",
    "bundle_name": "pack_name",
    "pack_name": "pack_name",
    "name": "pack_name",
    "price": "price",
    "price_usd": "price",
    "price($)": "price",
    "cost": "price",
    "usd": "price",
    "currency": "currency",
    "$": "currency",
    "item": "item_name",
    "items": "item_name",
    "reward": "item_name",
    "item_name": "item_name",
    "quantity": "quantity",
    "qty": "quantity",
    "amount": "quantity",
    "count": "quantity",
    "category": "category",
    "type": "category",
    "tag": "tags",
    "tags": "tags",
    "note": "notes",
}


def _normalize_columns(columns: Iterable[str]) -> List[str]:
    normalized = []
    for col in columns:
        key = str(col).strip().lower()
        key = key.replace(" ", "_").replace("(", "").replace(")", "")
        key = COLUMN_ALIASES.get(key, key)
        normalized.append(key)
    return normalized


def _to_float(value) -> float:
    try:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = str(value).replace("$", "").replace(",", "").strip()
        return float(cleaned) if cleaned else 0.0
    except Exception:
        return 0.0


def _extract_images(ws, dest_dir: Path, prefix: str) -> List[Tuple[int, Path]]:
    """Extract embedded images and return mapping of row -> saved path."""
    ensure_dir(dest_dir)
    mappings: List[Tuple[int, Path]] = []
    for idx, image in enumerate(getattr(ws, "_images", []), start=1):
        row_num = None
        try:
            row_num = image.anchor._from.row + 1  # type: ignore[attr-defined]
        except Exception:
            row_num = None
        filename = dest_dir / f"{prefix}_img_{idx}.png"
        try:
            data = image._data()  # type: ignore[attr-defined]
            with filename.open("wb") as f:
                f.write(data)
            mappings.append((row_num, filename))
        except Exception as exc:
            logger.warning("Could not extract image %s: %s", filename.name, exc)
    return mappings


def _expand_merged_cells(ws) -> None:
    for merged in ws.merged_cells.ranges:
        top_left = merged.start_cell
        value = top_left.value
        for row in ws[merged.coord]:
            for cell in row:
                cell.value = value


def _sheet_to_dataframe(ws) -> Tuple[pd.DataFrame, List[int]]:
    """Convert a worksheet to DataFrame while remembering sheet row numbers."""
    _expand_merged_cells(ws)
    rows: List[List] = []
    row_numbers: List[int] = []
    for r_index, row in enumerate(ws.iter_rows(values_only=True), start=1):
        values = list(row)
        if all(v is None for v in values):
            continue
        rows.append(values)
        row_numbers.append(r_index)
    if not rows:
        return pd.DataFrame(), []

    header = [str(h) if h is not None else f"col_{idx+1}" for idx, h in enumerate(rows[0])]
    data = rows[1:]
    data_row_numbers = row_numbers[1:]
    df = pd.DataFrame(data, columns=_normalize_columns(header))
    return df, data_row_numbers


def _normalize_dataframe(df: pd.DataFrame, default_pack_name: str, default_currency: str) -> pd.DataFrame:
    df = df.copy()
    df.columns = _normalize_columns(df.columns)
    if "pack_name" not in df.columns:
        df["pack_name"] = default_pack_name
    if "item_name" not in df.columns:
        df["item_name"] = "Unknown Item"
    if "quantity" not in df.columns:
        df["quantity"] = 0
    if "price" not in df.columns:
        df["price"] = 0.0
    if "currency" not in df.columns:
        df["currency"] = default_currency
    if "tags" not in df.columns:
        df["tags"] = ""
    return df


def _pack_from_rows(
    df: pd.DataFrame, row_numbers: List[int], source_file: Path, sheet_name: str | None, image_map: Dict[int, Path]
) -> List[Pack]:
    packs: Dict[str, Pack] = {}
    for idx, (_, row) in enumerate(df.iterrows()):
        pack_name = str(row.get("pack_name") or "Unnamed Pack").strip()
        price = _to_float(row.get("price"))
        currency = str(row.get("currency") or "USD").strip().upper()
        tags_val = row.get("tags")
        tags = [t.strip() for t in str(tags_val).split(",") if str(tags_val) and t.strip()] if tags_val else []
        pack_id = slugify(f"{pack_name}-{price}-{source_file.stem}")
        pack = packs.get(pack_id)
        if pack is None:
            pack = Pack(
                pack_id=pack_id,
                name=pack_name,
                price=price,
                currency=currency,
                source_file=str(source_file),
                source_sheet=sheet_name,
                tags=tags,
                items=[],
            )
            packs[pack_id] = pack

        item_name = str(row.get("item_name") or "Unknown Item").strip()
        category = str(row.get("category") or "unknown").strip().lower() or "unknown"
        quantity = _to_float(row.get("quantity"))
        item_id = slugify(item_name)
        sheet_row_number = row_numbers[idx] if idx < len(row_numbers) else None
        icon_path = image_map.get(sheet_row_number) if sheet_row_number is not None else None

        pack.items.append(
            PackItem(
                item_id=item_id,
                name=item_name,
                category=category,
                quantity=quantity,
                icon=str(icon_path) if icon_path else None,
                source_row=sheet_row_number,
            )
        )
    return list(packs.values())


def parse_csv(path: Path, default_currency: str = "USD") -> List[Pack]:
    logger.info("Ingesting CSV %s", path.name)
    df = pd.read_csv(path)
    df = _normalize_dataframe(df, default_pack_name=path.stem, default_currency=default_currency)
    row_numbers = list(range(2, len(df) + 2))  # pretend header on row 1 for consistency
    return _pack_from_rows(df, row_numbers, path, None, image_map={})


def parse_excel(path: Path, images_dir: Path, default_currency: str = "USD") -> List[Pack]:
    logger.info("Ingesting Excel %s", path.name)
    workbook = load_workbook(path, data_only=True)
    all_packs: List[Pack] = []
    for sheet_name in workbook.sheetnames:
        ws = workbook[sheet_name]
        image_pairs = _extract_images(ws, images_dir, f"{path.stem}_{slugify(sheet_name)}")
        image_map = {row: file for row, file in image_pairs if row is not None}
        df, row_numbers = _sheet_to_dataframe(ws)
        if df.empty:
            continue
        df = _normalize_dataframe(df, default_pack_name=path.stem, default_currency=default_currency)
        sheet_packs = _pack_from_rows(df, row_numbers, path, sheet_name, image_map)
        all_packs.extend(sheet_packs)
    return all_packs


def parse_file(path: Path, images_dir: Path, default_currency: str = "USD") -> List[Pack]:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv"}:
        return parse_csv(path, default_currency=default_currency)
    if suffix in {".xlsx", ".xlsm"}:
        return parse_excel(path, images_dir=images_dir, default_currency=default_currency)
    logger.warning("Skipping unsupported file: %s", path.name)
    return []

