"""Database access helpers for patient records."""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from psycopg2.extras import RealDictCursor

from db import get_conn, put_conn


def _as_iso(value: Optional[datetime | date]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _row_to_patient(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(row.get("id")),
        "org_id": str(row.get("org_id")) if row.get("org_id") is not None else None,
        "person_name": row.get("person_name"),
        "birthdate": _as_iso(row.get("birthdate")),
        "sex": {
            "id": str(row.get("sex_id")) if row.get("sex_id") else None,
            "code": row.get("sex_code"),
            "label": row.get("sex_label"),
        },
        "risk_level": {
            "id": str(row.get("risk_level_id")) if row.get("risk_level_id") else None,
            "code": row.get("risk_level_code"),
            "label": row.get("risk_level_label"),
        },
        "profile_photo_url": row.get("profile_photo_url"),
        "created_at": _as_iso(row.get("created_at")),
    }


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


def list_patients(org_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    sql = """
        SELECT p.id,
               p.org_id,
               p.person_name,
               p.birthdate,
               p.sex_id,
               sx.code AS sex_code,
               sx.label AS sex_label,
               p.risk_level_id,
               rl.code AS risk_level_code,
               rl.label AS risk_level_label,
               p.profile_photo_url,
               p.created_at
          FROM patients p
          LEFT JOIN sexes sx ON sx.id = p.sex_id
          LEFT JOIN risk_levels rl ON rl.id = p.risk_level_id
         WHERE p.org_id = %s
         ORDER BY p.created_at DESC, p.person_name ASC
         LIMIT %s OFFSET %s;
    """
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (org_id, limit, offset))
            rows = cur.fetchall()
            return [_row_to_patient(dict(row)) for row in rows]
    finally:
        put_conn(conn)


def get_patient(patient_id: str) -> Optional[Dict[str, Any]]:
    sql = """
        SELECT p.id,
               p.org_id,
               p.person_name,
               p.birthdate,
               p.sex_id,
               sx.code AS sex_code,
               sx.label AS sex_label,
               p.risk_level_id,
               rl.code AS risk_level_code,
               rl.label AS risk_level_label,
               p.profile_photo_url,
               p.created_at
          FROM patients p
          LEFT JOIN sexes sx ON sx.id = p.sex_id
          LEFT JOIN risk_levels rl ON rl.id = p.risk_level_id
         WHERE p.id = %s
         LIMIT 1;
    """
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (patient_id,))
            row = cur.fetchone()
            return _row_to_patient(dict(row)) if row else None
    finally:
        put_conn(conn)


def create_patient(
    org_id: str,
    person_name: str,
    birthdate: Optional[date],
    sex_id: Optional[str],
    risk_level_id: Optional[str],
    profile_photo_url: Optional[str],
) -> str:
    sql = """
        INSERT INTO patients (org_id, person_name, birthdate, sex_id, risk_level_id, profile_photo_url)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    org_id,
                    person_name,
                    birthdate,
                    sex_id,
                    risk_level_id,
                    profile_photo_url,
                ),
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return str(new_id)
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)


def update_patient(
    patient_id: str,
    *,
    person_name: Optional[str] = None,
    birthdate: Optional[date] = None,
    clear_birthdate: bool = False,
    sex_id: Optional[str] = None,
    risk_level_id: Optional[str] = None,
    profile_photo_url: Optional[str] = None,
) -> bool:
    fields: List[str] = []
    values: List[Any] = []

    if person_name is not None:
        fields.append("person_name = %s")
        values.append(person_name)
    if clear_birthdate:
        fields.append("birthdate = NULL")
    elif birthdate is not None:
        fields.append("birthdate = %s")
        values.append(birthdate)
    if sex_id is not None:
        fields.append("sex_id = %s")
        values.append(sex_id)
    if risk_level_id is not None:
        fields.append("risk_level_id = %s")
        values.append(risk_level_id)
    if profile_photo_url is not None:
        fields.append("profile_photo_url = %s")
        values.append(profile_photo_url)

    if not fields:
        return False

    sql = "UPDATE patients SET " + ", ".join(fields) + " WHERE id = %s"
    values.append(patient_id)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(values))
            if cur.rowcount == 0:
                conn.rollback()
                return False
            conn.commit()
            return True
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)


def delete_patient(patient_id: str) -> bool:
    sql = "DELETE FROM patients WHERE id = %s"
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (patient_id,))
            if cur.rowcount == 0:
                conn.rollback()
                return False
            conn.commit()
            return True
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)
