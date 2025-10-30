"""Application factory utilities for microservices."""
from __future__ import annotations

import logging
import os
import time
from typing import Callable

from flask import Flask, Response, g, request
from flask_cors import CORS

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
