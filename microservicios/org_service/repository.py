from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from config import settings
from db import get_conn, put_conn


def _as_utc(dt):
    if not dt:
        return None
    if getattr(dt, "tzinfo", None) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _iso(dt) -> Optional[str]:
    normalized = _as_utc(dt)
    return normalized.isoformat() if normalized else None


def get_org_by_id(org_id: str) -> Optional[Dict[str, Any]]:
    sql = "SELECT id, code, name, created_at FROM organizations WHERE id = %s"
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (org_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": str(row[0]),
                "code": row[1],
                "name": row[2],
                "created_at": _iso(row[3]),
            }
    finally:
        put_conn(conn)


def get_membership(user_id: str, org_id: str) -> Optional[Dict[str, Any]]:
    sql = """
        SELECT m.org_id, o.code, o.name, m.joined_at, r.code AS role_code
        FROM user_org_membership m
        JOIN organizations o ON o.id = m.org_id
        LEFT JOIN org_roles r ON r.id = m.org_role_id
        WHERE m.user_id = %s AND m.org_id = %s
        LIMIT 1
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, org_id))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "org_id": str(row[0]),
                "org_code": row[1],
                "org_name": row[2],
                "joined_at": _iso(row[3]),
                "role_code": row[4],
            }
    finally:
        put_conn(conn)


def list_orgs_for_user(user_id: str) -> List[Dict[str, Any]]:
    sql = """
        SELECT o.id, o.code, o.name, o.created_at, r.code AS role_code
        FROM user_org_membership m
        JOIN organizations o ON o.id = m.org_id
        LEFT JOIN org_roles r ON r.id = m.org_role_id
        WHERE m.user_id = %s
        ORDER BY o.created_at DESC
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            rows = cur.fetchall()
            return [
                {
                    "id": str(row[0]),
                    "code": row[1],
                    "name": row[2],
                    "created_at": _iso(row[3]),
                    "role_code": row[4],
                }
                for row in rows
            ]
    finally:
        put_conn(conn)


def is_org_admin(user_id: str, org_id: str) -> bool:
    sql = """
        SELECT 1
        FROM user_org_membership m
        JOIN org_roles r ON r.id = m.org_role_id
        WHERE m.user_id = %s
          AND m.org_id = %s
          AND lower(r.code) = 'org_admin'
        LIMIT 1
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, org_id))
            return cur.fetchone() is not None
    finally:
        put_conn(conn)


def _resolve_role_id(cur, role_code: str):
    cur.execute(
        "SELECT id FROM org_roles WHERE lower(code) = lower(%s) LIMIT 1",
        (role_code,),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError("unknown_role")
    return row[0]


def create_invitation(
    org_id: str,
    email: str,
    invited_by_user_id: str,
    token: str,
    role_code: Optional[str] = None,
) -> str:
    sql = """
        INSERT INTO org_invitations (org_id, email, org_role_id, token, expires_at, created_by)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            resolved_role = _resolve_role_id(cur, role_code or settings.DEFAULT_INVITATION_ROLE)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.INVITATION_TTL_HOURS)
            cur.execute(sql, (org_id, email, resolved_role, token, expires_at, invited_by_user_id))
            new_id = cur.fetchone()[0]
            conn.commit()
            return str(new_id)
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)


def list_invitations(org_id: str) -> List[Dict[str, Any]]:
    sql = """
        SELECT i.id, i.email, i.token, i.expires_at, i.used_at, i.revoked_at,
               i.created_at, r.code AS role_code
        FROM org_invitations i
        LEFT JOIN org_roles r ON r.id = i.org_role_id
        WHERE i.org_id = %s
        ORDER BY i.created_at DESC
    """
    now = datetime.now(timezone.utc)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (org_id,))
            rows = cur.fetchall()
            invitations = []
            for row in rows:
                expires_at = _as_utc(row[3])
                used_at = _as_utc(row[4])
                revoked_at = _as_utc(row[5])
                status = "pending"
                if revoked_at:
                    status = "revoked"
                elif used_at:
                    status = "used"
                elif expires_at and expires_at <= now:
                    status = "expired"
                invitations.append(
                    {
                        "id": str(row[0]),
                        "email": row[1],
                        "token": row[2],
                        "expires_at": _iso(expires_at),
                        "used_at": _iso(used_at),
                        "revoked_at": _iso(revoked_at),
                        "created_at": _iso(row[6]),
                        "role_code": row[7],
                        "status": status,
                    }
                )
            return invitations
    finally:
        put_conn(conn)


def fetch_invitation_by_token(token: str) -> Optional[Dict[str, Any]]:
    sql = """
        SELECT i.id, i.org_id, o.name, i.email,
               i.expires_at, i.used_at, i.revoked_at,
               i.org_role_id, r.code AS role_code
        FROM org_invitations i
        JOIN organizations o ON o.id = i.org_id
        LEFT JOIN org_roles r ON r.id = i.org_role_id
        WHERE i.token = %s
        LIMIT 1
    """
    now = datetime.now(timezone.utc)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (token,))
            row = cur.fetchone()
            if not row:
                return None
            expires_at = _as_utc(row[4])
            used_at = _as_utc(row[5])
            revoked_at = _as_utc(row[6])
            status = "pending"
            if revoked_at:
                status = "revoked"
            elif used_at:
                status = "used"
            elif expires_at and expires_at <= now:
                status = "expired"
            return {
                "id": str(row[0]),
                "org_id": str(row[1]),
                "org_name": row[2],
                "email": row[3],
                "expires_at": _iso(expires_at),
                "used_at": _iso(used_at),
                "revoked_at": _iso(revoked_at),
                "org_role_id": str(row[7]) if row[7] else None,
                "role_code": row[8],
                "status": status,
            }
    finally:
        put_conn(conn)


def accept_invitation(token: str, user_id: str) -> Dict[str, Any]:
    sql = """
        WITH inv AS (
            SELECT id, org_id, org_role_id
            FROM org_invitations
            WHERE token = %s
              AND revoked_at IS NULL
              AND used_at IS NULL
              AND (expires_at IS NULL OR expires_at > NOW())
            FOR UPDATE
        ), mark AS (
            UPDATE org_invitations
               SET used_at = NOW()
             WHERE id IN (SELECT id FROM inv)
             RETURNING id
        ), upsert_membership AS (
            INSERT INTO user_org_membership (org_id, user_id, org_role_id, joined_at)
            SELECT inv.org_id,
                   %s,
                   COALESCE(inv.org_role_id, (SELECT id FROM org_roles WHERE lower(code) = 'org_user' LIMIT 1)),
                   NOW()
            FROM inv
            ON CONFLICT (org_id, user_id) DO NOTHING
        )
        SELECT o.id, o.name, r.code AS role_code
        FROM inv
        JOIN organizations o ON o.id = inv.org_id
        LEFT JOIN user_org_membership m ON m.org_id = inv.org_id AND m.user_id = %s
        LEFT JOIN org_roles r ON r.id = m.org_role_id
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (token, user_id, user_id))
            row = cur.fetchone()
            if not row:
                raise ValueError("accept_failed")
            conn.commit()
            return {
                "org_id": str(row[0]),
                "org_name": row[1],
                "role_code": row[2],
            }
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)
