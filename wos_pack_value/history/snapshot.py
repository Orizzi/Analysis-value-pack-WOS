"""Snapshot site_data exports into a timestamped history directory."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from ..settings import (
    DEFAULT_SITE_ANALYSIS_BY_CATEGORY,
    DEFAULT_SITE_ANALYSIS_OVERALL,
    DEFAULT_SITE_ITEMS,
    DEFAULT_SITE_PACKS,
    DEFAULT_SITE_VALIDATION_REPORT,
    SITE_DATA_DIR,
)
from ..utils import ensure_dir


DEFAULT_SNAPSHOT_FILES: tuple[Path, ...] = (
    DEFAULT_SITE_PACKS,
    DEFAULT_SITE_ITEMS,
    DEFAULT_SITE_ANALYSIS_OVERALL,
    DEFAULT_SITE_ANALYSIS_BY_CATEGORY,
    DEFAULT_SITE_VALIDATION_REPORT,
)


def _timestamp_str(ts: Optional[datetime] = None) -> str:
    ts = ts or datetime.now()
    return ts.strftime("%Y-%m-%d_%H%M%S")


def snapshot_site_data(
    site_dir: Path = SITE_DATA_DIR,
    history_root: Path = Path("exports"),
    *,
    timestamp: Optional[datetime] = None,
    extra_files: Optional[Iterable[Path]] = None,
) -> Path:
    """
    Copies JSON exports under site_dir into a new timestamped subdirectory
    under history_root and returns the snapshot path.
    Missing optional files are ignored.
    """
    ensure_dir(history_root)
    snap_dir = history_root / _timestamp_str(timestamp) / "site_data"
    ensure_dir(snap_dir)

    candidates = list(DEFAULT_SNAPSHOT_FILES) + list(extra_files or [])
    for src in candidates:
        src_path = site_dir / src.name if not src.is_absolute() else src
        if src_path.exists():
            shutil.copy2(src_path, snap_dir / src_path.name)
    return snap_dir
