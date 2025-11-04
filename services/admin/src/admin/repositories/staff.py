"""Repository for staff membership operations."""
from __future__ import annotations

from typing import Any

from .. import db


class StaffRepository:
    """Handle queries for organization staff membership."""

    def list_members(self, org_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
                u.id AS user_id,
                u.name,
                u.email,
                m.role_code,
                r.label AS role_label,
                m.joined_at
            FROM user_org_membership m
            JOIN users u ON u.id = m.user_id
            LEFT JOIN roles r ON r.code = m.role_code
            WHERE m.org_id = %s
            ORDER BY u.name ASC
        """
        return db.fetch_all(query, (org_id,))

    def update_role(self, org_id: str, user_id: str, role_code: str) -> None:
        query = """
            UPDATE user_org_membership
            SET role_code = %s
            WHERE org_id = %s AND user_id = %s
        """
        db.execute(query, (role_code, org_id, user_id))

    def remove_member(self, org_id: str, user_id: str) -> None:
        query = """
            DELETE FROM user_org_membership
            WHERE org_id = %s AND user_id = %s
        """
        db.execute(query, (org_id, user_id))

    def list_invitations(self, org_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        query = """
            SELECT *
            FROM heartguard.sp_org_invitations_list(
                %(org_id)s,
                %(limit)s,
                %(offset)s
            )
        """
        params = {"org_id": org_id, "limit": limit, "offset": offset}
        return db.fetch_all(query, params)

    def create_invitation(
        self,
        org_id: str,
        invited_by: str,
        email: str,
        role_code: str,
        ttl_hours: int | None = None,
    ) -> dict[str, Any]:
        query = """
            SELECT *
            FROM heartguard.sp_org_invitation_create(
                %(org_id)s,
                %(role_code)s,
                %(email)s,
                %(ttl_hours)s,
                %(invited_by)s
            )
        """
        params = {
            "org_id": org_id,
            "role_code": role_code,
            "email": email.lower(),
            "ttl_hours": ttl_hours,
            "invited_by": invited_by,
        }
        return db.fetch_one(query, params) or {}

    def revoke_invitation(self, org_id: str, invitation_id: str) -> None:
        """Revoke an invitation by setting revoked_at timestamp."""
        query = """
            UPDATE org_invitations
            SET revoked_at = NOW()
            WHERE id = %s AND org_id = %s AND revoked_at IS NULL
        """
        db.execute(query, (invitation_id, org_id))
