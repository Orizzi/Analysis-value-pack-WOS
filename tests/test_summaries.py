from wos_pack_value.analysis.summaries import (
    generate_all_pack_summaries,
    generate_pack_summary,
    SummaryContext,
)


def test_generate_all_pack_summaries_respects_overall_and_category_strength():
    packs = [
        {
            "id": "a",
            "name": "Alpha",
            "price": 10.0,
            "total_value": 200.0,
            "value_per_dollar": 20.0,
            "category_values": {"shards": 120.0, "vip": 20.0},
        },
        {
            "id": "b",
            "name": "Beta",
            "price": 10.0,
            "total_value": 100.0,
            "value_per_dollar": 10.0,
            "category_values": {"vip": 60.0},
        },
        {
            "id": "c",
            "name": "Gamma",
            "price": 10.0,
            "total_value": 20.0,
            "value_per_dollar": 2.0,
            "category_values": {"resources": 20.0},
        },
    ]

    summaries = generate_all_pack_summaries(packs, profile_name="f2p")

    assert summaries["a"]  # summary exists
    assert "exceptional" in summaries["a"]
    assert "Shards" in summaries["a"]
    assert "F2P" in summaries["a"]

    assert "solid" in summaries["b"]
    assert "Vip" in summaries["b"]

    assert "average" in summaries["c"] or "situational" in summaries["c"]


def test_generate_pack_summary_handles_missing_data():
    ctx = SummaryContext(overall_percentiles={"p90": 0, "p75": 0, "p50": 0, "p25": 0}, category_percentiles={})
    summary = generate_pack_summary(
        {"price": 0, "total_value": 0, "value_per_dollar": 0, "category_values": {}},
        context=ctx,
    )
    assert "hard to estimate" in summary
