from pathlib import Path

from wos_pack_value.analysis.item_categories import (
    ItemCategoryConfig,
    CategoryRule,
    classify_item,
    aggregate_category_values,
    load_item_category_config,
)


def test_classify_item_matches_contains_and_exact(tmp_path: Path):
    cfg_path = tmp_path / "item_categories.yaml"
    cfg_path.write_text(
        """
categories:
  shards:
    match:
      name_contains: ["shard"]
  vip:
    match:
      name_contains: ["vip"]
  special:
    match:
      name_exact: ["unique-token"]
""",
        encoding="utf-8",
    )
    cfg = load_item_category_config(cfg_path)
    assert classify_item({"name": "Hero Shard"}, cfg) == ["shards"]
    assert classify_item({"name": "VIP Points"}, cfg) == ["vip"]
    assert classify_item({"name": "Other", "item_id": "unique-token"}, cfg) == ["special"]
    assert classify_item({"name": "Unknown"}, cfg) == []


def test_aggregate_category_values_with_breakdown():
    cfg = ItemCategoryConfig(categories={"shards": CategoryRule(name_contains=["shard"]), "speedups": CategoryRule(name_contains=["speedup"])})
    items = [
        {"item_id": "a", "name": "Shard A", "category": None},
        {"item_id": "b", "name": "Speedup 5m", "category": None},
    ]
    breakdown = {"a": 100.0, "b": 50.0}
    totals = aggregate_category_values(items, breakdown, cfg)
    assert totals["shards"] == 100.0
    assert totals["speedups"] == 50.0
