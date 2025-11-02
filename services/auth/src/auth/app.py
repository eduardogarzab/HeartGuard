"""Aplicación Flask para Auth Service."""
from __future__ import annotations

from flask import Flask

from .config import configure_app
from .extensions import init_extensions
from .errors import register_error_handlers
from .blueprints import register_blueprints


def create_app() -> Flask:
    """Crea y configura la instancia principal de Flask."""
    app = Flask(__name__)

    configure_app(app)
    init_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)

    return app
