"""Flask application entrypoint for Admin Service."""
from __future__ import annotations

from flask import Flask
from flask_cors import CORS

from .config import configure_app
from .routes import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__)
    configure_app(app)
    
    # Enable CORS for all routes
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })
    
    register_blueprints(app)
    return app


app = create_app()
