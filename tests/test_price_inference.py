from wos_pack_value.models.domain import Pack, PackItem
from wos_pack_value.valuation.config import load_valuation_config
from wos_pack_value.valuation.engine import value_packs


def _base_pack(name: str, price: float = 0.0, currency: str = "USD", gem_total=None):
    pack = Pack(
        pack_id=name,
        name=name,
        price=price,
        currency=currency,
        source_file="generated",
        items=[PackItem(item_id="item", name="Item", quantity=1, category="premium_currency")],
        meta={},
    )
    if gem_total is not None:
        pack.meta["gem_total"] = gem_total
    return pack


def test_snap_uses_price_hint_and_tier():
    config = load_valuation_config()
    config["pack_price_hints"]["test pack"] = 10.0
    pack = _base_pack("Test Pack", price=0.0, currency="USD")
    valued = value_packs([pack], config=config)
    inferred = valued[0].valuation.price
    # Should snap to nearest USD tier (9.99) rather than raw 10.0
    assert abs(inferred - 9.99) < 0.05
    assert "snap" in valued[0].pack.meta.get("price_source", "")


def test_gem_total_snaps_to_eur_tier():
    config = load_valuation_config()
    pack = _base_pack("Euro Pack", price=0.0, currency="EUR", gem_total=1800)
    valued = value_packs([pack], config=config)
    # gem_total 1800 / 300 = 6 -> nearest EUR tier 5.99
    assert abs(valued[0].valuation.price - 5.99) < 0.05


def test_snap_respects_max_delta():
    config = load_valuation_config()
    config["price_inference"]["snap_max_delta"] = 0.1  # effectively disable snapping
    pack = _base_pack("Weird Pack", price=7.5, currency="USD")
    valued = value_packs([pack], config=config)
    assert valued[0].valuation.price == 7.5
