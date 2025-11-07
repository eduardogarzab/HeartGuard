"""Logging helpers for the Tkinter application."""
from __future__ import annotations

import logging
import os
from pathlib import Path


def configure_logging(level: int | None = None) -> None:
    """Configure application wide logging.

    Parameters
    ----------
    level:
        Optional logging level. Defaults to ``INFO``. Can be overridden by the
        ``HEARTGUARD_LOG_LEVEL`` environment variable.
    """
    log_level = level or getattr(logging, os.getenv("HEARTGUARD_LOG_LEVEL", "INFO"))

    log_dir = Path.home() / ".heartguard"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "desktop-app.log"

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
