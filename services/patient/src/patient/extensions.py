"""
Extensiones compartidas del servicio
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from .config import get_config

config = get_config()


@contextmanager
def get_db_cursor():
    """
    Context manager para obtener un cursor de base de datos.
    Maneja automáticamente el commit/rollback y el cierre de conexión.
    
    Yields:
        cursor: Cursor de psycopg2 con RealDictCursor
    """
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
