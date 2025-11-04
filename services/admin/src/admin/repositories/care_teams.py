"""Repository helpers for care team operations."""
from __future__ import annotations

from typing import Any

from .. import db


class CareTeamsRepository:
    """Data access layer for care teams scoped to an organization."""

    def list_for_org(self, org_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT id, org_id, name, created_at
            FROM care_teams
            WHERE org_id = %s
            ORDER BY name ASC
        """
        return db.fetch_all(query, (org_id,))

    def create(self, org_id: str, name: str) -> dict[str, Any] | None:
        query = """
            INSERT INTO care_teams (org_id, name)
            VALUES (%s, %s)
            RETURNING id, org_id, name, created_at
        """
        return db.fetch_one(query, (org_id, name))

    def update(self, care_team_id: str, org_id: str, name: str | None) -> dict[str, Any] | None:
        query = """
            UPDATE care_teams
            SET name = COALESCE(%(name)s, name)
            WHERE id = %(care_team_id)s AND org_id = %(org_id)s
            RETURNING id, org_id, name, created_at
        """
        params = {"care_team_id": care_team_id, "org_id": org_id, "name": name}
        return db.fetch_one(query, params)

    def delete(self, care_team_id: str, org_id: str) -> None:
        query = """
            DELETE FROM care_teams
            WHERE id = %s AND org_id = %s
        """
        db.execute(query, (care_team_id, org_id))

    def list_members(self, care_team_id: str, org_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
                m.user_id,
                u.name,
                u.email,
                m.role_id,
                r.code AS role_code,
                r.label AS role_label,
                m.joined_at
            FROM care_team_member m
            JOIN users u ON u.id = m.user_id
            JOIN team_member_roles r ON r.id = m.role_id
            JOIN care_teams ct ON ct.id = m.care_team_id
            WHERE m.care_team_id = %s AND ct.org_id = %s
            ORDER BY u.name ASC
        """
        return db.fetch_all(query, (care_team_id, org_id))

    def add_member(self, care_team_id: str, org_id: str, user_id: str, role_id: str) -> dict[str, Any] | None:
        query = """
            WITH inserted AS (
                INSERT INTO care_team_member (care_team_id, user_id, role_id)
                SELECT %s, %s, %s
                WHERE EXISTS (
                    SELECT 1 FROM care_teams WHERE id = %s AND org_id = %s
                )
                AND EXISTS (
                    SELECT 1 FROM user_org_membership WHERE org_id = %s AND user_id = %s
                )
                RETURNING care_team_id, user_id, role_id, joined_at
            )
            SELECT
                i.care_team_id,
                i.user_id,
                i.role_id,
                i.joined_at,
                u.name,
                u.email,
                r.code AS role_code,
                r.label AS role_label
            FROM inserted i
            JOIN users u ON u.id = i.user_id
            JOIN team_member_roles r ON r.id = i.role_id
        """
        params = (care_team_id, user_id, role_id, care_team_id, org_id, org_id, user_id)
        return db.fetch_one(query, params)

    def update_member(self, care_team_id: str, org_id: str, user_id: str, role_id: str) -> dict[str, Any] | None:
        query = """
            WITH updated AS (
                UPDATE care_team_member AS m
                SET role_id = %(role_id)s
                FROM care_teams ct
                WHERE m.care_team_id = %(care_team_id)s
                  AND m.user_id = %(user_id)s
                  AND m.care_team_id = ct.id
                  AND ct.org_id = %(org_id)s
                RETURNING m.care_team_id, m.user_id, m.role_id, m.joined_at
            )
            SELECT
                u.care_team_id,
                u.user_id,
                u.role_id,
                u.joined_at,
                usr.name,
                usr.email,
                r.code AS role_code,
                r.label AS role_label
            FROM updated u
            JOIN users usr ON usr.id = u.user_id
            JOIN team_member_roles r ON r.id = u.role_id
        """
        params = {
            "role_id": role_id,
            "care_team_id": care_team_id,
            "user_id": user_id,
            "org_id": org_id,
        }
        return db.fetch_one(query, params)

    def remove_member(self, care_team_id: str, org_id: str, user_id: str) -> None:
        query = """
            DELETE FROM care_team_member
            USING care_teams ct
            WHERE care_team_id = %s
              AND user_id = %s
              AND care_team_member.care_team_id = ct.id
              AND ct.org_id = %s
        """
        db.execute(query, (care_team_id, user_id, org_id))

    def list_patients(self, care_team_id: str, org_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
                pct.patient_id,
                p.person_name,
                p.email,
                pct.care_team_id
            FROM patient_care_team pct
            JOIN patients p ON p.id = pct.patient_id
            JOIN care_teams ct ON ct.id = pct.care_team_id
            WHERE pct.care_team_id = %s AND ct.org_id = %s
            ORDER BY p.person_name ASC
        """
        return db.fetch_all(query, (care_team_id, org_id))

    def add_patient(self, care_team_id: str, org_id: str, patient_id: str) -> dict[str, Any] | None:
        query = """
            WITH inserted AS (
                INSERT INTO patient_care_team (patient_id, care_team_id)
                SELECT %s, %s
                WHERE EXISTS (
                    SELECT 1 FROM care_teams WHERE id = %s AND org_id = %s
                )
                AND EXISTS (
                    SELECT 1 FROM patients WHERE id = %s AND org_id = %s
                )
                ON CONFLICT DO NOTHING
                RETURNING patient_id, care_team_id
            )
            SELECT
                i.patient_id,
                p.person_name,
                p.email,
                i.care_team_id
            FROM inserted i
            JOIN patients p ON p.id = i.patient_id
        """
        params = (patient_id, care_team_id, care_team_id, org_id, patient_id, org_id)
        return db.fetch_one(query, params)

    def remove_patient(self, care_team_id: str, org_id: str, patient_id: str) -> None:
        query = """
            DELETE FROM patient_care_team
            USING care_teams ct
            WHERE care_team_id = %s
              AND patient_id = %s
              AND patient_care_team.care_team_id = ct.id
              AND ct.org_id = %s
        """
        db.execute(query, (care_team_id, patient_id, org_id))