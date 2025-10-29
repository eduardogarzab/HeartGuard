"""Application factory for the signal service."""

import logging

from flask import Flask

from config import settings
from responses import ok
from routes.signals import bp as signals_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    _configure_logging(app)

    @app.get("/health")
    def health():
        return ok({"service": "signal_service", "status": "healthy"})

    app.register_blueprint(signals_bp)

    return app


def _configure_logging(app: Flask) -> None:
    log_level = logging.DEBUG if settings.FLASK_ENV == "development" else logging.INFO
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    handler.setFormatter(formatter)

    app.logger.setLevel(log_level)
    if not app.logger.handlers:
        app.logger.addHandler(handler)


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=settings.SERVICE_PORT, debug=settings.FLASK_ENV == "development")
