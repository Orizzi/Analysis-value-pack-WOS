from pathlib import Path

from wos_pack_value.analysis.budget_planner import plan_budget, PlannedPack, PlanSummary


def _pack(pid, name, price, vpd, total_value, ref=False):
    return PlannedPack(
        pack_id=pid,
        name=name,
        price=price,
        total_value=total_value,
        value_per_dollar=vpd,
        rank_overall=None,
        is_reference=ref,
    )


def test_budget_planner_selects_best_under_budget():
    packs = [
        _pack("a", "Pack A", price=10.0, vpd=10.0, total_value=100.0),
        _pack("b", "Pack B", price=15.0, vpd=8.0, total_value=120.0),
        _pack("c", "Pack C", price=20.0, vpd=5.0, total_value=100.0),
    ]
    selected, summary = plan_budget(packs, budget=30.0)
    ids = [p.pack_id for p in selected]
    assert ids == ["a", "b"]
    assert summary.total_spent == 25.0
    assert summary.total_value == 220.0
    assert summary.remaining_budget == 5.0
    assert round(summary.average_value_per_dollar, 2) == round(220.0 / 25.0, 2)


def test_budget_planner_respects_max_count():
    packs = [
        _pack("a", "Pack A", price=10.0, vpd=10.0, total_value=100.0),
        _pack("b", "Pack B", price=15.0, vpd=9.0, total_value=135.0),
    ]
    selected, summary = plan_budget(packs, budget=50.0, max_count=1)
    assert len(selected) == 1
    assert selected[0].pack_id == "a"
    assert summary.total_spent == 10.0


def test_budget_planner_excludes_reference_by_default():
    packs = [
        _pack("a", "Pack A", price=10.0, vpd=10.0, total_value=100.0, ref=True),
        _pack("b", "Pack B", price=10.0, vpd=9.0, total_value=90.0, ref=False),
    ]
    selected, summary = plan_budget(packs, budget=20.0)
    assert [p.pack_id for p in selected] == ["b"]
    assert summary.excluded == 1


def test_budget_planner_handles_zero_budget():
    packs = [
        _pack("a", "Pack A", price=10.0, vpd=10.0, total_value=100.0),
    ]
    selected, summary = plan_budget(packs, budget=0.0)
    assert selected == []
    assert summary.total_spent == 0.0
    assert summary.total_value == 0.0


def test_budget_planner_respects_profile_weights():
    packs = [
        PlannedPack(
            pack_id="a",
            name="Pack A",
            price=10.0,
            total_value=120.0,
            value_per_dollar=12.0,
            category_values={"shard": 10, "speedup": 10},
        ),
        PlannedPack(
            pack_id="b",
            name="Pack B",
            price=10.0,
            total_value=90.0,
            value_per_dollar=9.0,
            category_values={"shard": 50, "speedup": 1},
        ),
    ]
    from wos_pack_value.analysis.player_profiles import PlayerProfile

    profile = PlayerProfile(name="f2p", description="", weights={"shard": 1.0, "speedup": 0.1})
    selected, _ = plan_budget(packs, budget=10.0, profile=profile)
    assert selected[0].pack_id == "b"
