import os
from pathlib import Path

from dotenv import load_dotenv


def _load_environment() -> None:
    service_dir = Path(__file__).resolve().parent
    shared_env = service_dir.parent / ".env"
    if shared_env.exists():
        load_dotenv(shared_env, override=False)


_load_environment()


class Settings:
    FLASK_ENV = os.getenv("FLASK_ENV", os.getenv("ENV", "production"))
    SERVICE_PORT = int(
        os.getenv(
            "ORG_SERVICE_PORT",
            os.getenv("SERVICE_PORT", os.getenv("HTTP_PORT", "5002")),
        )
    )

    DATABASE_URL = os.getenv("ORG_DATABASE_URL") or os.getenv("DATABASE_URL")

    PGHOST = (
        os.getenv("PGHOST")
        or os.getenv("POSTGRES_HOST")
        or os.getenv("DBHOST")
        or os.getenv("ORG_DBHOST")
        or "127.0.0.1"
    )
    PGPORT = int(
        os.getenv("PGPORT")
        or os.getenv("POSTGRES_PORT")
        or os.getenv("DBPORT")
        or os.getenv("ORG_DBPORT")
        or "5432"
    )
    PGDATABASE = (
        os.getenv("PGDATABASE")
        or os.getenv("DBNAME")
        or os.getenv("ORG_DBNAME")
        or "heartguard"
    )
    PGUSER = (
        os.getenv("PGUSER")
        or os.getenv("DBUSER")
        or os.getenv("ORG_DBUSER")
        or "heartguard_app"
    )
    PGPASSWORD = (
        os.getenv("PGPASSWORD")
        or os.getenv("DBPASS")
        or os.getenv("ORG_DBPASS")
        or "dev_change_me"
    )
    PGSCHEMA = (
        os.getenv("PGSCHEMA")
        or os.getenv("DBSCHEMA")
        or os.getenv("ORG_DBSCHEMA")
        or "heartguard"
    )
    DB_POOL_MIN = int(os.getenv("ORG_DB_POOL_MIN", "1"))
    DB_POOL_MAX = int(os.getenv("ORG_DB_POOL_MAX", "10"))

    JWT_SECRET = os.getenv("ORG_JWT_SECRET") or os.getenv("JWT_SECRET", "change_me")

    INVITATION_TTL_HOURS = int(
        os.getenv("ORG_INVITE_TTL_HOURS", os.getenv("INVITATION_TTL_HOURS", "72"))
    )
    DEFAULT_INVITATION_ROLE = os.getenv("ORG_INVITE_ROLE", "org_user")


settings = Settings()
