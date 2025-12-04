from pathlib import Path
import shutil

from wos_pack_value.ingestion.pipeline import ingest_all
from wos_pack_value.ingestion.tabular import parse_excel
from wos_pack_value.valuation.config import load_valuation_config
from wos_pack_value.valuation.engine import value_packs
from wos_pack_value.export.json_export import export_site_json
from wos_pack_value.models.domain import Pack, PackItem


def test_excel_ingestion_pack_headers(tmp_path: Path):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Regular Packs Summary"
    ws.append(["Regular Packs"])
    ws.append([])
    ws.append([None, "Test Pack"])
    ws.append([None, "Item", "Quantity", "Gem per unit", "Total"])
    ws.append([None, "Sample Item", 2, 100, 200])
    ws.append([None, "Gem Total", None, None, 200])
    excel_path = tmp_path / "sample.xlsx"
    wb.save(excel_path)

    packs = parse_excel(excel_path, images_dir=tmp_path / "images")
    assert len(packs) == 1
    pack = packs[0]
    assert pack.name == "Test Pack"
    assert pack.meta.get("gem_total") == 200
    assert pack.items[0].base_value == 100


def _prepare_raw(tmp_path: Path) -> Path:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    sample = Path(__file__).parent / "data" / "sample_packs.csv"
    shutil.copy(sample, raw_dir / "sample_packs.csv")
    return raw_dir


def test_ingestion_creates_packs(tmp_path: Path):
    raw_dir = _prepare_raw(tmp_path)
    packs, items = ingest_all(
        raw_dir=raw_dir,
        processed_dir=tmp_path / "processed",
        images_dir=tmp_path / "images",
        persist=False,
    )
    assert len(packs) == 2
    assert len(items) == 4
    names = sorted([p.name for p in packs])
    assert names == ["Builder Bundle", "Starter Pack"]


def test_valuation_scores(tmp_path: Path):
    raw_dir = _prepare_raw(tmp_path)
    packs, _ = ingest_all(
        raw_dir=raw_dir,
        processed_dir=tmp_path / "processed",
        images_dir=tmp_path / "images",
        persist=False,
    )
    config = load_valuation_config()
    valued = value_packs(packs, config=config)
    assert valued
    first = valued[0]
    assert first.valuation.score >= 0
    assert first.valuation.total_value > 0


def test_export_writes_json(tmp_path: Path):
    raw_dir = _prepare_raw(tmp_path)
    packs, items = ingest_all(
        raw_dir=raw_dir,
        processed_dir=tmp_path / "processed",
        images_dir=tmp_path / "images",
        persist=False,
    )
    config = load_valuation_config()
    valued = value_packs(packs, config=config)
    packs_path, items_path = export_site_json(valued, items=items, site_dir=tmp_path / "site")
    assert packs_path.exists()
    assert items_path.exists()


def test_price_inference_from_hints():
    pack = Pack(
        pack_id="test-pack",
        name="Test Pack",
        price=0.0,
        currency="USD",
        source_file="generated",
        items=[PackItem(item_id="item", name="Item", quantity=1, category="premium_currency")],
        meta={"gem_total": 600},
    )
    config = load_valuation_config()
    config["pack_price_hints"]["test pack"] = 10.0
    valued = value_packs([pack], config=config)
    assert valued[0].valuation.price == 10.0
    assert valued[0].pack.meta.get("price_source", "")[:4] in {"hint", "gem"}
