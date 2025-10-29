"""Funciones de acceso a datos para el servicio de analytics."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config import audit_db_engine, db_engine
from models import ServiceHealth


class RepositoryError(RuntimeError):
    """Error de infraestructura al interactuar con la base de datos."""


def log_heartbeat(service_name: str, status: str, *, details: Optional[Dict[str, Any]] = None) -> None:
    """Registra o actualiza el último ``heartbeat`` de un servicio."""

    if db_engine is None:
        raise RepositoryError("Database engine is not configured")

    payload = {
        "service_name": service_name,
        "status": status,
        "last_heartbeat": datetime.utcnow(),
        "details": details or {},
    }

    statement = insert(ServiceHealth).values(**payload)
    update_clause = {
        "status": statement.excluded.status,
        "last_heartbeat": statement.excluded.last_heartbeat,
        "details": statement.excluded.details,
    }

    try:
        with Session(db_engine) as session:
            session.execute(
                statement.on_conflict_do_update(
                    index_elements=[ServiceHealth.service_name], set_=update_clause
                )
            )
            session.commit()
    except SQLAlchemyError as exc:
        raise RepositoryError("Failed to upsert heartbeat") from exc


def get_overview_metrics(*, org_id: Optional[int], include_all: bool) -> Dict[str, Any]:
    """Obtiene métricas agregadas desde la base de auditoría."""

    if audit_db_engine is None:
        raise RepositoryError("Audit database engine is not configured")

    filter_clause = ""
    params: Dict[str, Any] = {}
    if not include_all:
        filter_clause = "WHERE filtered.org_id = :org_id"
        params["org_id"] = org_id

    query = text(
        """
        WITH filtered AS (
            SELECT
                l.ts,
                COALESCE(NULLIF(l.details->>'org_id', ''), '0')::bigint AS org_id,
                l.action,
                l.entity,
                l.user_id,
                l.details
            FROM audit_logs AS l
        ),
        scoped AS (
            SELECT * FROM filtered
            {filter_clause}
        ),
        last_30_days AS (
            SELECT * FROM scoped WHERE ts >= NOW() - INTERVAL '30 days'
        ),
        daily_totals AS (
            SELECT date_trunc('day', ts) AS day, action, COUNT(*) AS total
            FROM last_30_days
            GROUP BY day, action
        ),
        entity_totals AS (
            SELECT entity, COUNT(*) AS total FROM scoped WHERE entity IS NOT NULL GROUP BY entity
        ),
        user_totals AS (
            SELECT COUNT(DISTINCT user_id) AS total FROM last_30_days WHERE user_id IS NOT NULL
        )
        SELECT
            COALESCE((SELECT SUM(total) FROM daily_totals), 0) AS total_events,
            COALESCE((SELECT total FROM user_totals), 0) AS active_users_30d,
            COALESCE(json_agg(json_build_object('day', day, 'action', action, 'total', total)
                              ORDER BY day DESC, action), '[]'::json) AS timeline,
            COALESCE(json_object_agg(entity, total), '{}'::json) AS entity_counts
        FROM entity_totals
        RIGHT JOIN (SELECT 1) AS singleton ON TRUE;
        """.format(filter_clause=filter_clause)
    )

    try:
        with audit_db_engine.connect() as conn:
            result = conn.execute(query, params).mappings().first()
            if not result:
                return {
                    "total_events": 0,
                    "active_users_30d": 0,
                    "timeline": [],
                    "entity_counts": {},
                }

            timeline = result["timeline"] or []
            if isinstance(timeline, str):
                timeline = json.loads(timeline)

            entity_counts = result["entity_counts"] or {}
            if isinstance(entity_counts, str):
                entity_counts = json.loads(entity_counts)

            return {
                "total_events": result["total_events"],
                "active_users_30d": result["active_users_30d"],
                "timeline": timeline,
                "entity_counts": entity_counts,
            }
    except SQLAlchemyError as exc:
        raise RepositoryError("Failed to fetch overview metrics") from exc
