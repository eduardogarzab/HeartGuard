"""Repository for caregiver assignments."""
from __future__ import annotations

from typing import Any

from .. import db


class CaregiversRepository:
    """Data access layer for caregiver assignment operations."""

    def list_relationship_types(self) -> list[dict[str, Any]]:
        query = """
            SELECT id, code, label
            FROM caregiver_relationship_types
            ORDER BY label ASC
        """
        return db.fetch_all(query)

    def list_assignments(self, org_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
                cp.patient_id,
                p.person_name AS patient_name,
                cp.user_id AS caregiver_id,
                u.name AS caregiver_name,
                u.email AS caregiver_email,
                cp.rel_type_id,
                crt.code AS relationship_code,
                crt.label AS relationship_label,
                cp.is_primary,
                cp.started_at,
                cp.ended_at,
                cp.note
            FROM caregiver_patient cp
            JOIN patients p ON p.id = cp.patient_id
            JOIN users u ON u.id = cp.user_id
            LEFT JOIN caregiver_relationship_types crt ON crt.id = cp.rel_type_id
            WHERE p.org_id = %s
            ORDER BY p.person_name ASC, u.name ASC
        """
        return db.fetch_all(query, (org_id,))

    def create_assignment(
        self,
        org_id: str,
        patient_id: str,
        caregiver_id: str,
    *,
    relationship_type_id: str | None,
    is_primary: bool | None,
        started_at: str | None,
        ended_at: str | None,
        note: str | None,
    ) -> dict[str, Any] | None:
        query = """
            WITH inserted AS (
                INSERT INTO caregiver_patient (
                    patient_id,
                    user_id,
                    rel_type_id,
                    is_primary,
                    started_at,
                    ended_at,
                    note
                )
                SELECT %s, %s, %s, COALESCE(%s, FALSE), COALESCE(%s, NOW()), %s, %s
                WHERE EXISTS (
                    SELECT 1 FROM patients WHERE id = %s AND org_id = %s
                )
                AND EXISTS (
                    SELECT 1 FROM user_org_membership WHERE user_id = %s AND org_id = %s
                )
                ON CONFLICT (patient_id, user_id) DO UPDATE
                SET rel_type_id = EXCLUDED.rel_type_id,
                    is_primary = EXCLUDED.is_primary,
                    started_at = EXCLUDED.started_at,
                    ended_at = EXCLUDED.ended_at,
                    note = EXCLUDED.note
                RETURNING patient_id, user_id, rel_type_id, is_primary, started_at, ended_at, note
            )
            SELECT
                i.patient_id,
                p.person_name AS patient_name,
                i.user_id AS caregiver_id,
                u.name AS caregiver_name,
                u.email AS caregiver_email,
                i.rel_type_id,
                crt.code AS relationship_code,
                crt.label AS relationship_label,
                i.is_primary,
                i.started_at,
                i.ended_at,
                i.note
            FROM inserted i
            JOIN patients p ON p.id = i.patient_id
            JOIN users u ON u.id = i.user_id
            LEFT JOIN caregiver_relationship_types crt ON crt.id = i.rel_type_id
        """
        params = (
            patient_id,
            caregiver_id,
            relationship_type_id,
            is_primary,
            started_at,
            ended_at,
            note,
            patient_id,
            org_id,
            caregiver_id,
            org_id,
        )
        return db.fetch_one(query, params)

    def update_assignment(
        self,
        org_id: str,
        patient_id: str,
        caregiver_id: str,
        *,
        relationship_type_id: str | None,
        clear_relationship: bool,
        is_primary: bool | None,
        started_at: str | None,
        ended_at: str | None,
        note: str | None,
    ) -> dict[str, Any] | None:
        query = """
            WITH updated AS (
                UPDATE caregiver_patient AS cp
                SET rel_type_id = CASE
                        WHEN %(clear_relationship)s THEN NULL
                        WHEN %(rel_type_id)s IS NULL THEN cp.rel_type_id
                        ELSE %(rel_type_id)s
                    END,
                    is_primary = COALESCE(%(is_primary)s, cp.is_primary),
                    started_at = COALESCE(%(started_at)s, cp.started_at),
                    ended_at = %(ended_at)s,
                    note = %(note)s
                FROM patients p
                WHERE cp.patient_id = %(patient_id)s
                  AND cp.user_id = %(caregiver_id)s
                  AND cp.patient_id = p.id
                  AND p.org_id = %(org_id)s
                RETURNING cp.patient_id, cp.user_id, cp.rel_type_id, cp.is_primary, cp.started_at, cp.ended_at, cp.note
            )
            SELECT
                u.patient_id,
                p.person_name AS patient_name,
                u.user_id AS caregiver_id,
                usr.name AS caregiver_name,
                usr.email AS caregiver_email,
                u.rel_type_id,
                crt.code AS relationship_code,
                crt.label AS relationship_label,
                u.is_primary,
                u.started_at,
                u.ended_at,
                u.note
            FROM updated u
            JOIN patients p ON p.id = u.patient_id
            JOIN users usr ON usr.id = u.user_id
            LEFT JOIN caregiver_relationship_types crt ON crt.id = u.rel_type_id
        """
        params = {
            "rel_type_id": relationship_type_id,
            "clear_relationship": clear_relationship,
            "is_primary": is_primary,
            "started_at": started_at,
            "ended_at": ended_at,
            "note": note,
            "patient_id": patient_id,
            "caregiver_id": caregiver_id,
            "org_id": org_id,
        }
        return db.fetch_one(query, params)

    def delete_assignment(self, org_id: str, patient_id: str, caregiver_id: str) -> None:
        query = """
            DELETE FROM caregiver_patient
            USING patients p
            WHERE caregiver_patient.patient_id = %s
              AND caregiver_patient.user_id = %s
              AND caregiver_patient.patient_id = p.id
              AND p.org_id = %s
        """
        db.execute(query, (patient_id, caregiver_id, org_id))