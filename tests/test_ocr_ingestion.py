from pathlib import Path

from wos_pack_value.ingestion.ocr import ingest_ocr_text_blocks
from wos_pack_value.valuation.config import load_valuation_config
from wos_pack_value.valuation.engine import value_packs


def test_ocr_text_to_pack_and_value():
    text = """Mega Pack
$4.99
Fire Crystal x300
Speedup 60m x2
VIP Point x500
"""
    packs = ingest_ocr_text_blocks([("mega.png", text)])
    assert len(packs) == 1
    pack = packs[0]
    assert pack.name == "Mega Pack"
    assert abs(pack.price - 4.99) < 0.01
    assert len(pack.items) == 3
    config = load_valuation_config()
    valued = value_packs(packs, config=config)
    assert valued[0].valuation.price > 0
    assert valued[0].valuation.total_value > 0


def test_ocr_text_without_price_uses_defaults():
    text = """Mystery Pack
Fire Crystal x200
Speedup 60m x1
"""
    packs = ingest_ocr_text_blocks([("mystery.png", text)])
    pack = packs[0]
    assert pack.price == 0.0  # left to inference
    config = load_valuation_config()
    valued = value_packs(packs, config=config)
    # price should be inferred via gem_total if available; here it stays fallback
    assert valued[0].valuation.price >= 0.0
