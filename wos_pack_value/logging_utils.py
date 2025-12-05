"""Logging setup for the toolkit."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .settings import LOG_DIR
from .utils import ensure_dir


def configure_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None:
    """Configure root logging with console and rotating file handlers."""
    ensure_dir(LOG_DIR)
    log_path = log_file or (LOG_DIR / "run.log")
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    handlers = []

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)

    logging.basicConfig(level=level, handlers=handlers, force=True)
