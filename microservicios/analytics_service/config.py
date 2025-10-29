"""Configuración y utilidades de conexión para el servicio de analytics."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def _load_environment() -> None:
    """Carga variables desde los .env compartidos y locales.

    Este método busca primero el archivo compartido ``microservicios/.env`` y
    posteriormente uno local ``analytics_service/.env`` si existiera. Permite
    sobrescribir valores sin clobberear los definidos por el entorno del host.
    """

    service_dir = Path(__file__).resolve().parent
    shared_env = service_dir.parent / ".env"
    local_env = service_dir / ".env"

    for candidate in (shared_env, local_env):
        if candidate.exists():
            load_dotenv(candidate, override=False)


_load_environment()


class Settings:
    """Objeto de configuración centralizado."""

    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    SERVICE_PORT: int = int(os.getenv("ANALYTICS_SERVICE_PORT", os.getenv("SERVICE_PORT", "5010")))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    READ_ONLY_DATABASE_URL: str = os.getenv("READ_ONLY_DATABASE_URL", "")
    AUDIT_DATABASE_URL: str = os.getenv("AUDIT_DATABASE_URL", "")
    ORG_DATABASE_URL: str = os.getenv("ORG_DATABASE_URL", "")

    INGEST_API_KEY: str = os.getenv("INGEST_API_KEY", "")


settings = Settings()


@lru_cache(maxsize=None)
def _build_engine(url: str, *, read_only: bool = False) -> Optional[Engine]:
    """Construye un ``Engine`` de SQLAlchemy a partir de un URL.

    Cuando ``read_only`` es ``True`` se fuerzan banderas que optimizan lecturas.
    Si el URL está vacío devuelve ``None`` para simplificar la lógica de los
    consumidores.
    """

    if not url:
        return None

    connect_args = {}
    if read_only:
        options = ["-c default_transaction_read_only=on"]
        connect_args["options"] = " ".join(options)

    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


# Engine principal del servicio (lectura/escritura).
db_engine: Optional[Engine] = _build_engine(settings.DATABASE_URL)

# Engine opcional de solo lectura para operaciones pesadas.
readonly_engine: Optional[Engine] = _build_engine(
    settings.READ_ONLY_DATABASE_URL or settings.DATABASE_URL, read_only=True
)

# Motores secundarios conectados a bases externas.
audit_db_engine: Optional[Engine] = _build_engine(settings.AUDIT_DATABASE_URL, read_only=True)
org_db_engine: Optional[Engine] = _build_engine(settings.ORG_DATABASE_URL, read_only=True)


__all__ = [
    "settings",
    "db_engine",
    "readonly_engine",
    "audit_db_engine",
    "org_db_engine",
]
