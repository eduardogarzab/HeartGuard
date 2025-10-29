"""Configuration and database initialization for the analytics service."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Load environment variables from the service specific .env file if present
_SERVICE_DIR = Path(__file__).resolve().parent
for candidate in (_SERVICE_DIR / ".env", _SERVICE_DIR.parent / ".env"):
    if candidate.exists():
        load_dotenv(candidate, override=False)


class Settings:
    """Typed access to configuration options."""

    FLASK_ENV: str = os.getenv("FLASK_ENV", os.getenv("ENV", "production"))
    SERVICE_PORT: int = int(os.getenv("ANALYTICS_SERVICE_PORT", os.getenv("SERVICE_PORT", "5010")))

    DATABASE_URL: str = os.getenv("ANALYTICS_DATABASE_URL") or os.getenv("DATABASE_URL", "postgresql://heartguard_app:dev_change_me@localhost:5432/heartguard")
    AUDIT_DATABASE_URL: Optional[str] = os.getenv("ANALYTICS_AUDIT_DATABASE_URL") or os.getenv("AUDIT_DATABASE_URL")
    ORG_DATABASE_URL: Optional[str] = os.getenv("ANALYTICS_ORG_DATABASE_URL") or os.getenv("ORG_DATABASE_URL")

    INTERNAL_API_KEY: str = os.getenv("ANALYTICS_INTERNAL_API_KEY", os.getenv("INTERNAL_API_KEY", ""))


settings = Settings()


def _build_engine(url: Optional[str]) -> Optional[Engine]:
    if not url:
        return None
    return create_engine(url, pool_pre_ping=True, future=True)


def _build_session_factory(engine: Optional[Engine]) -> Optional[sessionmaker]:
    if engine is None:
        return None
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


engine: Engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal: sessionmaker = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

audit_engine: Optional[Engine] = _build_engine(settings.AUDIT_DATABASE_URL)
audit_session_factory: Optional[sessionmaker] = _build_session_factory(audit_engine)

org_engine: Optional[Engine] = _build_engine(settings.ORG_DATABASE_URL)
org_session_factory: Optional[sessionmaker] = _build_session_factory(org_engine)


@contextmanager
def get_db_session() -> Iterator[Session]:
    """Context manager that yields a transactional session against the local database."""

    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_audit_session() -> Iterator[Session]:
    """Yield a read-only session for the audit database if configured."""

    if audit_session_factory is None:
        raise RuntimeError("AUDIT_DATABASE_URL is not configured")

    session: Session = audit_session_factory()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def get_org_session() -> Iterator[Session]:
    """Yield a read-only session for the organization service database if configured."""

    if org_session_factory is None:
        raise RuntimeError("ORG_DATABASE_URL is not configured")

    session: Session = org_session_factory()
    try:
        yield session
    finally:
        session.close()

