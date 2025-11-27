"""Configuración de Auth Service."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv


@dataclass
class AppConfig:
    debug: bool = False
    testing: bool = False
    secret_key: str = "dev"
    database_url: str = ""
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_minutes: int = 15
    jwt_refresh_minutes: int = 60 * 24 * 7
    bcrypt_rounds: int = 12
    log_level: str = "INFO"
    skip_db_init: bool = False


CONFIG_CLASS = AppConfig


def configure_app(app: Any) -> None:
    """Carga configuración basada en variables de entorno."""
    load_dotenv()

    config = CONFIG_CLASS(
        debug=_str_to_bool(os.getenv("FLASK_DEBUG", "0")),
        testing=_str_to_bool(os.getenv("FLASK_TESTING", "0")),
        secret_key=os.getenv("FLASK_SECRET_KEY", "dev"),
        database_url=os.getenv("DATABASE_URL", ""),
        jwt_secret=os.getenv("JWT_SECRET", "change-me"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_access_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MIN", "15")),
        jwt_refresh_minutes=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_MIN", "10080")),
        bcrypt_rounds=int(os.getenv("BCRYPT_ROUNDS", "12")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    skip_db_init=_str_to_bool(os.getenv("SKIP_DB_INIT", "0")),
    )

    if not config.database_url:
        raise RuntimeError("DATABASE_URL es requerido para el servicio Auth")

    app.config.update(
        DEBUG=config.debug,
        TESTING=config.testing,
        SECRET_KEY=config.secret_key,
        DATABASE_URL=config.database_url,
        JWT_SECRET=config.jwt_secret,
        JWT_ALGORITHM=config.jwt_algorithm,
        JWT_ACCESS_TOKEN_EXPIRES_MIN=config.jwt_access_minutes,
        JWT_REFRESH_TOKEN_EXPIRES_MIN=config.jwt_refresh_minutes,
        BCRYPT_ROUNDS=config.bcrypt_rounds,
        LOG_LEVEL=config.log_level,
    SKIP_DB_INIT=config.skip_db_init,
    )


def _str_to_bool(value: str) -> bool:
    return value.lower() in {"1", "true", "t", "yes", "on"}
