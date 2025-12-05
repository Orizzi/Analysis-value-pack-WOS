from pathlib import Path

from wos_pack_value.analysis.player_profiles import load_profiles, get_profile, PlayerProfile
from wos_pack_value.analysis.ranking import compute_profile_score


def test_load_profiles_defaults_when_missing(tmp_path: Path):
    cfg_path = tmp_path / "missing.yaml"
    profiles = load_profiles(cfg_path)
    assert "default" in profiles
    assert profiles["default"].weights == {}


def test_load_profiles_custom(tmp_path: Path):
    cfg = tmp_path / "profiles.yaml"
    cfg.write_text(
        """
profiles:
  f2p:
    description: f2p profile
    weights:
      shard: 1.0
      speedup: 0.5
""",
        encoding="utf-8",
    )
    profiles = load_profiles(cfg)
    assert "f2p" in profiles
    assert profiles["f2p"].weights["shard"] == 1.0
    assert get_profile("f2p", config_path=cfg).name == "f2p"
    assert get_profile("unknown", config_path=cfg).name == "default"


def test_compute_profile_score_uses_weights():
    profile = PlayerProfile(name="f2p", description="", weights={"shard": 1.0, "vip": 0.5})
    pack_metrics = {
        "price": {"amount": 10},
        "value_per_dollar": 5,
        "category_values": {"shard": 50, "vip": 20},
    }
    score = compute_profile_score(pack_metrics, profile)
    # (50*1 + 20*0.5)=60 / 10 = 6
    assert round(score, 2) == 6.0


def test_compute_profile_score_defaults_to_vpd_when_no_weights():
    profile = PlayerProfile(name="default", description="", weights={})
    pack_metrics = {"price": {"amount": 10}, "value_per_dollar": 7}
    score = compute_profile_score(pack_metrics, profile)
    assert score == 7
