from pathlib import Path

from wos_pack_value.history.snapshot import snapshot_site_data
from wos_pack_value.history.diff import diff_packs
from wos_pack_value.utils import ensure_dir, save_json


def test_snapshot_site_data(tmp_path: Path):
    site_dir = tmp_path / "site_data"
    ensure_dir(site_dir)
    packs_path = site_dir / "packs.json"
    items_path = site_dir / "items.json"
    save_json(packs_path, {"packs": [{"id": "a"}]})
    save_json(items_path, {"items": []})

    history_root = tmp_path / "exports"
    snapshot_path = snapshot_site_data(site_dir=site_dir, history_root=history_root)
    assert snapshot_path.exists()
    assert (snapshot_path / "packs.json").exists()
    assert (snapshot_path / "items.json").exists()


def test_diff_packs_new_removed_changed(tmp_path: Path):
    prev = tmp_path / "prev.json"
    curr = tmp_path / "curr.json"
    save_json(prev, {"packs": [{"id": "a", "price": {"amount": 5.0}, "value_per_dollar": 100}, {"id": "b", "price": {"amount": 10.0}, "value_per_dollar": 200}]})
    save_json(curr, {"packs": [{"id": "a", "price": {"amount": 5.0}, "value_per_dollar": 120}, {"id": "c", "price": {"amount": 8.0}, "value_per_dollar": 150}]})

    diff = diff_packs(prev, curr)
    assert diff["summary"]["num_new_packs"] == 1
    assert diff["summary"]["num_removed_packs"] == 1
    assert diff["summary"]["num_changed_packs"] == 1
    assert diff["new_packs"][0]["pack_id"] == "c"
    assert diff["removed_packs"][0]["pack_id"] == "b"
    assert diff["changed_packs"][0]["pack_id"] == "a"

