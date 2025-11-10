"""Configuración del Media Service."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Tuple
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


def _split_origin(origin: str | None) -> tuple[str | None, str | None]:
    if not origin:
        return None, None
    parsed = urlparse(origin)
    host = parsed.netloc
    if not host:
        return None, None
    parts = host.split(".")
    if len(parts) < 3:
        return parts[0] if parts else None, None
    bucket = parts[0]
    region = parts[1]
    return bucket, region


def _parse_allowed_content_types(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ("image/jpeg", "image/png", "image/webp")
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return tuple(items) if items else ("image/jpeg", "image/png", "image/webp")


@dataclass
class BaseConfig:
    """Valores base cargados desde el entorno."""

    DEBUG: bool = os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes", "on"}
    TESTING: bool = os.getenv("FLASK_TESTING", "0").lower() in {"1", "true", "yes", "on"}
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 5005))
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    MEDIA_MAX_FILE_MB: int = int(os.getenv("MEDIA_MAX_FILE_MB", 5))
    MEDIA_ALLOWED_CONTENT_TYPES: Tuple[str, ...] = _parse_allowed_content_types(os.getenv("MEDIA_ALLOWED_CONTENT_TYPES"))
    MEDIA_NAMESPACE_USERS: str = os.getenv("MEDIA_NAMESPACE_USERS", "users")
    MEDIA_NAMESPACE_PATIENTS: str = os.getenv("MEDIA_NAMESPACE_PATIENTS", "patients")
    MEDIA_DEFAULT_ACL: str = os.getenv("MEDIA_DEFAULT_ACL", "public-read")

    SPACES_ACCESS_KEY: str | None = os.getenv("ID")
    SPACES_SECRET_KEY: str | None = os.getenv("KEY")
    SPACES_ORIGIN_ENDPOINT: str | None = os.getenv("ORIGIN_ENDPOINT")
    SPACES_BUCKET: str | None = os.getenv("SPACES_BUCKET")
    SPACES_REGION: str | None = os.getenv("SPACES_REGION")
    SPACES_ENDPOINT: str | None = os.getenv("SPACES_ENDPOINT")
    MEDIA_CDN_BASE_URL: str | None = os.getenv("MEDIA_CDN_BASE_URL")
    
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    def __post_init__(self) -> None:
        if not self.SPACES_ORIGIN_ENDPOINT:
            raise RuntimeError("ORIGIN_ENDPOINT es requerido para inicializar el Media Service")

        bucket, region = _split_origin(self.SPACES_ORIGIN_ENDPOINT)
        if not self.SPACES_BUCKET:
            if not bucket:
                raise RuntimeError("No fue posible inferir SPACES_BUCKET a partir de ORIGIN_ENDPOINT")
            self.SPACES_BUCKET = bucket
        if not self.SPACES_REGION:
            if not region:
                raise RuntimeError("No fue posible inferir SPACES_REGION a partir de ORIGIN_ENDPOINT")
            self.SPACES_REGION = region
        if not self.SPACES_ENDPOINT and self.SPACES_REGION:
            self.SPACES_ENDPOINT = f"https://{self.SPACES_REGION}.digitaloceanspaces.com"
        if not self.MEDIA_CDN_BASE_URL:
            self.MEDIA_CDN_BASE_URL = self.SPACES_ORIGIN_ENDPOINT.rstrip("/")
        else:
            self.MEDIA_CDN_BASE_URL = self.MEDIA_CDN_BASE_URL.rstrip("/")

        self.MEDIA_MAX_FILE_BYTES = self.MEDIA_MAX_FILE_MB * 1024 * 1024

        missing = []
        if not self.SPACES_ACCESS_KEY:
            missing.append("ID")
        if not self.SPACES_SECRET_KEY:
            missing.append("KEY")
        if not self.DATABASE_URL:
            missing.append("DATABASE_URL")
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"Variables de entorno faltantes: {joined}")


class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True


class ProductionConfig(BaseConfig):
    DEBUG: bool = False


config_registry = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config() -> BaseConfig:
    env = os.getenv("FLASK_ENV", "development")
    config_cls = config_registry.get(env, config_registry["default"])
    return config_cls()
