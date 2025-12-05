"""Knowledge base utilities (schemas, ingestion, linking)."""

from .schemas import KnowledgeEntity
from .loader import save_knowledge_entities, load_knowledge_entities
from .github_ingestion import extract_knowledge_from_github_root
from .web_scraping import scrape_wosnerds, scrape_wiki
from .linking import build_item_to_knowledge_links

__all__ = [
    "KnowledgeEntity",
    "save_knowledge_entities",
    "load_knowledge_entities",
    "extract_knowledge_from_github_root",
    "scrape_wosnerds",
    "scrape_wiki",
    "build_item_to_knowledge_links",
]
