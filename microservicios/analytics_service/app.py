"""Aplicación Flask para el servicio de analytics."""
from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Flask, g, request

from config import db_engine, settings
from models import Base
from routes import register_blueprints

try:  # pragma: no cover - dependencia compartida
    from shared_lib.flask.responses import create_response  # type: ignore
except Exception:  # pragma: no cover
    try:
        from shared_lib.responses import create_response  # type: ignore
    except Exception:  # pragma: no cover
        from flask import jsonify

        def create_response(
            payload: Dict[str, Any],
            status_code: int = 200,
            headers: Optional[Dict[str, Any]] = None,
        ):
            response = jsonify(payload)
            response.status_code = status_code
            if headers:
                for key, value in headers.items():
                    response.headers[key] = value
            return response


app = Flask(__name__)
app.config["SERVICE_NAME"] = "analytics_service"
app.config["ENV"] = settings.FLASK_ENV


if db_engine is not None:
    Base.metadata.create_all(bind=db_engine)


@app.before_request
def enrich_context() -> None:
    """Asegura que ``g`` contenga los metadatos esperados por los reportes."""

    if getattr(g, "org_id", None) is None:
        org_header = request.headers.get("X-Org-ID") or request.headers.get("X-Org-Id")
        if org_header:
            try:
                g.org_id = int(org_header)
            except ValueError:
                g.org_id = org_header

    if getattr(g, "role", None) is None:
        g.role = request.headers.get("X-Role") or request.headers.get("X-User-Role")

    if getattr(g, "user_id", None) is None:
        g.user_id = request.headers.get("X-User-Id") or request.headers.get("X-User-ID")


@app.after_request
def attach_headers(response):
    response.headers.setdefault("X-Service", "analytics_service")
    return response


register_blueprints(app)


@app.get("/health")
def healthcheck():
    return create_response({"status": "ok", "service": "analytics_service"})


if __name__ == "__main__":
    debug = settings.FLASK_ENV == "development"
    app.run(host="0.0.0.0", port=settings.SERVICE_PORT, debug=debug)
