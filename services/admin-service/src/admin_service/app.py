"""Application factory for the admin service."""

from __future__ import annotations

from flask import Flask

from .config import get_config
from .extensions import cors, db
from .blueprints.admin_api import admin_api_bp
from .blueprints.health import health_bp
from .errors import register_error_handlers


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure a Flask application instance."""
    app = Flask(__name__)
    config_object = get_config(config_name)
    app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)

    return app


def register_extensions(app: Flask) -> None:
    """Initialize Flask extensions."""
    db.init_app(app)
    cors.init_app(app)


def register_blueprints(app: Flask) -> None:
    """Register application blueprints."""
    app.register_blueprint(health_bp)
    app.register_blueprint(admin_api_bp, url_prefix="/admin-api")


__all__ = ["create_app"]
