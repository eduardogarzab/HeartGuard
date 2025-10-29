from typing import Optional

from db import get_conn, put_conn


def user_belongs_to_org(user_id: str, org_id: str) -> bool:
    sql = """
        SELECT 1
          FROM user_org_membership
         WHERE user_id = %s AND org_id = %s
         LIMIT 1;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, org_id))
            return cur.fetchone() is not None
    finally:
        put_conn(conn)


def resolve_org_for_user(user_id: str) -> Optional[str]:
    sql = """
        SELECT org_id
          FROM user_org_membership
         WHERE user_id = %s
         ORDER BY joined_at ASC
         LIMIT 1;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            row = cur.fetchone()
            return str(row[0]) if row else None
    finally:
        put_conn(conn)
