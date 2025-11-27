"""Acceso a datos de pacientes."""
from __future__ import annotations

from typing import Any, Optional

from ..extensions import get_db_cursor


def get_by_email(email: str) -> Optional[dict[str, Any]]:
    query = """
        SELECT
            p.id,
            p.org_id,
            p.person_name AS name,
            p.email,
            p.password_hash,
            p.birthdate,
            p.sex_id,
            sx.code AS sex_code,
            p.risk_level_id,
            rl.code AS risk_level_code,
            p.created_at,
            o.code AS org_code,
            o.name AS org_name
        FROM heartguard.patients p
        LEFT JOIN heartguard.sexes sx ON sx.id = p.sex_id
        LEFT JOIN heartguard.risk_levels rl ON rl.id = p.risk_level_id
        LEFT JOIN heartguard.organizations o ON o.id = p.org_id
        WHERE lower(p.email) = lower(%s)
    """
    with get_db_cursor() as cur:
        cur.execute(query, (email,))
        return cur.fetchone()


def get_by_id(patient_id: str) -> Optional[dict[str, Any]]:
    query = """
        SELECT
            p.id,
            p.org_id,
            p.person_name AS name,
            p.email,
            p.birthdate,
            p.sex_id,
            sx.code AS sex_code,
            sx.label AS sex_label,
            p.risk_level_id,
            rl.code AS risk_level_code,
            rl.label AS risk_level_label,
            o.code AS org_code,
            o.name AS org_name
        FROM heartguard.patients p
        LEFT JOIN heartguard.sexes sx ON sx.id = p.sex_id
        LEFT JOIN heartguard.risk_levels rl ON rl.id = p.risk_level_id
        LEFT JOIN heartguard.organizations o ON o.id = p.org_id
        WHERE p.id = %s
    """
    with get_db_cursor() as cur:
        cur.execute(query, (patient_id,))
        return cur.fetchone()


def create_patient(
    *,
    org_id: str,
    name: str,
    email: str,
    password_hash: str,
    birthdate: str | None,
    sex_code: str | None,
    risk_level_code: str | None,
) -> dict[str, Any]:
    sex_id = _get_sex_id(sex_code) if sex_code else None
    risk_level_id = _get_risk_level_id(risk_level_code) if risk_level_code else None

    query = """
        INSERT INTO heartguard.patients (org_id, person_name, email, password_hash, birthdate, sex_id, risk_level_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, org_id, person_name AS name, email, birthdate, sex_id, risk_level_id
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(query, (org_id, name, email, password_hash, birthdate, sex_id, risk_level_id))
        return cur.fetchone()


def _get_sex_id(code: str | None) -> Optional[str]:
    if not code:
        return None
    query = "SELECT id FROM heartguard.sexes WHERE lower(code) = lower(%s)"
    with get_db_cursor() as cur:
        cur.execute(query, (code,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Sexo {code} no existe")
        return row["id"]


def _get_risk_level_id(code: str | None) -> Optional[str]:
    if not code:
        return None
    query = "SELECT id FROM heartguard.risk_levels WHERE lower(code) = lower(%s)"
    with get_db_cursor() as cur:
        cur.execute(query, (code,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Nivel de riesgo {code} no existe")
        return row["id"]