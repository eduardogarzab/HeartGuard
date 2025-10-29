"""Data access helpers for biometric signals."""

from typing import Any, Dict, List, Optional

from db import connection_scope

_SIGNAL_COLUMNS = [
    "id",
    "patient_id",
    "org_id",
    "signal_type",
    "value",
    "unit",
    "recorded_at",
    "created_by",
    "created_at",
]


def _row_to_signal(row) -> Dict[str, Any]:
    return {key: row[idx] for idx, key in enumerate(_SIGNAL_COLUMNS)}


def create_signal(
    *,
    patient_id: str,
    org_id: str,
    signal_type: str,
    value: float,
    unit: str,
    recorded_at,
    created_by: str,
) -> Dict[str, Any]:
    sql = """
        INSERT INTO signals (patient_id, org_id, signal_type, value, unit, recorded_at, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, patient_id, org_id, signal_type, value, unit, recorded_at, created_by, created_at;
    """
    with connection_scope() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    sql,
                    (patient_id, org_id, signal_type, value, unit, recorded_at, created_by),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            row = cur.fetchone()
            return _row_to_signal(row)


def list_signals_for_patient(
    *, patient_id: str, org_id: str, limit: Optional[int] = None, offset: int = 0
) -> List[Dict[str, Any]]:
    sql = """
        SELECT id, patient_id, org_id, signal_type, value, unit, recorded_at, created_by, created_at
          FROM signals
         WHERE patient_id = %s
           AND org_id = %s
         ORDER BY recorded_at DESC NULLS LAST, created_at DESC
         LIMIT %s OFFSET %s;
    """
    lim = limit if limit is not None else 100
    with connection_scope() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (patient_id, org_id, lim, offset))
            rows = cur.fetchall() or []
            return [_row_to_signal(row) for row in rows]


def get_signal_by_id(*, signal_id: str, org_id: str) -> Optional[Dict[str, Any]]:
    sql = """
        SELECT id, patient_id, org_id, signal_type, value, unit, recorded_at, created_by, created_at
          FROM signals
         WHERE id = %s
           AND org_id = %s
         LIMIT 1;
    """
    with connection_scope() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (signal_id, org_id))
            row = cur.fetchone()
            return _row_to_signal(row) if row else None


def delete_signal(*, signal_id: str, org_id: str) -> bool:
    sql = """
        DELETE FROM signals
         WHERE id = %s
           AND org_id = %s;
    """
    with connection_scope() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(sql, (signal_id, org_id))
                deleted = cur.rowcount > 0
                if deleted:
                    conn.commit()
                else:
                    conn.rollback()
                return deleted
            except Exception:
                conn.rollback()
                raise
