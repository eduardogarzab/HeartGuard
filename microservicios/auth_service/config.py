import os
from pathlib import Path

from dotenv import load_dotenv


def _load_environment() -> None:
    """Carga el .env central ubicado en microservicios/."""
    service_dir = Path(__file__).resolve().parent
    shared_env = service_dir.parent / ".env"
    if shared_env.exists():
        load_dotenv(shared_env, override=False)


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

    PGHOST = (
        os.getenv("PGHOST")
        or os.getenv("POSTGRES_HOST")
        or os.getenv("DBHOST")
        or os.getenv("AUTH_DBHOST")
        or "127.0.0.1"
    )
    PGPORT = int(
        os.getenv("PGPORT")
        or os.getenv("POSTGRES_PORT")
        or os.getenv("DBPORT")
        or os.getenv("AUTH_DBPORT")
        or "5432"
    )
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

    _redis_url = os.getenv("AUTH_REDIS_URL") or os.getenv("REDIS_URL")
    if not _redis_url:
        redis_host = (
            os.getenv("REDIS_HOST")
            or os.getenv("AUTH_REDIS_HOST")
            or os.getenv("POSTGRES_HOST")
            or "127.0.0.1"
        )
        redis_port = (
            os.getenv("REDIS_PORT")
            or os.getenv("AUTH_REDIS_PORT")
            or os.getenv("POSTGRES_REDIS_PORT")
            or os.getenv("POSTGRES_PORT")
            or "6379"
        )
        redis_db = os.getenv("REDIS_DB") or os.getenv("AUTH_REDIS_DB") or "0"
        _redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
    REDIS_URL = _redis_url
    REDIS_PREFIX = os.getenv("AUTH_REDIS_PREFIX", "authsvc")

    DEFAULT_ORG_ID = os.getenv("DEFAULT_ORG_ID")


settings = Settings()
