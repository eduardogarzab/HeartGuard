"""Configuration for Generator Service."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Database
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgres://heartguard_app:dev_change_me@134.199.204.58:5432/heartguard?sslmode=disable'
    )
    
    # InfluxDB
    INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://134.199.204.58:8086')
    INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', 'heartguard-dev-token-change-me')
    INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'heartguard')
    INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'timeseries')
    
    # Generator settings
    GENERATION_INTERVAL = int(os.getenv('GENERATION_INTERVAL', '5'))
    
    # Flask
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'


def configure_app(app):
    """Configure Flask app."""
    app.config.from_object(Config)
