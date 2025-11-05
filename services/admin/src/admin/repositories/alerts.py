"""Repository helpers for alert operations."""
from __future__ import annotations

from typing import Any

from .. import db


class AlertsRepository:
    """Expose alert queries filtered by organization."""

    def list_alerts(
        self,
        org_id: str,
        *,
        status_code: str | None = None,
        level_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
        from_ts: str | None = None,
        to_ts: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["p.org_id = %(org_id)s"]
        params: dict[str, Any] = {
            "org_id": org_id,
            "limit": max(1, min(limit, 200)),
            "offset": max(0, offset),
        }
        if status_code:
            clauses.append("st.code = %(status)s")
            params["status"] = status_code
        if level_code:
            clauses.append("al.code = %(level)s")
            params["level"] = level_code
        if from_ts:
            clauses.append("a.created_at >= %(from)s")
            params["from"] = from_ts
        if to_ts:
            clauses.append("a.created_at <= %(to)s")
            params["to"] = to_ts
        where = " AND ".join(clauses)
        query = f"""
            SELECT
                a.id,
                a.created_at,
                a.description,
                p.id AS patient_id,
                p.person_name AS patient_name,
                at.code AS type_code,
                at.description AS type_description,
                al.code AS level_code,
                al.label AS level_label,
                st.code AS status_code,
                st.description AS status_description
            FROM alerts a
            JOIN patients p ON p.id = a.patient_id
            JOIN alert_types at ON at.id = a.type_id
            JOIN alert_levels al ON al.id = a.alert_level_id
            JOIN alert_status st ON st.id = a.status_id
            WHERE {where}
            ORDER BY a.created_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        return db.fetch_all(query, params)

    def get_alert(self, org_id: str, alert_id: str) -> dict[str, Any] | None:
        query = """
            SELECT
                a.id,
                a.created_at,
                a.description,
                a.type_id,
                a.created_by_model_id,
                a.source_inference_id,
                ST_AsText(a.location)::text AS location_wkt,
                at.code AS type_code,
                at.description AS type_description,
                a.alert_level_id,
                al.code AS level_code,
                al.label AS level_label,
                a.status_id,
                st.code AS status_code,
                st.description AS status_description,
                p.id AS patient_id,
                p.person_name AS patient_name,
                p.email AS patient_email,
                p.org_id
            FROM alerts a
            JOIN patients p ON p.id = a.patient_id
            JOIN alert_types at ON at.id = a.type_id
            JOIN alert_levels al ON al.id = a.alert_level_id
            JOIN alert_status st ON st.id = a.status_id
            WHERE a.id = %s AND p.org_id = %s
        """
        return db.fetch_one(query, (alert_id, org_id))

    def list_acks(self, alert_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
                ack.id,
                ack.alert_id,
                ack.ack_at,
                ack.note,
                ack.ack_by_user_id,
                u.name AS ack_by_name
            FROM alert_ack ack
            LEFT JOIN users u ON u.id = ack.ack_by_user_id
            WHERE ack.alert_id = %s
            ORDER BY ack.ack_at DESC
        """
        return db.fetch_all(query, (alert_id,))

    def list_resolutions(self, alert_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
                res.id,
                res.alert_id,
                res.resolved_at,
                res.note,
                res.outcome,
                res.resolved_by_user_id,
                u.name AS resolved_by_name
            FROM alert_resolution res
            LEFT JOIN users u ON u.id = res.resolved_by_user_id
            WHERE res.alert_id = %s
            ORDER BY res.resolved_at DESC
        """
        return db.fetch_all(query, (alert_id,))

    def acknowledge(self, alert_id: str, user_id: str | None, note: str | None) -> dict[str, Any] | None:
        query = """
            INSERT INTO alert_ack (alert_id, ack_by_user_id, note)
            VALUES (%s, %s, %s)
            RETURNING id,
                      alert_id,
                      ack_at,
                      note,
                      ack_by_user_id,
                      (SELECT name FROM users WHERE id = ack_by_user_id) AS ack_by_name
        """
        return db.fetch_one(query, (alert_id, user_id, note))

    def resolve(
        self,
        alert_id: str,
        user_id: str | None,
        outcome: str | None,
        note: str | None,
    ) -> dict[str, Any] | None:
        query = """
            INSERT INTO alert_resolution (alert_id, resolved_by_user_id, outcome, note)
            VALUES (%s, %s, %s, %s)
            RETURNING id,
                      alert_id,
                      resolved_at,
                      resolved_by_user_id,
                      (SELECT name FROM users WHERE id = resolved_by_user_id) AS resolved_by_name,
                      outcome,
                      note
        """
        return db.fetch_one(query, (alert_id, user_id, outcome, note))

    def create_alert(
        self,
        patient_id: str,
        *,
        alert_type_code: str,
        alert_level_code: str,
        status_code: str,
        description: str | None = None,
        model_id: str | None = None,
        inference_id: str | None = None,
        location_wkt: str | None = None,
    ) -> dict[str, Any] | None:
        query = """
            SELECT *
            FROM heartguard.sp_alert_create(
                %(patient_id)s,
                %(alert_type_code)s,
                %(alert_level_code)s,
                %(status_code)s,
                %(model_id)s,
                %(inference_id)s,
                %(description)s,
                %(location_wkt)s
            )
        """
        params = {
            "patient_id": patient_id,
            "alert_type_code": alert_type_code,
            "alert_level_code": alert_level_code,
            "status_code": status_code,
            "model_id": model_id,
            "inference_id": inference_id,
            "description": description,
            "location_wkt": location_wkt,
        }
        return db.fetch_one(query, params)

    def update_alert(
        self,
        alert_id: str,
        *,
        alert_type_code: str,
        alert_level_code: str,
        status_code: str,
        description: str | None = None,
        model_id: str | None = None,
        inference_id: str | None = None,
        location_wkt: str | None = None,
    ) -> dict[str, Any] | None:
        query = """
            SELECT *
            FROM heartguard.sp_alert_update(
                %(alert_id)s,
                %(alert_type_code)s,
                %(alert_level_code)s,
                %(status_code)s,
                %(model_id)s,
                %(inference_id)s,
                %(description)s,
                %(location_wkt)s
            )
        """
        params = {
            "alert_id": alert_id,
            "alert_type_code": alert_type_code,
            "alert_level_code": alert_level_code,
            "status_code": status_code,
            "model_id": model_id,
            "inference_id": inference_id,
            "description": description,
            "location_wkt": location_wkt,
        }
        return db.fetch_one(query, params)

    def delete_alert(self, alert_id: str) -> bool:
        query = """
            SELECT heartguard.sp_alert_delete(%(alert_id)s) AS deleted
        """
        result = db.fetch_one(query, {"alert_id": alert_id})
        return bool(result and result.get("deleted"))

    def list_alert_types(self) -> list[dict[str, Any]]:
        """Get all alert types from the catalog."""
        query = """
            SELECT
                id,
                code,
                description,
                severity_min_id,
                severity_max_id
            FROM heartguard.alert_types
            ORDER BY code
        """
        return db.fetch_all(query)

    def list_alert_levels(self) -> list[dict[str, Any]]:
        """Get all alert levels (severity) from the catalog."""
        query = """
            SELECT
                id,
                code,
                label,
                weight
            FROM heartguard.alert_levels
            ORDER BY weight
        """
        return db.fetch_all(query)

    def list_alert_statuses(self) -> list[dict[str, Any]]:
        """Get all alert statuses from the catalog."""
        query = """
            SELECT
                id,
                code,
                description
            FROM heartguard.alert_status
            ORDER BY step_order
        """
        return db.fetch_all(query)