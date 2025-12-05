"""Web scraping helpers for wosnerds.com and whiteoutsurvival.wiki.

These functions are intentionally simple and should be mocked in tests; they
are not called automatically in CI.
"""

from __future__ import annotations

import logging
from typing import List, Optional

import requests
from bs4 import BeautifulSoup  # type: ignore

from .schemas import KnowledgeEntity

logger = logging.getLogger(__name__)


def _parse_tables_from_html(game: str, html: str, source: str, detail: str) -> List[KnowledgeEntity]:
    soup = BeautifulSoup(html, "html.parser")
    entities: List[KnowledgeEntity] = []
    tables = soup.find_all("table")
    for t_idx, table in enumerate(tables):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        rows = table.find_all("tr")
        for r_idx, row in enumerate(rows[1:]):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            row_dict = {headers[i] if i < len(headers) else f"col_{i}": cells[i] for i in range(len(cells))}
            name = row_dict.get("Name") or row_dict.get("Hero") or row_dict.get("Building") or row_dict.get("Title") or f"row_{t_idx}_{r_idx}"
            entities.append(
                KnowledgeEntity(
                    id=f"{source}-{t_idx}-{r_idx}-{hash(name)}",
                    game=game,
                    entity_type="table",
                    name=name,
                    source=source,
                    source_detail=detail,
                    attributes=row_dict,
                    raw=row_dict,
                )
            )
    return entities


def scrape_wosnerds(game: str, base_url: str, paths: Optional[List[str]] = None) -> List[KnowledgeEntity]:
    entities: List[KnowledgeEntity] = []
    for path in paths or []:
        url = base_url.rstrip("/") + "/" + path.lstrip("/")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        entities.extend(_parse_tables_from_html(game, resp.text, "wosnerds_site", url))
    logger.info("Scraped %s knowledge entities from wosnerds", len(entities))
    return entities


def scrape_wiki(game: str, base_url: str, paths: Optional[List[str]] = None) -> List[KnowledgeEntity]:
    entities: List[KnowledgeEntity] = []
    for path in paths or []:
        url = base_url.rstrip("/") + "/" + path.lstrip("/")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        entities.extend(_parse_tables_from_html(game, resp.text, "wiki", url))
    logger.info("Scraped %s knowledge entities from wiki", len(entities))
    return entities


__all__ = ["scrape_wosnerds", "scrape_wiki"]
