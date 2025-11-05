"""
Extensiones compartidas del servicio User
"""
import logging
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from .config import get_config

config = get_config()
logger = logging.getLogger('user-service')
logging.basicConfig(level=getattr(logging, str(config.LOG_LEVEL).upper(), logging.INFO))


@contextmanager
def get_db_cursor():
    """
    Context manager para obtener un cursor de base de datos.
    Gestiona commit/rollback y cierre de recursos.
    """
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        conn.commit()
    except Exception as exc:
        if conn:
            conn.rollback()
        logger.exception('Database operation failed', exc_info=exc)
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
