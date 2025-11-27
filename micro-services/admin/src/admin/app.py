"""Flask application entrypoint for Admin Service."""
from __future__ import annotations

from flask import Flask

from .config import configure_app
from .routes import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__)
    configure_app(app)
    register_blueprints(app)
    return app


app = create_app()
