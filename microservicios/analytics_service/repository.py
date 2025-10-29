"""Data access layer for the analytics service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional

from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from config import get_audit_session, get_db_session
from models import ServiceHealth


class RepositoryError(RuntimeError):
    """Raised when repository operations fail."""


def _coerce_metadata(value: Any) -> Dict[str, Any]:
    """Normalize metadata returned from the database into a dictionary."""

    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, (bytes, bytearray)):
        try:
            return json.loads(value.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}


def _serialize_dt(value: Any) -> Optional[str]:
    """Return a safe ISO formatted string for datetime-like values."""

    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat()
    return str(value)


def log_heartbeat(service_name: str, status: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Insert or update the heartbeat entry for a given service."""

    metadata = metadata or {}
    payload = {
        "service_name": service_name,
        "status": status,
        "details": metadata,
        "last_heartbeat": datetime.now(timezone.utc),
    }

    with get_db_session() as session:
        insert_stmt = insert(ServiceHealth).values(payload)
        stmt = insert_stmt.on_conflict_do_update(
            index_elements=[ServiceHealth.service_name],
            set_={
                "status": insert_stmt.excluded.status,
                "details": insert_stmt.excluded.details,
                "last_heartbeat": func.now(),
            },
        ).returning(
            ServiceHealth.service_name,
            ServiceHealth.status,
            ServiceHealth.last_heartbeat,
            ServiceHealth.payload.label("metadata"),
        )

        try:
            result = session.execute(stmt)
            row = result.mappings().one()
        except SQLAlchemyError as exc:
            raise RepositoryError("Failed to persist heartbeat") from exc

        return {
            "service_name": row["service_name"],
            "status": row["status"],
            "last_heartbeat": _serialize_dt(row.get("last_heartbeat")),
            "metadata": _coerce_metadata(row.get("metadata")),
        }


def get_overview_metrics(org_id: Optional[str], is_superadmin: bool) -> Dict[str, Any]:
    """Fetch summary metrics from the audit service respecting org scoping."""

    query = [
        "SELECT",
        "    COUNT(*) FILTER (WHERE action = 'login') AS login_events",
        "  , COUNT(*) FILTER (WHERE action = 'data_export') AS data_exports",
        "  , COUNT(DISTINCT user_id) AS active_users",
        "  , MAX(created_at) AS last_event_at",
        "FROM audit_logs",
    ]

    params: Dict[str, Any] = {}
    if not is_superadmin:
        if not org_id:
            raise RepositoryError("Organization context is required for non super-admin users")
        query.append("WHERE org_id = :org_id")
        params["org_id"] = org_id

    sql = text("\n".join(query))

    try:
        with get_audit_session() as session:
            row = session.execute(sql, params).mappings().one()
    except SQLAlchemyError as exc:
        raise RepositoryError("Failed to load overview metrics") from exc

    return {
        "login_events": int(row.get("login_events") or 0),
        "data_exports": int(row.get("data_exports") or 0),
        "active_users": int(row.get("active_users") or 0),
        "last_event_at": _serialize_dt(row.get("last_event_at")),
        "scope": "all" if is_superadmin and not org_id else org_id,
    }

