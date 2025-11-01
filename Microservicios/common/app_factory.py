"""Application factory utilities for microservices."""
from __future__ import annotations

import importlib
import logging
import os
import time
from typing import Callable

from flask import Flask, Response, g, request

_cors_spec = importlib.util.find_spec("flask_cors")
if _cors_spec is not None:
    CORS = importlib.import_module("flask_cors").CORS  # type: ignore[attr-defined]
else:  # pragma: no cover - exercised implicitly when dependency missing
    def CORS(app, *args, **kwargs):  # type: ignore[empty-body]
        return app

from .database import db, DB_AVAILABLE
from .errors import register_error_handlers
from .serialization import render_response


def _configure_logging(service_name: str) -> logging.Logger:
    logger = logging.getLogger(service_name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    logger.propagate = False
    return logger


def create_app(service_name: str, register_blueprint: Callable[[Flask], None]) -> Flask:
    app = Flask(service_name)
    logger = _configure_logging(service_name)

    # Only configure database if SQLAlchemy is available and DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if DB_AVAILABLE and database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)
        logger.info("Database initialized with SQLAlchemy for %s", service_name)
    else:
        if not DB_AVAILABLE:
            logger.info("SQLAlchemy not available - service %s running without database", service_name)
        elif not database_url:
            logger.info("DATABASE_URL not set - service %s running without database", service_name)

    allowed_origins = os.getenv("ALLOWED_ORIGINS")
    if allowed_origins:
        origins = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]
    else:
        origins = "*"
    CORS(app, resources={r"/*": {"origins": origins}})

    @app.before_request
    def _before_request():
        g.start_time = time.time()
        g.request_id = request.headers.get("X-Request-ID") or os.urandom(8).hex()
        g.logger = logger
        g.db = db if DB_AVAILABLE else None

    @app.after_request
    def _after_request(response: Response):
        duration = time.time() - g.get("start_time", time.time())
        logger.info("request_completed request_id=%s method=%s path=%s status=%s duration_ms=%s",
                    g.get("request_id"), request.method, request.path, response.status_code, int(duration * 1000))
        response.headers["X-Request-ID"] = g.get("request_id")
        return response

    @app.route("/health")
    def health_check():
        return render_response({"service": service_name, "status": "healthy"})

    register_blueprint(app)
    register_error_handlers(app)
    return app
