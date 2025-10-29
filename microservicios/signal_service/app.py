"""Entry point for the HeartGuard signal_service."""

import logging
from logging.config import dictConfig

from flask import Flask

from config import settings
from responses import ok


def configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {
                "level": "INFO" if settings.FLASK_ENV != "development" else "DEBUG",
                "handlers": ["console"],
            },
        }
    )


def create_app() -> Flask:
    configure_logging()
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    @app.get("/health")
    def health():
        return ok({"service": "signal_service", "status": "healthy"})

    from routes.signals import bp as signals_bp

    app.register_blueprint(signals_bp)
    return app


if __name__ == "__main__":
    application = create_app()
    application.run(
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        debug=(settings.FLASK_ENV == "development"),
    )
