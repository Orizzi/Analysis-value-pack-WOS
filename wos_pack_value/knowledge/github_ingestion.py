"""Ingest tabular knowledge from locally cloned GitHub repos (wosnerdwarriors)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

import pandas as pd

from .schemas import KnowledgeEntity

logger = logging.getLogger(__name__)


def _classify_table(headers: Iterable[str]) -> str:
    headers_l = [h.lower() for h in headers if h]
    if any("hero" in h for h in headers_l) or any("skill" in h for h in headers_l):
        return "hero"
    if any("building" in h for h in headers_l) or any("level" in h for h in headers_l):
        return "building"
    if any("tech" in h for h in headers_l) or any("research" in h for h in headers_l):
        return "tech"
    return "table"


def _iter_tables(file_path: Path) -> List[pd.DataFrame]:
    if file_path.suffix.lower() in {".csv"}:
        return [pd.read_csv(file_path)]
    if file_path.suffix.lower() in {".xlsx", ".xls"}:
        excel = pd.ExcelFile(file_path)
        return [excel.parse(sheet_name) for sheet_name in excel.sheet_names]
    return []


def extract_knowledge_from_github_root(game: str, root: Path, table_patterns: List[str]) -> List[KnowledgeEntity]:
    entities: List[KnowledgeEntity] = []
    root = Path(root)
    if not root.exists():
        logger.warning("GitHub root %s missing; skipping.", root)
        return entities
    matches = []
    for pattern in table_patterns:
        matches.extend(root.glob(pattern))
    for file_path in matches:
        if not file_path.is_file():
            continue
        try:
            tables = _iter_tables(file_path)
        except Exception as exc:
            logger.warning("Failed reading %s: %s", file_path, exc)
            continue
        for idx, df in enumerate(tables):
            if df.empty:
                continue
            entity_type = _classify_table(df.columns)
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                name = str(row_dict.get("Name") or row_dict.get("Hero") or row_dict.get("Building") or row_dict.get("name") or "Unknown")
                ent_id = f"{file_path.stem}-{idx}-{hash(name)}"
                entities.append(
                    KnowledgeEntity(
                        id=str(ent_id),
                        game=game,
                        entity_type=entity_type,
                        name=name,
                        source="wosnerdwarriors_github",
                        source_detail=f"{file_path}",
                        tags=[],
                        attributes={k: v for k, v in row_dict.items() if pd.notna(v)},
                        raw=row_dict,
                    )
                )
    logger.info("Extracted %s knowledge entities from %s", len(entities), root)
    return entities


__all__ = ["extract_knowledge_from_github_root"]
