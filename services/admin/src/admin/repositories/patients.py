"""Repository for patient operations."""
from __future__ import annotations

from typing import Any

from .. import db


class PatientsRepository:
    """Data access layer for patients."""

    def list_by_org(self, org_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
                p.id,
                p.person_name,
                p.email,
                p.birthdate,
                p.org_id,
                o.name AS org_name,
                rl.code AS risk_level_code,
                rl.label AS risk_level_label,
                p.created_at
            FROM patients p
            JOIN organizations o ON o.id = p.org_id
            LEFT JOIN risk_levels rl ON rl.id = p.risk_level_id
            WHERE p.org_id = %s
            ORDER BY p.person_name ASC
        """
        return db.fetch_all(query, (org_id,))

    def create_patient(
        self,
        *,
        org_id: str,
        name: str,
        email: str,
        raw_password: str,
        birthdate: str | None,
        risk_level_id: str | None,
    ) -> dict[str, Any]:
        # Si risk_level_id parece ser un código (no un UUID), convertirlo primero
        if risk_level_id and len(risk_level_id) < 36:
            # Es un código, no un UUID - buscar el UUID correspondiente
            lookup_query = "SELECT id FROM risk_levels WHERE code = %s"
            risk_level_row = db.fetch_one(lookup_query, (risk_level_id,))
            if risk_level_row:
                risk_level_id = str(risk_level_row['id'])
            else:
                risk_level_id = None
        
        query = """
            SELECT * FROM sp_patient_create(
                %(org_id)s,
                %(name)s,
                %(email)s,
                %(password)s,
                %(birthdate)s,
                NULL,
                %(risk_level_id)s,
                NULL
            )
        """
        params = {
            "org_id": org_id,
            "name": name,
            "email": email,
            "password": raw_password,
            "birthdate": birthdate,
            "risk_level_id": risk_level_id,
        }
        return db.fetch_one(query, params) or {}

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        query = """
            SELECT
                p.id,
                p.person_name,
                p.email,
                p.birthdate,
                p.org_id,
                o.name AS org_name,
                rl.code AS risk_level_code,
                rl.label AS risk_level_label,
                p.created_at
            FROM patients p
            JOIN organizations o ON o.id = p.org_id
            LEFT JOIN risk_levels rl ON rl.id = p.risk_level_id
            WHERE p.id = %s
        """
        return db.fetch_one(query, (patient_id,))

    def update_patient(
        self,
        patient_id: str,
        *,
        name: str | None,
        birthdate: str | None,
        risk_level_id: str | None,
    ) -> dict[str, Any] | None:
        # Si risk_level_id parece ser un código (no un UUID), convertirlo primero
        if risk_level_id and len(risk_level_id) < 36:
            # Es un código, no un UUID - buscar el UUID correspondiente
            lookup_query = "SELECT id FROM risk_levels WHERE code = %s"
            risk_level_row = db.fetch_one(lookup_query, (risk_level_id,))
            if risk_level_row:
                risk_level_id = str(risk_level_row['id'])
            else:
                risk_level_id = None
        
        query = """
            UPDATE patients
            SET person_name = COALESCE(%(name)s, person_name),
                birthdate = COALESCE(%(birthdate)s, birthdate),
                risk_level_id = COALESCE(%(risk_level_id)s, risk_level_id)
            WHERE id = %(patient_id)s
            RETURNING id, person_name, email, birthdate, org_id, risk_level_id
        """
        params = {
            "patient_id": patient_id,
            "name": name,
            "birthdate": birthdate,
            "risk_level_id": risk_level_id,
        }
        return db.fetch_one(query, params)

    def delete_patient(self, patient_id: str) -> None:
        query = """
            DELETE FROM patients
            WHERE id = %s
        """
        db.execute(query, (patient_id,))
