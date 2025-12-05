from wos_pack_value.knowledge.schemas import KnowledgeEntity
from wos_pack_value.knowledge.linking import build_item_to_knowledge_links


def test_build_item_to_knowledge_links_hero_match():
    items = [{"id": "sarge-shard", "name": "Sarge Shard", "quantity": 10}]
    entities = [
        KnowledgeEntity(
            id="hero-sarge",
            game="whiteout_survival",
            entity_type="hero",
            name="Sarge",
            source="test",
            source_detail="",
        )
    ]
    links = build_item_to_knowledge_links(items, entities)
    assert "sarge-shard" in links
    assert "hero-sarge" in links["sarge-shard"]
