"""Runtime configuration helpers for the Tkinter HeartGuard client."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


DEFAULT_GATEWAY_URL = "http://127.0.0.1:8080"
SESSION_DIR = Path.home() / ".heartguard"
SESSION_FILE = SESSION_DIR / "session.dat"
KEY_FILE = SESSION_DIR / "session.key"
FONT_FAMILY = "Segoe UI"
BACKGROUND_COLOR = "#f7f9fb"
PRIMARY_COLOR = "#0078D7"
ACCENT_COLOR = "#28a745"
TEXT_COLOR = "#1f2933"
LIGHT_TEXT_COLOR = "#4a5568"
CARD_BACKGROUND = "#ffffff"


@dataclass(frozen=True)
class AppConfig:
    gateway_url: str = os.getenv("HEARTGUARD_GATEWAY_URL", DEFAULT_GATEWAY_URL)
    session_file: Path = SESSION_FILE
    session_key_file: Path = KEY_FILE
    font_family: str = os.getenv("HEARTGUARD_FONT", FONT_FAMILY)


APP_CONFIG = AppConfig()
