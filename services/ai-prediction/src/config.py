"""
Configuración del servicio de IA
"""
import os
from pathlib import Path

# Directorios
BASE_DIR = Path(__file__).parent.parent
MODEL_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Modelo
MODEL_FILENAME = "modelo_salud_randomforest.pkl"
MODEL_PATH = MODEL_DIR / MODEL_FILENAME
DEFAULT_THRESHOLD = float(os.getenv("PREDICTION_THRESHOLD", "0.6"))

# Flask
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5007"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

# Internal Service Authentication
INTERNAL_SERVICE_KEY = os.getenv("INTERNAL_SERVICE_KEY", "dev_internal_key")

# Features del modelo (orden IMPORTANTE - debe coincidir con el entrenamiento)
MODEL_FEATURES = [
    "GPS_longitude",
    "GPS_latitude",
    "Heart Rate (bpm)",
    "SpO2 Level (%)",
    "Systolic Blood Pressure (mmHg)",
    "Diastolic Blood Pressure (mmHg)",
    "Body Temperature (°C)"
]

# Mapeo de nombres de API a features del modelo
API_TO_MODEL_MAPPING = {
    "gps_longitude": "GPS_longitude",
    "gps_latitude": "GPS_latitude",
    "heart_rate": "Heart Rate (bpm)",
    "spo2": "SpO2 Level (%)",
    "systolic_bp": "Systolic Blood Pressure (mmHg)",
    "diastolic_bp": "Diastolic Blood Pressure (mmHg)",
    "temperature": "Body Temperature (°C)"
}

# Niveles de severidad basados en probabilidad
SEVERITY_LEVELS = {
    "low": (0.0, 0.3),      # 0-30% probabilidad de problema
    "medium": (0.3, 0.6),   # 30-60%
    "high": (0.6, 1.0)      # 60-100%
}

# Tipos de alertas (basadas en análisis de features)
ALERT_TYPES = {
    "GENERAL_RISK": "Riesgo general detectado por el modelo",
    "ARRHYTHMIA": "Posible arritmia cardíaca",
    "DESAT": "Posible desaturación de oxígeno",
    "HYPERTENSION": "Posible hipertensión",
    "HYPOTENSION": "Posible hipotensión",
    "FEVER": "Posible fiebre",
    "HYPOTHERMIA": "Posible hipotermia"
}
