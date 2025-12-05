from pathlib import Path

from wos_pack_value.analysis.ranking import analyze_packs


def test_analyze_ranking_basic():
    packs = [
        {
            "id": "pack-a",
            "name": "Pack A",
            "price": {"amount": 5.0, "currency": "USD"},
            "value": 100.0,
            "items": [
                {"id": "vip", "name": "VIP", "quantity": 100, "category": "vip", "value": 20},
                {"id": "shard", "name": "Shard", "quantity": 10, "category": "shard", "value": 80},
            ],
        },
        {
            "id": "pack-b",
            "name": "Pack B",
            "price": {"amount": 5.0, "currency": "USD"},
            "value": 60.0,
            "items": [
                {"id": "speed", "name": "Speedup", "quantity": 2, "category": "speedup", "value": 60},
            ],
        },
    ]
    config = {
        "analysis": {
            "exclude_reference": False,
            "max_value_per_dollar": 50,
            "focus_categories": ["shard", "speedup"],
            "category_weights": {"shard": 1.0, "speedup": 1.0},
        }
    }
    overall, by_cat, _ = analyze_packs(packs, config)
    assert overall[0]["id"] == "pack-a"
    assert overall[0]["rank_overall"] == 1
    assert overall[1]["rank_overall"] == 2
    assert by_cat["shard"][0]["id"] == "pack-a"
    assert by_cat["speedup"][0]["id"] == "pack-b"


def test_analyze_with_profile_changes_order():
    packs = [
        {
            "id": "pack-a",
            "name": "Pack A",
            "price": {"amount": 10.0, "currency": "USD"},
            "value": 120.0,
            "items": [{"id": "shard", "name": "Shard", "quantity": 10, "category": "shard", "value": 120}],
        },
        {
            "id": "pack-b",
            "name": "Pack B",
            "price": {"amount": 10.0, "currency": "USD"},
            "value": 200.0,
            "items": [{"id": "speed", "name": "Speedup", "quantity": 5, "category": "speedup", "value": 200}],
        },
    ]
    config = {
        "analysis": {
            "exclude_reference": False,
            "max_value_per_dollar": 50,
            "focus_categories": [],
            "category_weights": {},
        }
    }
    from wos_pack_value.analysis.player_profiles import PlayerProfile

    profile = PlayerProfile(name="f2p", description="", weights={"shard": 1.0})
    overall, _, profile_sorted = analyze_packs(packs, config, profile=profile)
    # overall still by value_per_dollar; pack-b has higher
    assert overall[0]["id"] == "pack-b"
    # profile_sorted should prefer shard-heavy pack-a
    assert profile_sorted[0]["id"] == "pack-a"
