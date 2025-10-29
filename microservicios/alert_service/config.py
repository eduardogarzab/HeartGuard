import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.getenv("JWT_SECRET", "")
    AUDIT_SERVICE_URL = os.getenv("AUDIT_SERVICE_URL", "")
    ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "")
