from pathlib import Path

from wos_pack_value.analysis.announcements import generate_announcement


def test_generate_announcement_basic():
    packs = [
        {"id": "a", "name": "Pack A", "price": {"amount": 10, "currency": "USD"}, "value_per_dollar": 5, "summary": "Great."},
        {"id": "b", "name": "Pack B", "price": {"amount": 20, "currency": "USD"}, "value_per_dollar": 8, "summary": "Better."},
        {"id": "c", "name": "Ref", "price": {"amount": 5, "currency": "USD"}, "value_per_dollar": 9, "is_reference": True},
    ]
    md = generate_announcement(packs, top_n=2)
    assert "Pack B" in md and "Pack A" in md
    assert "Ref" not in md  # excluded reference


def test_generate_announcement_profile_sort():
    packs = [
        {"id": "a", "name": "Pack A", "price": {"amount": 10, "currency": "USD"}, "value_per_dollar": 5, "profile_score": 1},
        {"id": "b", "name": "Pack B", "price": {"amount": 10, "currency": "USD"}, "value_per_dollar": 4, "profile_score": 9},
    ]
    md = generate_announcement(packs, profile_name="f2p", top_n=1)
    assert "Pack B" in md  # profile_score sorting


def test_generate_announcement_includes_title_and_summary():
    packs = [
        {"id": "a", "name": "Pack A", "price": {"amount": 10, "currency": "USD"}, "value_per_dollar": 5, "summary": "Line."},
    ]
    md = generate_announcement(packs, title="Custom Title", top_n=1)
    assert "Custom Title" in md
    assert "Summary" in md
