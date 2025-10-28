from typing import Optional, Dict, Any, List
from db import get_conn, put_conn

def fetch_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT id, name, email, password_hash, user_status_id
    FROM users
    WHERE lower(email) = lower(%s)
    LIMIT 1;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (email,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": str(row[0]),
                "name": row[1],
                "email": row[2],
                "password_hash": row[3],
                "user_status_id": str(row[4]) if row[4] else None
            }
    finally:
        put_conn(conn)

def fetch_user_roles(user_id: str) -> List[str]:
    sql = """
    SELECT r.name
    FROM user_role ur
    JOIN roles r ON r.id = ur.role_id
    WHERE ur.user_id = %s
    ORDER BY r.name;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            return [r[0] for r in cur.fetchall()]
    finally:
        put_conn(conn)

def create_user(name: str, email: str, password_hash: str, user_status_id: str) -> str:
    sql = """
    INSERT INTO users (name, email, password_hash, user_status_id)
    VALUES (%s, %s, %s, %s)
    RETURNING id;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (name, email, password_hash, user_status_id))
            new_id = cur.fetchone()[0]
            conn.commit()
            return str(new_id)
    finally:
        put_conn(conn)

def insert_refresh_token(user_id: str, token_hash: str, expires_at):
    sql = """
    INSERT INTO refresh_tokens
      (user_id, token_hash, issued_at, expires_at)
    VALUES (%s, %s, NOW(), %s)
    ON CONFLICT (user_id, token_hash)
      DO UPDATE SET revoked_at = NULL,
                    issued_at = NOW(),
                    expires_at = EXCLUDED.expires_at;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, token_hash, expires_at))
            conn.commit()
    finally:
        put_conn(conn)


def revoke_refresh_token(user_id: str, token_hash: str):
    sql = """
    UPDATE refresh_tokens
       SET revoked_at = NOW()
     WHERE user_id = %s AND token_hash = %s AND revoked_at IS NULL;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, token_hash))
            conn.commit()
    finally:
        put_conn(conn)


def is_refresh_token_active(user_id: str, token_hash: str) -> bool:
    sql = """
    SELECT 1
      FROM refresh_tokens
     WHERE user_id = %s
       AND token_hash = %s
       AND revoked_at IS NULL
       AND expires_at > NOW()
     LIMIT 1;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, token_hash))
            return cur.fetchone() is not None
    finally:
        put_conn(conn)
