"""Repository access for organization data."""
from __future__ import annotations

from typing import Any

from .. import db


class OrganizationsRepository:
    """Queries for organization metadata and stats."""

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
                o.id,
                o.code,
                o.name,
                m.role_code,
                m.joined_at
            FROM user_org_membership m
            JOIN organizations o ON o.id = m.org_id
            WHERE m.user_id = %s AND m.role_code = 'org_admin'
            ORDER BY o.name ASC
        """
        return db.fetch_all(query, (user_id,))

    def get(self, org_id: str) -> dict[str, Any] | None:
        query = """
            SELECT id, code, name, created_at
            FROM organizations
            WHERE id = %s
        """
        return db.fetch_one(query, (org_id,))

    def stats(self, org_id: str) -> dict[str, Any]:
        query = """
            SELECT
                COALESCE((SELECT COUNT(*) FROM user_org_membership WHERE org_id = %(org_id)s), 0) AS member_count,
                COALESCE((SELECT COUNT(*) FROM patients WHERE org_id = %(org_id)s), 0) AS patient_count,
                COALESCE((SELECT COUNT(*) FROM care_teams WHERE org_id = %(org_id)s), 0) AS care_team_count,
                COALESCE((
                    SELECT COUNT(*)
                    FROM caregiver_patient cp
                    JOIN patients p ON p.id = cp.patient_id
                    WHERE p.org_id = %(org_id)s
                ), 0) AS caregiver_count,
                COALESCE((
                    SELECT COUNT(*)
                    FROM alerts a
                    JOIN patients p ON p.id = a.patient_id
                    WHERE p.org_id = %(org_id)s
                ), 0) AS alert_count
        """
        result = db.fetch_one(query, {"org_id": org_id})
        return result or {
            "member_count": 0,
            "patient_count": 0,
            "care_team_count": 0,
            "caregiver_count": 0,
            "alert_count": 0,
        }