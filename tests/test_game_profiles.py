from pathlib import Path

import pytest

from wos_pack_value.analysis.game_profiles import get_game_profile, load_game_profiles


def test_default_profile_when_missing_config(tmp_path: Path):
    profiles = load_game_profiles(tmp_path)  # no file
    assert "whiteout_survival" in profiles
    gp = get_game_profile(tmp_path, None)
    assert gp.key == "whiteout_survival"


def test_unknown_game_raises(tmp_path: Path):
    cfg = tmp_path / "game_profiles.yaml"
    cfg.write_text(
        """
default_game: "whiteout_survival"
games:
  whiteout_survival:
    label: "Whiteout Survival"
    config_dir: "config/games/whiteout_survival"
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        get_game_profile(tmp_path, "unknown_game")
