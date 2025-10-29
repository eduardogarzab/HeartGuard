"""Application factory for the analytics service."""

from __future__ import annotations

from flask import Flask

from config import engine, settings
from models import Base
from routes.ingest import bp as ingest_bp
from routes.reports import bp as reports_bp
from utils import create_response


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        ENV=settings.FLASK_ENV,
        JSON_SORT_KEYS=False,
    )

    # Ensure tables exist when running the service standalone.
    Base.metadata.create_all(bind=engine)

    @app.get("/health")
    def healthcheck():
        return create_response({"service": "analytics_service", "status": "healthy"})

    app.register_blueprint(reports_bp)
    app.register_blueprint(ingest_bp)
    return app


if __name__ == "__main__":
    service = create_app()
    service.run(host="0.0.0.0", port=settings.SERVICE_PORT, debug=settings.FLASK_ENV == "development")
