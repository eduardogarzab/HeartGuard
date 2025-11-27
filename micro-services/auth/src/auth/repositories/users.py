"""Acceso a datos de usuarios."""
from __future__ import annotations

from typing import Any, Optional

from ..extensions import get_db_cursor


def get_by_email(email: str) -> Optional[dict[str, Any]]:
    query = """
        SELECT
            u.id,
            u.name,
            u.email,
            u.password_hash,
            u.role_code,
            u.user_status_id,
            us.code AS user_status_code,
            us.label AS user_status_label,
            u.created_at,
            u.updated_at
        FROM heartguard.users u
        JOIN heartguard.user_statuses us ON us.id = u.user_status_id
        WHERE lower(u.email) = lower(%s)
    """
    with get_db_cursor() as cur:
        cur.execute(query, (email,))
        return cur.fetchone()


def get_by_id(user_id: str) -> Optional[dict[str, Any]]:
    query = """
        SELECT
            u.id,
            u.name,
            u.email,
            u.role_code,
            u.user_status_id,
            us.code AS user_status_code,
            us.label AS user_status_label,
            u.created_at,
            u.updated_at
        FROM heartguard.users u
        JOIN heartguard.user_statuses us ON us.id = u.user_status_id
        WHERE u.id = %s
    """
    with get_db_cursor() as cur:
        cur.execute(query, (user_id,))
        return cur.fetchone()


def create_user(*, name: str, email: str, password_hash: str, status_code: str = "active", role_code: str = "user") -> dict[str, Any]:
    status_id = _get_status_id(status_code)
    if status_id is None:
        raise ValueError(f"Estado de usuario {status_code!r} no existe")

    query = """
        INSERT INTO heartguard.users (name, email, password_hash, user_status_id, role_code)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, name, email, role_code, user_status_id, created_at
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(query, (name, email, password_hash, status_id, role_code))
        return cur.fetchone()


def list_memberships(user_id: str) -> list[dict[str, Any]]:
    query = """
        SELECT
            m.org_id,
            o.code AS org_code,
            o.name AS org_name,
            m.role_code,
            COALESCE(r.label, m.role_code) AS role_label,
            m.joined_at
        FROM heartguard.user_org_membership m
        JOIN heartguard.organizations o ON o.id = m.org_id
        LEFT JOIN heartguard.roles r ON r.code = m.role_code
        WHERE m.user_id = %s
        ORDER BY o.name, m.joined_at DESC
    """
    with get_db_cursor() as cur:
        cur.execute(query, (user_id,))
        return list(cur.fetchall() or [])


def _get_status_id(code: str) -> Optional[str]:
    query = "SELECT id FROM heartguard.user_statuses WHERE code = %s"
    with get_db_cursor() as cur:
        cur.execute(query, (code,))
        row = cur.fetchone()
        return row["id"] if row else None