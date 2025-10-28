import os
from pathlib import Path
from dotenv import load_dotenv

def _load_environment() -> None:
    """Carga el .env raíz para compartir configuración."""
    service_dir = Path(__file__).resolve().parent
    # Sube dos niveles (gateway/ -> microservicios/ -> raíz)
    root_dir = service_dir.parents[1] 
    root_env = root_dir / ".env"
    
    if root_env.exists():
        print(f"[Gateway] Cargando configuración desde {root_env}")
        load_dotenv(root_env, override=False)
    else:
        print(f"[Gateway] ADVERTENCIA: No se encontró {root_env}. Usando valores por defecto.")

_load_environment()

class Config:
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    
    # Puerto para este servicio (gateway)
    SERVICE_PORT = int(os.getenv("GATEWAY_SERVICE_PORT", "5000"))

    # Clave secreta para JWT.
    # Lee la *misma* variable que usa auth_service
    JWT_SECRET_KEY = os.getenv("AUTH_JWT_SECRET") or os.getenv("JWT_SECRET", "change_me")
    JWT_ALGORITHM = "HS256"

    # URLs de los microservicios internos (deben estar en tu .env raíz)
    # Los valores por defecto (5001, 5002) los tomo de tu start_microservices.sh
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:5001")
    ORG_SERVICE_URL = os.getenv("ORG_SERVICE_URL", "http://127.0.0.1:5002")
    
    # Agrega aquí las URLs de los nuevos servicios cuando los crees
    # SIGNAL_SERVICE_URL = os.getenv("SIGNAL_SERVICE_URL", "http://127.0.0.1:5003")
    # INFERENCE_SERVICE_URL = os.getenv("INFERENCE_SERVICE_URL", "http://127.0.0.1:5004")
    # ALERT_SERVICE_URL = os.getenv("ALERT_SERVICE_URL", "http://127.0.0.1:5005")
    # AUDIT_SERVICE_URL = os.getenv("AUDIT_SERVICE_URL", "http://127.0.0.1:5006")
    # ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://127.0.0.1:5007")