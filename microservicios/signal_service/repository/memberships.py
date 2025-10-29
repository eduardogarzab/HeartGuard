"""Repository helpers for membership validation."""

from typing import Optional

from db import connection_scope


def user_belongs_to_org(user_id: str, org_id: str) -> bool:
    sql = """
        SELECT 1
          FROM user_org_membership
         WHERE user_id = %s AND org_id = %s
         LIMIT 1;
    """
    with connection_scope() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, org_id))
            return cur.fetchone() is not None


def resolve_org_for_user(user_id: str) -> Optional[str]:
    sql = """
        SELECT org_id
          FROM user_org_membership
         WHERE user_id = %s
         ORDER BY joined_at ASC
         LIMIT 1;
    """
    with connection_scope() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            row = cur.fetchone()
            return str(row[0]) if row else None
