"""Generate Markdown/Discord-friendly announcements from existing exports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..settings import (
    DEFAULT_SITE_PACKS,
    DEFAULT_SITE_ANALYSIS_PROFILE,
    SITE_DATA_DIR,
)
from ..utils import load_json


def _load_packs_with_profile(site_dir: Path, profile_name: Optional[str] = None) -> List[Dict[str, Any]]:
    packs_path = site_dir / DEFAULT_SITE_PACKS.name
    if not packs_path.exists():
        raise FileNotFoundError("packs.json not found; run `wos-pack-value run --with-analysis` first.")
    packs = load_json(packs_path).get("packs", [])

    # Merge profile-specific ranking if available
    if profile_name:
        profile_path = site_dir / DEFAULT_SITE_ANALYSIS_PROFILE.format(profile=profile_name)
        if profile_path.exists():
            profile_data = load_json(profile_path)
            profile_map = {p.get("id"): p for p in profile_data.get("packs", [])}
            for p in packs:
                prof = profile_map.get(p.get("id"))
                if prof:
                    p["profile_score"] = prof.get("profile_score") or prof.get("value_per_dollar")
                    p["profile_rank"] = prof.get("profile_rank")
    return packs


def _filter_and_sort(
    packs: List[Dict[str, Any]],
    *,
    profile_name: Optional[str],
    top_n: int,
    include_reference: bool = False,
) -> List[Dict[str, Any]]:
    eligible = []
    for p in packs:
        if (p.get("is_reference") and not include_reference) or not p.get("price"):
            continue
        price_val = p.get("price", {})
        price = price_val.get("amount", price_val) if isinstance(price_val, dict) else price_val
        if not price or price <= 0:
            continue
        metric = None
        if profile_name and p.get("profile_score") is not None:
            metric = float(p.get("profile_score") or 0.0)
        else:
            metric = float(p.get("value_per_dollar") or 0.0)
        if metric <= 0:
            continue
        eligible.append((metric, p))
    eligible.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in eligible[:top_n]]


def _format_pack_line(idx: int, pack: Dict[str, Any]) -> str:
    price_val = pack.get("price", {})
    if isinstance(price_val, dict):
        price = price_val.get("amount")
        currency = price_val.get("currency", "")
    else:
        price = price_val
        currency = ""
    vpd = pack.get("value_per_dollar") or 0
    summary = pack.get("summary") or "No summary available; see Pack Explorer for details."
    lines = [
        f"{idx}. **{pack.get('name', 'Unknown Pack')}** – {price:.2f} {currency}".strip(),
        f"   • Value per {currency or 'currency'}: {vpd:.2f}",
    ]
    if pack.get("profile_score") is not None:
        lines.append(f"   • Profile score: {pack.get('profile_score'):.2f}")
    rank = pack.get("profile_rank") or pack.get("rank_overall")
    if rank:
        lines.append(f"   • Rank: {rank}")
    lines.append(f"   • Summary: {summary}")
    return "\n".join(lines)


def generate_announcement(
    packs: List[Dict[str, Any]],
    *,
    profile_name: Optional[str] = None,
    top_n: int = 5,
    title: Optional[str] = None,
    include_reference: bool = False,
) -> str:
    selected = _filter_and_sort(packs, profile_name=profile_name, top_n=top_n, include_reference=include_reference)
    heading = title or (
        f"Top {len(selected)} packs for profile: {profile_name}" if profile_name else f"Top {len(selected)} packs right now"
    )
    if not selected:
        return f"**{heading}**\n\nNo eligible packs found."
    lines = [f"**{heading}**", ""]
    for idx, pack in enumerate(selected, start=1):
        lines.append(_format_pack_line(idx, pack))
        lines.append("")  # spacing
    return "\n".join(lines).strip()


def load_and_generate_announcement(
    site_dir: Path = SITE_DATA_DIR,
    *,
    profile_name: Optional[str] = None,
    top_n: int = 5,
    title: Optional[str] = None,
    include_reference: bool = False,
) -> str:
    packs = _load_packs_with_profile(site_dir, profile_name=profile_name)
    return generate_announcement(
        packs,
        profile_name=profile_name,
        top_n=top_n,
        title=title,
        include_reference=include_reference,
    )


__all__ = ["generate_announcement", "load_and_generate_announcement"]
