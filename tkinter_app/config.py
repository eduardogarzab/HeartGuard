"""Configuración global para la app Tkinter de HeartGuard."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiSettings:
    """Valores de configuración para el cliente HTTP."""

    base_url: str = os.getenv("HEARTGUARD_GATEWAY_URL", "http://136.115.53.140:8080")
    connect_timeout: float = float(os.getenv("HEARTGUARD_CONNECT_TIMEOUT", "10"))
    read_timeout: float = float(os.getenv("HEARTGUARD_READ_TIMEOUT", "30"))
    write_timeout: float = float(os.getenv("HEARTGUARD_WRITE_TIMEOUT", "10"))


API_SETTINGS = ApiSettings()


class Colors:
    """Paleta reutilizable para la interfaz."""

    PRIMARY = "#2196F3"
    PRIMARY_DARK = "#1976D2"
    ACCENT = "#00BCD4"
    SUCCESS = "#2ECC71"
    WARNING = "#FFB300"
    DANGER = "#E74C3C"
    BACKGROUND = "#F0F4F9"
    SURFACE = "#FFFFFF"
    TEXT_PRIMARY = "#233446"
    TEXT_SECONDARY = "#68788A"
    BORDER = "#E1E7EE"


class Fonts:
    """Fuentes comunes para mantener consistencia."""

    TITLE = ("Segoe UI", 20, "bold")
    SUBTITLE = ("Segoe UI", 12, "normal")
    BODY = ("Segoe UI", 11, "normal")
    BODY_BOLD = ("Segoe UI", 11, "bold")
    CAPTION = ("Segoe UI", 9, "normal")
