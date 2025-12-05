"""Core schemas for structured knowledge entities."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass
class KnowledgeEntity:
    id: str
    game: str
    entity_type: str  # hero/building/tech/resource/guide/table/page/unknown
    name: str
    source: str  # e.g., wosnerdwarriors_github, wosnerds_site, wiki
    source_detail: str  # repo/file/path/url/etc.
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

    def dict(self) -> Dict[str, Any]:
        return asdict(self)
