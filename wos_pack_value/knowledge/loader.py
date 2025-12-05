"""Serialize/deserialize knowledge entities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from .schemas import KnowledgeEntity
from ..utils import ensure_dir


def save_knowledge_entities(path: Path, entities: Iterable[KnowledgeEntity]) -> None:
    ensure_dir(path.parent)
    payload = [e.dict() for e in entities]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_knowledge_entities(path: Path) -> List[KnowledgeEntity]:
    data = json.loads(path.read_text(encoding="utf-8"))
    entities = []
    for entry in data:
        entities.append(KnowledgeEntity(**entry))
    return entities


__all__ = ["save_knowledge_entities", "load_knowledge_entities"]
