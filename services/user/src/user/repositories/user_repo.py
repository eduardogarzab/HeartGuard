"""Repositorio de acceso a datos para usuarios"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..extensions import get_db_cursor


class UserRepository:
    """Operaciones de base de datos relacionadas con usuarios"""

    @staticmethod
    def get_user_profile(user_id: str) -> Optional[Dict]:
        query = """
            SELECT
                u.id,
                u.name,
                u.email,
                u.role_code,
                u.two_factor_enabled,
                u.profile_photo_url,
                u.created_at,
                u.updated_at,
                us.code AS status_code,
                us.label AS status_label
            FROM users u
            JOIN user_statuses us ON us.id = u.user_status_id
            WHERE u.id = %s
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (user_id,))
            return cursor.fetchone()

    @staticmethod
    def update_user_profile(user_id: str, updates: Dict) -> Optional[Dict]:
        allowed_columns = {
            'name': 'name',
            'profile_photo_url': 'profile_photo_url',
            'two_factor_enabled': 'two_factor_enabled',
        }
        set_parts: List[str] = []
        values: List[Any] = []

        for field, column in allowed_columns.items():
            if field in updates:
                set_parts.append(f"{column} = %s")
                values.append(updates[field])

        if not set_parts:
            return None

        set_parts.append('updated_at = NOW()')
        query = f"""
            UPDATE users
            SET {', '.join(set_parts)}
            WHERE id = %s
            RETURNING id
        """
        values.append(user_id)

        with get_db_cursor() as cursor:
            cursor.execute(query, tuple(values))
            return cursor.fetchone()

    @staticmethod
    def list_memberships(user_id: str) -> List[Dict]:
        query = """
            SELECT
                m.org_id,
                o.code AS org_code,
                o.name AS org_name,
                m.role_code,
                COALESCE(r.label, m.role_code) AS role_label,
                m.joined_at
            FROM user_org_membership m
            JOIN organizations o ON o.id = m.org_id
            LEFT JOIN roles r ON r.code = m.role_code
            WHERE m.user_id = %s
            ORDER BY o.name ASC, m.joined_at DESC
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall() or []
            return list(rows)

    @staticmethod
    def get_membership(org_id: str, user_id: str) -> Optional[Dict]:
        query = """
            SELECT
                m.org_id,
                m.user_id,
                m.role_code,
                COALESCE(r.label, m.role_code) AS role_label,
                m.joined_at,
                o.code AS org_code,
                o.name AS org_name
            FROM user_org_membership m
            JOIN organizations o ON o.id = m.org_id
            LEFT JOIN roles r ON r.code = m.role_code
            WHERE m.org_id = %s AND m.user_id = %s
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (org_id, user_id))
            return cursor.fetchone()
