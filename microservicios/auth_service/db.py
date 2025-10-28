import psycopg2
import psycopg2.pool
from config import settings


def _build_pool() -> psycopg2.pool.SimpleConnectionPool:
    minconn = settings.DB_POOL_MIN
    maxconn = settings.DB_POOL_MAX
    if settings.DATABASE_URL:
        return psycopg2.pool.SimpleConnectionPool(minconn, maxconn, settings.DATABASE_URL)
    return psycopg2.pool.SimpleConnectionPool(
        minconn,
        maxconn,
        host=settings.PGHOST,
        port=settings.PGPORT,
        dbname=settings.PGDATABASE,
        user=settings.PGUSER,
        password=settings.PGPASSWORD,
    )


pool = _build_pool()

def get_conn():
    conn = pool.getconn()
    # Garantiza que las consultas utilicen el schema esperado
    with conn.cursor() as cur:
        cur.execute("SET search_path TO %s, public;", (settings.PGSCHEMA,))
    return conn

def put_conn(conn):
    pool.putconn(conn)
