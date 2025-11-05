"""Analytics queries for organization dashboards."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .. import db


class AnalyticsRepository:
    """Provide aggregated metrics scoped to an organization."""

    def patient_risk_breakdown(self, org_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
                COALESCE(rl.code, 'unknown') AS code,
                COALESCE(rl.label, 'Sin clasificar') AS label,
                COUNT(*) AS count
            FROM patients p
            LEFT JOIN risk_levels rl ON rl.id = p.risk_level_id
            WHERE p.org_id = %s
            GROUP BY rl.code, rl.label
            ORDER BY COUNT(*) DESC
        """
        return db.fetch_all(query, (org_id,))

    def device_status_breakdown(self, org_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
                CASE WHEN d.active THEN 'active' ELSE 'inactive' END AS code,
                CASE WHEN d.active THEN 'Activos' ELSE 'Inactivos' END AS label,
                COUNT(*) AS count
            FROM devices d
            WHERE d.org_id = %s
            GROUP BY d.active
            ORDER BY code DESC
        """
        return db.fetch_all(query, (org_id,))

    def alert_outcome_breakdown(self, org_id: str, *, days: int = 30) -> list[dict[str, Any]]:
        since = _since(days)
        query = """
            SELECT
                COALESCE(ar.outcome, 'unknown') AS code,
                COALESCE(ar.outcome, 'Sin clasificación') AS label,
                COUNT(*) AS count
            FROM alert_resolution ar
            JOIN alerts a ON a.id = ar.alert_id
            JOIN patients p ON p.id = a.patient_id
            WHERE p.org_id = %(org_id)s
              AND ar.resolved_at >= %(since)s
            GROUP BY ar.outcome
            ORDER BY count DESC
        """
        params = {"org_id": org_id, "since": since}
        return db.fetch_all(query, params)

    def alert_response_stats(self, org_id: str, *, days: int = 30) -> dict[str, Any]:
        since = _since(days)
        query = """
            WITH ack_times AS (
                SELECT
                    a.id,
                    EXTRACT(EPOCH FROM ack.ack_at - a.created_at) AS ack_seconds
                FROM alerts a
                JOIN patients p ON p.id = a.patient_id
                JOIN alert_ack ack ON ack.alert_id = a.id
                WHERE p.org_id = %(org_id)s
                  AND a.created_at >= %(since)s
                  AND ack.ack_at > a.created_at
            ),
            resolve_times AS (
                SELECT
                    a.id,
                    EXTRACT(EPOCH FROM res.resolved_at - a.created_at) AS resolve_seconds
                FROM alerts a
                JOIN patients p ON p.id = a.patient_id
                JOIN alert_resolution res ON res.alert_id = a.id
                WHERE p.org_id = %(org_id)s
                  AND a.created_at >= %(since)s
                  AND res.resolved_at > a.created_at
            )
            SELECT
                COALESCE(AVG(ack_seconds), 0) AS avg_ack_seconds,
                COALESCE(AVG(resolve_seconds), 0) AS avg_resolve_seconds
            FROM ack_times
            FULL OUTER JOIN resolve_times ON ack_times.id = resolve_times.id
        """
        params = {"org_id": org_id, "since": since}
        stats = db.fetch_one(query, params) or {}
        return {
            "avg_ack_seconds": float(stats.get("avg_ack_seconds") or 0.0),
            "avg_resolve_seconds": float(stats.get("avg_resolve_seconds") or 0.0),
        }

    def alerts_created_count(self, org_id: str, *, days: int = 30) -> int:
        since = _since(days)
        query = """
            SELECT COUNT(*) AS count
            FROM alerts a
            JOIN patients p ON p.id = a.patient_id
            WHERE p.org_id = %(org_id)s
              AND a.created_at >= %(since)s
        """
        params = {"org_id": org_id, "since": since}
        result = db.fetch_one(query, params) or {}
        return int(result.get("count") or 0)

    def invitation_status_breakdown(self, org_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT status AS code, status AS label, COUNT(*) AS count
            FROM (
                SELECT
                    CASE
                        WHEN i.revoked_at IS NOT NULL THEN 'revoked'
                        WHEN i.used_at IS NOT NULL THEN 'used'
                        WHEN i.expires_at <= NOW() THEN 'expired'
                        ELSE 'pending'
                    END AS status
                FROM org_invitations i
                WHERE i.org_id = %s
            ) AS derived
            GROUP BY status
            ORDER BY count DESC
        """
        return db.fetch_all(query, (org_id,))


def _since(days: int) -> datetime:
    days = max(days, 1)
    base = datetime.now(timezone.utc)
    return base - timedelta(days=days)
