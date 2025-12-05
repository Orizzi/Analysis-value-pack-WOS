from pathlib import Path

from openpyxl import Workbook

from wos_pack_value.ingestion.tabular import parse_excel
from wos_pack_value.ingestion.pipeline import ingest_all
from wos_pack_value.export.json_export import export_site_json
from wos_pack_value.valuation.engine import value_packs
from wos_pack_value.valuation.config import load_valuation_config
from wos_pack_value.settings import SITE_DATA_DIR
from wos_pack_value.utils import ensure_dir


def _make_workbook(path: Path):
    wb = Workbook()
    ws1 = wb.active
    ws1.title = "NormalPack"
    ws1.append(["Normal Packs"])
    ws1.append([])
    ws1.append([None, "Starter Pack"])
    ws1.append([None, "Item", "Quantity", "Gem per unit", "Total"])
    ws1.append([None, "Fire Crystal", 100, 1, 100])

    ws2 = wb.create_sheet("LibraryRates")
    ws2.append(["Library Data"])
    ws2.append([])
    ws2.append([None, "Lookup Row"])
    ws2.append([None, "Item", "Quantity", "Gem per unit", "Total"])
    ws2.append([None, "Rate A", 1, 0, 0])

    wb.save(path)


def test_reference_sheet_detection(tmp_path: Path):
    excel_path = tmp_path / "sample.xlsx"
    _make_workbook(excel_path)
    packs = parse_excel(excel_path, images_dir=tmp_path / "images", reference_config={"sheet_name_patterns": ["library"]})
    assert any(p.is_reference for p in packs)
    assert any(not p.is_reference for p in packs)


def test_reference_export_separate(tmp_path: Path):
    excel_path = tmp_path / "sample.xlsx"
    _make_workbook(excel_path)
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    excel_path.rename(raw_dir / excel_path.name)
    processed_dir = tmp_path / "processed"
    site_dir = tmp_path / "site"
    ensure_dir(site_dir)

    packs, _ = ingest_all(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        images_dir=tmp_path / "images",
        persist=False,
        ingestion_config_path=None,
    )
    ref_packs = [p for p in packs if p.is_reference]
    normal_packs = [p for p in packs if not p.is_reference]
    config = load_valuation_config()
    valued = value_packs(normal_packs, config=config)
    packs_path, items_path = export_site_json(
        valued_packs=valued,
        items=None,
        site_dir=site_dir,
        reference_mode="separate",
        reference_packs=ref_packs,
    )
    assert packs_path.exists()
    assert items_path.exists()
    ref_json = site_dir / "reference_packs.json"
    assert ref_json.exists()
