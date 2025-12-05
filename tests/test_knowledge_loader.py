from pathlib import Path

from wos_pack_value.knowledge.loader import save_knowledge_entities, load_knowledge_entities
from wos_pack_value.knowledge.schemas import KnowledgeEntity


def test_save_and_load_round_trip(tmp_path: Path):
    entities = [
        KnowledgeEntity(
            id="hero-1",
            game="whiteout_survival",
            entity_type="hero",
            name="Hero One",
            source="test",
            source_detail="file",
            tags=["test"],
            attributes={"rarity": "Epic"},
            raw={"Name": "Hero One"},
        )
    ]
    path = tmp_path / "entities.json"
    save_knowledge_entities(path, entities)
    loaded = load_knowledge_entities(path)
    assert len(loaded) == 1
    assert loaded[0].name == "Hero One"
