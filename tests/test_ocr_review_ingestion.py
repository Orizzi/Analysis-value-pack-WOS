from pathlib import Path

from wos_pack_value.ingestion.ocr_review import load_reviewed_ocr_packs
from wos_pack_value.ingestion.pipeline import ingest_all
from wos_pack_value.utils import ensure_dir, save_json


def test_load_reviewed_ocr_packs(tmp_path: Path):
    reviewed_path = tmp_path / "ocr_packs_reviewed.json"
    sample = [
        {
            "id": "ocr_pack_001",
            "name": "Reviewed Pack",
            "price": 9.99,
            "currency": "USD",
            "items": [{"name": "Fire Crystal", "quantity": 100}],
            "source_image": "screenshots/sample.png",
        }
    ]
    save_json(reviewed_path, sample)

    packs = load_reviewed_ocr_packs(reviewed_path)
    assert len(packs) == 1
    p = packs[0]
    assert p.name == "Reviewed Pack"
    assert p.price == 9.99
    assert p.items[0].name == "Fire Crystal"


def test_ingest_all_uses_reviewed_packs(tmp_path: Path):
    review_dir = tmp_path / "data_review"
    ensure_dir(review_dir)
    reviewed_path = review_dir / "ocr_packs_reviewed.json"
    save_json(
        reviewed_path,
        [
            {
                "id": "ocr_pack_002",
                "name": "Reviewed Only",
                "price": 4.99,
                "currency": "USD",
                "items": [{"name": "Speedup 1h", "quantity": 3}],
                "source_image": "screenshots/new.png",
            }
        ],
    )

    packs, _ = ingest_all(
        raw_dir=tmp_path / "raw",
        processed_dir=tmp_path / "processed",
        images_dir=tmp_path / "images",
        use_ocr=True,
        screenshots_dir=tmp_path / "shots",
        ocr_reviewed_path=reviewed_path,
        persist=False,
    )
    names = [p.name for p in packs]
    assert "Reviewed Only" in names
