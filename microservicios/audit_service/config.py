import os
from pathlib import Path
from dotenv import load_dotenv

def _load_environment() -> None:
    """Carga el .env raíz para compartir configuración."""
    service_dir = Path(__file__).resolve().parent
    # Sube dos niveles (audit_service/ -> microservicios/ -> raíz)
    root_dir = service_dir.parents[1] 
    root_env = root_dir / ".env"
    
    if root_env.exists():
        print(f"[AuditService] Cargando configuración desde {root_env}")
        load_dotenv(root_env, override=False)
    else:
        print(f"[AuditService] ADVERTENCIA: No se encontró {root_env}. Usando valores por defecto.")

_load_environment()

class Settings:
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    
    # Puerto para este servicio (audit_service)
    SERVICE_PORT = int(os.getenv("AUDIT_SERVICE_PORT", "5006"))

    # --- Configuración de Base de Datos (Compartida) ---
    # Lee las variables de BD globales del .env raíz
    
    PGHOST = os.getenv("PGHOST", "127.0.0.1")
    PGPORT = int(os.getenv("PGPORT", "5432"))
    PGDATABASE = os.getenv("PGDATABASE") or os.getenv("DBNAME") or "heartguard"
    PGUSER = os.getenv("PGUSER") or os.getenv("DBUSER") or "heartguard_app"
    PGPASSWORD = os.getenv("PGPASSWORD") or os.getenv("DBPASS") or "dev_change_me"
    
    # El esquema 'heartguard' ya contiene la tabla 'audit_logs'
    PGSCHEMA = os.getenv("PGSCHEMA") or os.getenv("DBSCHEMA") or "heartguard"
    
    DB_POOL_MIN = int(os.getenv("AUDIT_DB_POOL_MIN", "1"))
    DB_POOL_MAX = int(os.getenv("AUDIT_DB_POOL_MAX", "5"))

settings = Settings()