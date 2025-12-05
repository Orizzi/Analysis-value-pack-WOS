from wos_pack_value.validation.validator import validate_packs_and_items


def test_validation_detects_missing_and_extreme():
    packs = [
        {"id": "p1", "name": "No Price", "price": None, "value_per_dollar": 0},
        {"id": "p2", "name": "Bad Price", "price": {"amount": -1}, "value_per_dollar": 0},
        {"id": "p3", "name": "Normal", "price": {"amount": 10}, "value_per_dollar": 5},
        {"id": "p4", "name": "Extreme", "price": {"amount": 10}, "value_per_dollar": 1000},
    ]
    items = [{"item_id": "i1", "name": "Unknown", "base_value": None}]
    report = validate_packs_and_items(packs, items, config={"validation": {"value_per_dollar_threshold_std": 0.01}})
    assert report.summary.num_packs_missing_price == 1
    assert report.summary.num_packs_invalid_price == 1
    assert report.summary.num_unknown_items == 1
    assert report.summary.num_packs_extreme_value_per_dollar == 1
