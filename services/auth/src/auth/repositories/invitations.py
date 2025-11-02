"""Acceso y actualización de invitaciones a organizaciones."""
from __future__ import annotations

from typing import Any, Optional

from ..extensions import get_db_cursor


def get_valid_invitation(token: str) -> Optional[dict[str, Any]]:
    query = """
        SELECT
            inv.id,
            inv.org_id,
            inv.email,
            inv.role_code,
            inv.token,
            inv.expires_at,
            inv.used_at,
            inv.revoked_at,
            inv.created_at,
            o.name AS org_name,
            o.code AS org_code
        FROM heartguard.org_invitations inv
        JOIN heartguard.organizations o ON o.id = inv.org_id
        WHERE inv.token = %s
          AND inv.revoked_at IS NULL
          AND inv.used_at IS NULL
          AND (inv.expires_at IS NULL OR inv.expires_at > NOW())
    """
    with get_db_cursor() as cur:
        cur.execute(query, (token,))
        return cur.fetchone()


def mark_invitation_used(invitation_id: str) -> None:
    query = "UPDATE heartguard.org_invitations SET used_at = NOW() WHERE id = %s"
    with get_db_cursor(commit=True) as cur:
        cur.execute(query, (invitation_id,))


def create_membership(org_id: str, user_id: str, role_code: str) -> dict[str, Any]:
    query = """
        INSERT INTO heartguard.user_org_membership (org_id, user_id, role_code)
        VALUES (%s, %s, %s)
        ON CONFLICT (org_id, user_id) DO UPDATE SET role_code = EXCLUDED.role_code
        RETURNING org_id, user_id, role_code, joined_at
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(query, (org_id, user_id, role_code))
        return cur.fetchone()