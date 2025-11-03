"""Flask extensions registry."""

from __future__ import annotations

from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
cors = CORS(resources={r"/admin-api/*": {"origins": "*"}})


__all__ = ["db", "cors"]
