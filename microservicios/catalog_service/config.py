"""Application configuration for the catalog service."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name, default)
    if value is None:
        return default
    return value


@dataclass
class Config:
    """Base configuration loaded from environment variables."""

    FLASK_ENV: str = _get_env("FLASK_ENV", "production")
    DATABASE_URL: str = _get_env("DATABASE_URL", "sqlite:///catalog.db")
    JWT_SECRET: str = _get_env("JWT_SECRET", "change-me")
    AUDIT_SERVICE_URL: Optional[str] = _get_env("AUDIT_SERVICE_URL")
    ANALYTICS_SERVICE_URL: Optional[str] = _get_env("ANALYTICS_SERVICE_URL")


CONFIG = Config()
