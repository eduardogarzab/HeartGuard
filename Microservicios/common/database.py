"""Shared database instance for microservices."""
from __future__ import annotations

try:
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()
    DB_AVAILABLE = True
except ImportError:
    # SQLAlchemy not installed - services without DB dependencies can still work
    db = None
    DB_AVAILABLE = False
