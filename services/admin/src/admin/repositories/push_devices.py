"""Repository helpers for push device registrations."""
from __future__ import annotations

from typing import Any

from .. import db


class PushDevicesRepository:
    """Data access for push devices scoped to organization members."""

    def list_for_org(
        self,
        org_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        active: bool | None = None,
    ) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 200))
        safe_offset = max(0, int(offset))
        clauses = ["m.org_id = %(org_id)s"]
        params: dict[str, Any] = {
            "org_id": org_id,
            "limit": safe_limit,
            "offset": safe_offset,
        }
        if active is not None:
            clauses.append("pd.active = %(active)s")
            params["active"] = active
        query = f"""
            SELECT
                pd.id,
                pd.user_id,
                u.name AS user_name,
                u.email AS user_email,
                pd.platform_id,
                pl.code AS platform_code,
                pl.label AS platform_label,
                pd.push_token,
                pd.last_seen_at,
                pd.active
            FROM push_devices pd
            JOIN users u ON u.id = pd.user_id
            JOIN platforms pl ON pl.id = pd.platform_id
            JOIN user_org_membership m ON m.user_id = pd.user_id
            WHERE {' AND '.join(clauses)}
            ORDER BY pd.last_seen_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        return db.fetch_all(query, params)

    def get(self, org_id: str, device_id: str) -> dict[str, Any] | None:
        query = """
            SELECT
                pd.id,
                pd.user_id,
                u.name AS user_name,
                u.email AS user_email,
                pd.platform_id,
                pl.code AS platform_code,
                pl.label AS platform_label,
                pd.push_token,
                pd.last_seen_at,
                pd.active
            FROM push_devices pd
            JOIN users u ON u.id = pd.user_id
            JOIN platforms pl ON pl.id = pd.platform_id
            JOIN user_org_membership m ON m.user_id = pd.user_id
            WHERE pd.id = %(device_id)s AND m.org_id = %(org_id)s
        """
        params = {"device_id": device_id, "org_id": org_id}
        return db.fetch_one(query, params)

    def update_active(self, device_id: str, active: bool) -> dict[str, Any] | None:
        query = """
            UPDATE push_devices
               SET active = %(active)s,
                   last_seen_at = NOW()
             WHERE id = %(device_id)s
            RETURNING
                id,
                user_id,
                platform_id,
                push_token,
                last_seen_at,
                active
        """
        params = {"device_id": device_id, "active": active}
        return db.fetch_one(query, params)

    def delete(self, device_id: str) -> bool:
        query = """
            DELETE FROM push_devices
            WHERE id = %(device_id)s
            RETURNING id
        """
        return db.fetch_one(query, {"device_id": device_id}) is not None

    def list_platforms(self) -> list[dict[str, Any]]:
        query = """
            SELECT id, code, label
            FROM platforms
            ORDER BY label ASC
        """
        return db.fetch_all(query)
