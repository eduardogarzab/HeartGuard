"""Acceso a datos de organizaciones."""
from __future__ import annotations

from typing import Any, Optional

from ..extensions import get_db_cursor


def get_by_id(org_id: str) -> Optional[dict[str, Any]]:
    query = """
        SELECT id, code, name
        FROM heartguard.organizations
        WHERE id = %s
    """
    with get_db_cursor() as cur:
        cur.execute(query, (org_id,))
        return cur.fetchone()


def get_by_code(org_code: str) -> Optional[dict[str, Any]]:
    """Obtiene una organización por su código."""
    query = """
        SELECT id, code, name
        FROM heartguard.organizations
        WHERE code = %s
    """
    with get_db_cursor() as cur:
        cur.execute(query, (org_code,))
        return cur.fetchone()