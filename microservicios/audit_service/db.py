import psycopg2.pool
from psycopg2.extras import RealDictCursor
from flask import g
from config import settings

pool = None

def init_db():
    global pool
    print(f"[AuditService] Creando pool de conexiones a {settings.PGHOST}:{settings.PGPORT}...")
    pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=settings.DB_POOL_MIN,
        maxconn=settings.DB_POOL_MAX,
        host=settings.PGHOST,
        port=settings.PGPORT,
        dbname=settings.PGDATABASE,
        user=settings.PGUSER,
        password=settings.PGPASSWORD,
        options=f"-c search_path={settings.PGSCHEMA}",
        cursor_factory=RealDictCursor
    )

def get_db():
    if 'db_conn' not in g or g.db_conn.closed:
        if pool is None:
            init_db()
        g.db_conn = pool.getconn()
    return g.db_conn

def close_db(e=None):
    db_conn = g.pop('db_conn', None)
    if db_conn is not None and not db_conn.closed:
        pool.putconn(db_conn)

def init_app(app):
    app.teardown_appcontext(close_db)