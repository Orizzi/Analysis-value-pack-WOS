"""Lightweight linking between items and knowledge entities."""

from __future__ import annotations

from typing import Any, Dict, List

from .schemas import KnowledgeEntity


def build_item_to_knowledge_links(
    items: List[Dict[str, Any]], knowledge_entities: List[KnowledgeEntity]
) -> Dict[str, List[str]]:
    links: Dict[str, List[str]] = {}
    if not items or not knowledge_entities:
        return links
    for item in items:
        name = str(item.get("name", "")).lower()
        item_id = item.get("id") or item.get("item_id") or item.get("name")
        matched = []
        for ent in knowledge_entities:
            if ent.entity_type == "hero":
                if name and ent.name.lower() in name:
                    matched.append(ent.id)
            else:
                if name == ent.name.lower():
                    matched.append(ent.id)
        if matched and item_id:
            links[item_id] = matched
    return links


__all__ = ["build_item_to_knowledge_links"]
