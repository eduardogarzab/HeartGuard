"""
AI Monitor Service - Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# InfluxDB Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "heartguard")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "timeseries")

# PostgreSQL Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "heartguard")
POSTGRES_USER = os.getenv("POSTGRES_USER", "heartguard_app")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "dev_change_me")

# AI Service Configuration
# ai-prediction corre en el mismo servidor de microservicios, puerto 5007
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:5007")
AI_PREDICTION_THRESHOLD = float(os.getenv("AI_PREDICTION_THRESHOLD", "0.6"))

# AI Model Configuration
# UUID del modelo RandomForest en PostgreSQL
AI_MODEL_ID = os.getenv("AI_MODEL_ID", "988e1fee-e18e-4eb9-9b9d-72ae7d48d8bc")

# Internal Service Authentication
# Clave compartida para comunicación entre microservicios
INTERNAL_SERVICE_KEY = os.getenv("INTERNAL_SERVICE_KEY", "dev_internal_key")

# Monitor Configuration
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "60"))  # segundos
LOOKBACK_WINDOW = int(os.getenv("LOOKBACK_WINDOW", "300"))  # 5 minutos
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))  # pacientes por batch

# Flask Configuration
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5008"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
