"""Auto-run the pipeline and create a git commit if exports changed."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Sequence

from ..settings import SITE_DATA_DIR


def _run_cmd(args: Sequence[str]) -> int:
    result = subprocess.run(list(args))
    return result.returncode


def _run_pipeline_cmd(
    raw_dir: Path,
    site_dir: Path,
    history_root: Optional[Path],
    extra_run_args: Sequence[str] | None = None,
    game_key: str | None = None,
) -> int:
    cmd = [
        "python",
        "-m",
        "wos_pack_value.cli",
        "run",
        "--raw-dir",
        str(raw_dir),
        "--site-dir",
        str(site_dir),
        "--with-analysis",
    ]
    if history_root:
        cmd += ["--history-root", str(history_root)]
    if game_key:
        cmd += ["--game", game_key]
    if extra_run_args:
        cmd += list(extra_run_args)
    return _run_cmd(cmd)


def _git_status() -> list[str]:
    proc = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git status failed")
    return proc.stdout.splitlines()


def _git_add(paths: Iterable[Path]) -> int:
    cmd = ["git", "add"] + [str(p) for p in paths]
    return _run_cmd(cmd)


def _git_commit(message: str) -> int:
    cmd = ["git", "commit", "-m", message]
    return _run_cmd(cmd)


def _filter_changed(status_lines: list[str], watch_paths: Sequence[Path]) -> list[str]:
    watch = [p.as_posix().rstrip("/") for p in watch_paths]
    changed: list[str] = []
    for line in status_lines:
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if any(path == w or path.startswith(f"{w}/") for w in watch):
            changed.append(path)
    return changed


def auto_update_and_commit(
    raw_dir: Path,
    site_dir: Path = SITE_DATA_DIR,
    *,
    history_root: Optional[Path] = None,
    extra_run_args: Optional[Sequence[str]] = None,
    dry_run: bool = False,
    commit_message: Optional[str] = None,
    paths_to_watch: Optional[Sequence[Path]] = None,
    game_key: str | None = None,
) -> int:
    """Run pipeline, detect export changes, and create a git commit if needed."""
    run_code = _run_pipeline_cmd(
        raw_dir=raw_dir, site_dir=site_dir, history_root=history_root, extra_run_args=extra_run_args, game_key=game_key
    )
    if run_code != 0:
        print("Pipeline run failed; aborting auto-update.")
        return run_code

    watch_paths = list(paths_to_watch) if paths_to_watch else [site_dir]
    if history_root:
        watch_paths.append(history_root)

    try:
        status_lines = _git_status()
    except Exception as exc:  # pragma: no cover - git environment issue
        print(f"Git status failed: {exc}")
        return 1

    changed = _filter_changed(status_lines, watch_paths)
    if not changed:
        print("No changes detected in watched paths; nothing to commit.")
        return 0

    if dry_run:
        print("Dry run: detected changes in:")
        for p in changed:
            print(f"  {p}")
        print("Would stage watched paths and create a commit.")
        return 0

    add_code = _git_add(watch_paths)
    if add_code != 0:
        print("git add failed.")
        return add_code

    msg = commit_message or f"Update pack data {datetime.now().date().isoformat()}"
    commit_code = _git_commit(msg)
    if commit_code != 0:
        print("git commit failed.")
        return commit_code

    print(f"Committed changes with message: {msg}")
    return 0


__all__ = ["auto_update_and_commit"]
