from pathlib import Path

from wos_pack_value.analysis.goal_planner import plan_for_goal
from wos_pack_value.analysis.player_profiles import PlayerProfile
from wos_pack_value.utils import save_json


def _write_site_data(tmp_path: Path, packs: list[dict], ranking_overall: dict):
    save_json(tmp_path / "packs.json", {"packs": packs})
    save_json(tmp_path / "pack_ranking_overall.json", ranking_overall)
    return tmp_path


def test_goal_planner_reaches_target_without_budget(tmp_path: Path):
    packs = [
        {
            "id": "a",
            "name": "Cheap Shards",
            "price": {"amount": 10, "currency": "USD"},
            "items": [{"id": "shard-x", "name": "Hero X Shard", "quantity": 20}],
        },
        {
            "id": "b",
            "name": "Big Shards",
            "price": {"amount": 25, "currency": "USD"},
            "items": [{"id": "shard-x", "name": "Hero X Shard", "quantity": 80}],
        },
    ]
    ranking = {"packs": [{"id": "a", "value_per_dollar": 4}, {"id": "b", "value_per_dollar": 5}]}
    site_dir = _write_site_data(tmp_path, packs, ranking)

    result = plan_for_goal(
        site_dir=site_dir,
        target_name="Hero X Shard",
        target_amount=90,
        budget=None,
        currency="USD",
        include_reference=False,
        profile=None,
    )

    assert result.selected
    assert result.summary.target_amount_obtained >= 90
    # Should pick the cheaper per unit pack first (pack b cost/unit=0.3125, pack a=0.5)
    assert result.selected[0].pack_id == "b"


def test_goal_planner_respects_budget(tmp_path: Path):
    packs = [
        {
            "id": "a",
            "name": "Small Shards",
            "price": {"amount": 10, "currency": "USD"},
            "items": [{"id": "shard-x", "name": "Hero X Shard", "quantity": 30}],
        },
        {
            "id": "b",
            "name": "Large Shards",
            "price": {"amount": 40, "currency": "USD"},
            "items": [{"id": "shard-x", "name": "Hero X Shard", "quantity": 80}],
        },
    ]
    ranking = {"packs": [{"id": "a", "value_per_dollar": 4}, {"id": "b", "value_per_dollar": 5}]}
    site_dir = _write_site_data(tmp_path, packs, ranking)

    result = plan_for_goal(
        site_dir=site_dir,
        target_name="shard-x",
        target_amount=100,
        budget=45,
        currency="USD",
    )

    assert result.summary.total_spent <= 45
    assert result.selected  # should select at least one pack within budget
    assert result.summary.target_amount_obtained <= 110


def test_goal_planner_handles_no_candidates(tmp_path: Path):
    packs = [
        {"id": "a", "name": "No Target", "price": {"amount": 10, "currency": "USD"}, "items": []},
    ]
    ranking = {"packs": [{"id": "a", "value_per_dollar": 4}]}
    site_dir = _write_site_data(tmp_path, packs, ranking)

    result = plan_for_goal(
        site_dir=site_dir,
        target_name="missing-item",
        target_amount=10,
        budget=20,
        currency="USD",
    )

    assert not result.selected
    assert any("No packs" in note for note in result.summary.notes)


def test_goal_planner_profile_tiebreak(tmp_path: Path):
    packs = [
        {
            "id": "a",
            "name": "Balanced",
            "price": {"amount": 20, "currency": "USD"},
            "items": [{"id": "shard-x", "name": "Hero X Shard", "quantity": 40}],
        },
        {
            "id": "b",
            "name": "Shard Heavy",
            "price": {"amount": 20, "currency": "USD"},
            "items": [{"id": "shard-x", "name": "Hero X Shard", "quantity": 40}],
        },
    ]
    ranking = {
        "packs": [
            {"id": "a", "value_per_dollar": 5, "category_values": {"vip": 100}},
            {"id": "b", "value_per_dollar": 5, "category_values": {"shards": 200}},
        ]
    }
    site_dir = _write_site_data(tmp_path, packs, ranking)
    profile = PlayerProfile(name="f2p", description="F2P", weights={"shards": 1.0})

    result = plan_for_goal(
        site_dir=site_dir,
        target_name="shard-x",
        target_amount=20,
        budget=None,
        currency="USD",
        profile=profile,
    )

    assert result.selected
    assert result.selected[0].pack_id == "b"
