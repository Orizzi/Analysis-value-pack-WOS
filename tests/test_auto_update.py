from pathlib import Path

from wos_pack_value.automation import auto_update


class DummyGit:
    def __init__(self):
        self.add_called = False
        self.commit_called = False
        self.status_lines = []
        self.run_code = 0
        self.commit_message = None

    def run_pipeline(self, **kwargs):
        return self.run_code

    def status(self):
        return self.status_lines

    def add(self, paths):
        self.add_called = True
        self.add_paths = list(paths)
        return 0

    def commit(self, msg):
        self.commit_called = True
        self.commit_message = msg
        return 0


def test_auto_update_no_changes(monkeypatch, tmp_path: Path):
    dummy = DummyGit()
    monkeypatch.setattr(auto_update, "_run_pipeline_cmd", lambda **kwargs: dummy.run_pipeline(**kwargs))
    monkeypatch.setattr(auto_update, "_git_status", lambda: dummy.status())
    monkeypatch.setattr(auto_update, "_git_add", lambda paths: dummy.add(paths))
    monkeypatch.setattr(auto_update, "_git_commit", lambda msg: dummy.commit(msg))

    code = auto_update.auto_update_and_commit(raw_dir=tmp_path, site_dir=tmp_path / "site")
    assert code == 0
    assert not dummy.add_called
    assert not dummy.commit_called


def test_auto_update_with_changes_dry_run(monkeypatch, tmp_path: Path):
    dummy = DummyGit()
    dummy.status_lines = [" M site_data/packs.json"]
    monkeypatch.setattr(auto_update, "_run_pipeline_cmd", lambda **kwargs: dummy.run_pipeline(**kwargs))
    monkeypatch.setattr(auto_update, "_git_status", lambda: dummy.status())
    monkeypatch.setattr(auto_update, "_git_add", lambda paths: dummy.add(paths))
    monkeypatch.setattr(auto_update, "_git_commit", lambda msg: dummy.commit(msg))

    code = auto_update.auto_update_and_commit(raw_dir=tmp_path, site_dir=tmp_path / "site", dry_run=True)
    assert code == 0
    assert not dummy.add_called
    assert not dummy.commit_called


def test_auto_update_with_changes_commit(monkeypatch, tmp_path: Path):
    dummy = DummyGit()
    dummy.status_lines = [" M site_data/packs.json"]
    monkeypatch.setattr(auto_update, "_run_pipeline_cmd", lambda **kwargs: dummy.run_pipeline(**kwargs))
    monkeypatch.setattr(auto_update, "_git_status", lambda: dummy.status())
    monkeypatch.setattr(auto_update, "_git_add", lambda paths: dummy.add(paths))
    monkeypatch.setattr(auto_update, "_git_commit", lambda msg: dummy.commit(msg))

    code = auto_update.auto_update_and_commit(raw_dir=tmp_path, site_dir=Path("site_data"))
    assert code == 0
    assert dummy.add_called
    assert dummy.commit_called
    assert dummy.commit_message.startswith("Update pack data")

