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
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "heartguard")

# PostgreSQL Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "heartguard")
POSTGRES_USER = os.getenv("POSTGRES_USER", "heartguard_app")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "dev_change_me")

# AI Service Configuration
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://134.199.204.58:5008")
AI_PREDICTION_THRESHOLD = float(os.getenv("AI_PREDICTION_THRESHOLD", "0.6"))

# Auth Service Configuration (para obtener JWT)
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8081")
INTERNAL_SERVICE_KEY = os.getenv("INTERNAL_SERVICE_KEY", "dev_internal_key")

# Monitor Configuration
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "60"))  # segundos
LOOKBACK_WINDOW = int(os.getenv("LOOKBACK_WINDOW", "300"))  # 5 minutos
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))  # pacientes por batch

# Notification Configuration
ENABLE_NOTIFICATIONS = os.getenv("ENABLE_NOTIFICATIONS", "true").lower() == "true"
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8083")

# Flask Configuration
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5008"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
