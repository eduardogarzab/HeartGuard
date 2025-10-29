"""Database models for the analytics service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import engine


class Base(DeclarativeBase):
    """Declarative base used by all SQLAlchemy models in the service."""


class ServiceHealth(Base):
    """Store the last heartbeat and status for each internal service."""

    __tablename__ = "service_health"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ok")
    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    payload: Mapped[Dict[str, Any]] = mapped_column("details", JSONB, nullable=False, default=dict)

    def touch(self, status: str, metadata: Dict[str, Any]) -> None:
        """Update this record with the latest status and metadata payload."""

        self.status = status
        self.last_heartbeat = datetime.now(timezone.utc)
        self.payload = metadata


# Create the tables on module import to simplify local development environments.
Base.metadata.create_all(bind=engine)

# Additional cross-service engines can be registered in :mod:`config` by creating
# read-only engine factories, for example::
#
#     audit_db_engine = create_engine(settings.AUDIT_DATABASE_URL, future=True)
#
# Session factories exposed in :mod:`config` (``audit_session_factory`` and
# ``org_session_factory``) provide dedicated connections for running analytical
# queries against the audit and organization services without mutating their
# state.
