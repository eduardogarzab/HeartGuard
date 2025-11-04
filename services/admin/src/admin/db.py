"""Database helper utilities."""
from __future__ import annotations

import contextlib
from typing import Iterator

import psycopg2
import psycopg2.extras
from flask import current_app


@contextlib.contextmanager
def get_connection() -> Iterator[psycopg2.extensions.connection]:
    """Yield a database connection with autocommit enabled."""
    conn = psycopg2.connect(current_app.config["DATABASE_URL"])
    conn.autocommit = False
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(query: str, params: tuple | dict | None = None) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]


def fetch_one(query: str, params: tuple | dict | None = None) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None


def execute(query: str, params: tuple | dict | None = None) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
