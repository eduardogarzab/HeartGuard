"""Catalog service Flask application factory."""
from __future__ import annotations

from flask import Flask

from .config import CONFIG
from .db import db
from .routes.catalog import catalog_bp


def create_app() -> Flask:
    """Application factory for the catalog service."""

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = CONFIG.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["ENV"] = CONFIG.FLASK_ENV
    app.config["JWT_SECRET"] = CONFIG.JWT_SECRET

    db.init_app(app)

    app.register_blueprint(catalog_bp)

    @app.shell_context_processor
    def _shell_context():
        return {"db": db}

    return app
