"""Gestión centralizada de extensiones para Auth Service."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from flask import current_app

_DB_POOL: SimpleConnectionPool | None = None
logger = logging.getLogger("auth-service")


def init_extensions(app) -> None:
    """Inicializa recursos compartidos (pool, logging)."""
    global _DB_POOL

    logging.basicConfig(level=getattr(logging, app.config.get("LOG_LEVEL", "INFO"), logging.INFO))

    if app.config.get("SKIP_DB_INIT"):
        logger.warning("SKIP_DB_INIT habilitado, no se inicializa conexión a base de datos")
        app.extensions["db_pool"] = None
        return

    dsn = app.config["DATABASE_URL"]
    minconn = int(app.config.get("DB_POOL_MIN", 1))
    maxconn = int(app.config.get("DB_POOL_MAX", 10))

    _DB_POOL = SimpleConnectionPool(minconn, maxconn, dsn=dsn)

    @app.teardown_appcontext
    def _close_pool(exception) -> None:  # type: ignore[override]
        if exception:
            logger.error("App context closed with exception", exc_info=exception)
        # Las conexiones se regresan mediante el contextmanager; el pool se cierra al apagar la app.

    app.extensions["db_pool"] = _DB_POOL


@contextmanager
def get_db_cursor(commit: bool = False) -> Generator[RealDictCursor, None, None]:
    """Entrega un cursor de la pool y asegura su devolución."""
    if _DB_POOL is None:
        raise RuntimeError("Database pool no inicializado")

    conn = _DB_POOL.getconn()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            cursor.close()
        except Exception:  # pragma: no cover - cierre defensivo
            pass
        _DB_POOL.putconn(conn)


def get_db_connection():
    """Retorna una conexión cruda (avoid usar fuera de tests)."""
    if _DB_POOL is None:
        raise RuntimeError("Database pool no inicializado")
    return _DB_POOL.getconn()


def close_all() -> None:
    """Cierra el pool (para tests o shutdowns controlados)."""
    if _DB_POOL:
        _DB_POOL.closeall()