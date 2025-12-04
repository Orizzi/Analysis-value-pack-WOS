from pathlib import Path
import shutil

from wos_pack_value.ingestion.pipeline import ingest_all
from wos_pack_value.valuation.config import load_valuation_config
from wos_pack_value.valuation.engine import value_packs
from wos_pack_value.export.json_export import export_site_json


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
