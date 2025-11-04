"""Configuration loader for Admin Service."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from dotenv import load_dotenv


@dataclass
class AppConfig:
    """Runtime configuration values."""

    debug: bool
    database_url: str
    auth_service_url: str
    service_timeout: float


class Config:
    """Singleton style config holder."""

    def __init__(self) -> None:
        load_dotenv()
        self._config = AppConfig(
            debug=_to_bool(os.getenv("ADMIN_DEBUG", "0")),
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql://heartguard_app:dev_change_me@localhost:5432/heartguard",
            ),
            auth_service_url=os.getenv("AUTH_SERVICE_URL", "http://localhost:5001"),
            service_timeout=float(os.getenv("ADMIN_SERVICE_TIMEOUT", "5")),
        )

    @property
    def values(self) -> AppConfig:
        return self._config


def configure_app(app: Any) -> AppConfig:
    """Attach and return the application config."""
    cfg = Config().values
    app.config.update(
        DEBUG=cfg.debug,
        DATABASE_URL=cfg.database_url,
        AUTH_SERVICE_URL=cfg.auth_service_url,
        ADMIN_SERVICE_TIMEOUT=cfg.service_timeout,
    )
    return cfg


def _to_bool(value: str) -> bool:
    return value.lower() in {"1", "true", "t", "yes", "on"}
