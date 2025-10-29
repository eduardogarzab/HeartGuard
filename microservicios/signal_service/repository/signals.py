"""Data access helpers for patient biomedical signals."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from db import get_conn, put_conn

SignalRecord = Dict[str, Any]

FIELDS = (
    "id",
    "patient_id",
    "org_id",
    "signal_type",
    "value",
    "unit",
    "recorded_at",
    "created_by",
    "created_at",
)


def _row_to_dict(row) -> SignalRecord:
    return {
        field: (str(value) if field in {"id", "patient_id", "org_id", "created_by"} and value is not None else value)
        for field, value in zip(FIELDS, row)
    }


def create_signal(
    *,
    patient_id: str,
    org_id: str,
    signal_type: str,
    value: float,
    unit: str,
    recorded_at,
    created_by: str,
) -> SignalRecord:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO signals (patient_id, org_id, signal_type, value, unit, recorded_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, patient_id, org_id, signal_type, value, unit, recorded_at, created_by, created_at
                """,
                (patient_id, org_id, signal_type, value, unit, recorded_at, created_by),
            )
            row = cur.fetchone()
        conn.commit()
        if not row:
            raise RuntimeError("No se pudo registrar la señal")
        return _row_to_dict(row)
    finally:
        put_conn(conn)


def list_signals(*, patient_id: str, org_id: str, limit: int = 100, offset: int = 0) -> List[SignalRecord]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, patient_id, org_id, signal_type, value, unit, recorded_at, created_by, created_at
                FROM signals
                WHERE patient_id = %s AND org_id = %s
                ORDER BY recorded_at DESC, created_at DESC
                LIMIT %s OFFSET %s
                """,
                (patient_id, org_id, limit, offset),
            )
            rows = cur.fetchall() or []
        return [_row_to_dict(row) for row in rows]
    finally:
        put_conn(conn)


def get_signal(signal_id: str, org_id: str) -> Optional[SignalRecord]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, patient_id, org_id, signal_type, value, unit, recorded_at, created_by, created_at
                FROM signals
                WHERE id = %s AND org_id = %s
                LIMIT 1
                """,
                (signal_id, org_id),
            )
            row = cur.fetchone()
            return _row_to_dict(row) if row else None
    finally:
        put_conn(conn)


def delete_signal(signal_id: str, org_id: str) -> bool:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM signals WHERE id = %s AND org_id = %s",
                (signal_id, org_id),
            )
            deleted = cur.rowcount
        conn.commit()
        return deleted > 0
    finally:
        put_conn(conn)
