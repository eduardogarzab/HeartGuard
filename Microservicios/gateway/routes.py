"""Gateway service routes providing routing metadata."""
from __future__ import annotations

from typing import List

from flask import Blueprint, request

from common.auth import require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("gateway", __name__)

# Static registry of service routes exposed by the gateway for documentation purposes.
SERVICE_ROUTES = [
    {"service": "auth", "path": "/auth/login", "methods": ["POST"]},
    {"service": "organization", "path": "/organization", "methods": ["GET", "PUT"]},
    {"service": "user", "path": "/users/me", "methods": ["GET", "PATCH"]},
    {"service": "patient", "path": "/patients", "methods": ["GET", "POST"]},
    {"service": "device", "path": "/devices", "methods": ["GET", "POST"]},
    {"service": "media", "path": "/media/upload", "methods": ["POST"]},
    {"service": "alerts", "path": "/alerts", "methods": ["GET", "POST"]},
]


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "gateway", "status": "healthy"})


@bp.route("/routes", methods=["GET"])
def list_routes() -> "Response":
    return render_response({"routes": SERVICE_ROUTES}, meta={"total": len(SERVICE_ROUTES)})


@bp.route("/echo", methods=["POST"])
def echo() -> "Response":
    payload, content_type = parse_request_data(request)
    meta = {"content_type": content_type}
    return render_response({"echo": payload}, status_code=201, meta=meta)


@bp.route("/forward/<service_name>", methods=["GET"])
@require_auth(optional=True)
def forward(service_name: str) -> "Response":
    matching: List[dict] = [route for route in SERVICE_ROUTES if route["service"] == service_name]
    if not matching:
        raise APIError("Unknown service", status_code=404, error_id="HG-GW-UNKNOWN-SERVICE")
    return render_response({"service": service_name, "registered_routes": matching})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/gateway")
