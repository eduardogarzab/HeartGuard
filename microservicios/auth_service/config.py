import os
from pathlib import Path

from dotenv import load_dotenv


def _load_environment() -> None:
    """Carga el .env raíz para compartir configuración."""
    service_dir = Path(__file__).resolve().parent
    root_dir = service_dir.parents[1]
    root_env = root_dir / ".env"
    if root_env.exists():
        load_dotenv(root_env, override=False)


_load_environment()


class Settings:
    FLASK_ENV = os.getenv("FLASK_ENV", os.getenv("ENV", "production"))
    SERVICE_PORT = int(
        os.getenv(
            "AUTH_SERVICE_PORT",
            os.getenv("SERVICE_PORT", os.getenv("HTTP_PORT", "5001")),
        )
    )

    DATABASE_URL = os.getenv("AUTH_DATABASE_URL") or os.getenv("DATABASE_URL")

    PGHOST = os.getenv("PGHOST", "127.0.0.1")
    PGPORT = int(os.getenv("PGPORT", "5432"))
    PGDATABASE = (
        os.getenv("PGDATABASE")
        or os.getenv("DBNAME")
        or os.getenv("AUTH_DBNAME")
        or "heartguard"
    )
    PGUSER = (
        os.getenv("PGUSER")
        or os.getenv("DBUSER")
        or os.getenv("AUTH_DBUSER")
        or "heartguard_app"
    )
    PGPASSWORD = (
        os.getenv("PGPASSWORD")
        or os.getenv("DBPASS")
        or os.getenv("AUTH_DBPASS")
        or "dev_change_me"
    )
    PGSCHEMA = (
        os.getenv("PGSCHEMA")
        or os.getenv("DBSCHEMA")
        or os.getenv("AUTH_DBSCHEMA")
        or "heartguard"
    )
    DB_POOL_MIN = int(os.getenv("AUTH_DB_POOL_MIN", "1"))
    DB_POOL_MAX = int(os.getenv("AUTH_DB_POOL_MAX", "10"))

    JWT_SECRET = os.getenv("AUTH_JWT_SECRET") or os.getenv("JWT_SECRET", "change_me")
    ACCESS_TTL_MIN = int(
        os.getenv("AUTH_ACCESS_TTL_MIN", os.getenv("ACCESS_TTL_MIN", "30"))
    )
    REFRESH_TTL_DAYS = int(
        os.getenv("AUTH_REFRESH_TTL_DAYS", os.getenv("REFRESH_TTL_DAYS", "7"))
    )

    REDIS_URL = os.getenv("AUTH_REDIS_URL") or os.getenv(
        "REDIS_URL", "redis://127.0.0.1:6379/0"
    )
    REDIS_PREFIX = os.getenv("AUTH_REDIS_PREFIX", "authsvc")

    DEFAULT_ORG_ID = os.getenv("DEFAULT_ORG_ID")


settings = Settings()
