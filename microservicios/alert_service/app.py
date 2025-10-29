import logging
from typing import Optional

from flask import Flask

from .config import Config
from .db import db
from .routes import alerts_bp


def create_app(config_object: Optional[type] = None) -> Flask:
    app = Flask(__name__)
    cfg = config_object or Config
    app.config.from_object(cfg)

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL is not configured")

    logging.basicConfig(level=logging.INFO)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(alerts_bp)

    @app.route("/health", methods=["GET"])
    def health() -> str:
        return "OK"

    return app


app: Optional[Flask]
try:
    app = create_app()
except RuntimeError:
    app = None
