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
        os.getenv("MEDIA_SERVICE_PORT", os.getenv("SERVICE_PORT", os.getenv("HTTP_PORT", "5006")))
    )

    DATABASE_URL = os.getenv("MEDIA_DATABASE_URL") or os.getenv("DATABASE_URL")

    PGHOST = (
        os.getenv("MEDIA_PGHOST")
        or os.getenv("PGHOST")
        or os.getenv("POSTGRES_HOST")
        or os.getenv("DBHOST")
        or "127.0.0.1"
    )
    PGPORT = int(
        os.getenv("MEDIA_PGPORT")
        or os.getenv("PGPORT")
        or os.getenv("POSTGRES_PORT")
        or os.getenv("DBPORT")
        or "5432"
    )
    PGDATABASE = (
        os.getenv("MEDIA_PGDATABASE")
        or os.getenv("PGDATABASE")
        or os.getenv("DBNAME")
        or "heartguard"
    )
    PGUSER = (
        os.getenv("MEDIA_PGUSER")
        or os.getenv("PGUSER")
        or os.getenv("DBUSER")
        or "heartguard_app"
    )
    PGPASSWORD = (
        os.getenv("MEDIA_PGPASSWORD")
        or os.getenv("PGPASSWORD")
        or os.getenv("DBPASS")
        or "dev_change_me"
    )
    PGSCHEMA = (
        os.getenv("MEDIA_PGSCHEMA")
        or os.getenv("PGSCHEMA")
        or os.getenv("DBSCHEMA")
        or "heartguard"
    )
    DB_POOL_MIN = int(os.getenv("MEDIA_DB_POOL_MIN", "1"))
    DB_POOL_MAX = int(os.getenv("MEDIA_DB_POOL_MAX", "10"))

    JWT_SECRET = os.getenv("MEDIA_JWT_SECRET") or os.getenv("JWT_SECRET", "change_me")
    JWT_ALGORITHM = os.getenv("MEDIA_JWT_ALGORITHM", os.getenv("JWT_ALGORITHM", "HS256"))

    GCS_BUCKET = os.getenv("MEDIA_GCS_BUCKET", "heartguard-system")
    SIGNED_URL_TTL_SECONDS = int(os.getenv("MEDIA_SIGNED_URL_TTL", "600"))


settings = Settings()
