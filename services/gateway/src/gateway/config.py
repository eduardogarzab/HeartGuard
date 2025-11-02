"""Configuración central de la aplicación."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv


@dataclass
class AppConfig:
    """Parámetros configurables para el gateway."""

    debug: bool = False
    testing: bool = False
    secret_key: str = "dev"
    service_timeout: float = 5.0


CONFIG_CLASS = AppConfig


def configure_app(app: Any) -> None:
    """Carga variables de entorno y aplica configuración al objeto Flask."""
    load_dotenv()

    config = CONFIG_CLASS(
        debug=_str_to_bool(os.getenv("FLASK_DEBUG", "0")),
        testing=_str_to_bool(os.getenv("FLASK_TESTING", "0")),
        secret_key=os.getenv("FLASK_SECRET_KEY", "dev"),
        service_timeout=float(os.getenv("GATEWAY_SERVICE_TIMEOUT", "5")),
    )

    app.config.update(
        DEBUG=config.debug,
        TESTING=config.testing,
        SECRET_KEY=config.secret_key,
        GATEWAY_SERVICE_TIMEOUT=config.service_timeout,
    )


def _str_to_bool(value: str) -> bool:
    return value.lower() in {"1", "true", "t", "yes", "on"}
