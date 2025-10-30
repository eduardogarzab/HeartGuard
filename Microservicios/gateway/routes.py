"""Gateway service routes providing proxy capabilities."""
from __future__ import annotations

import os
from urllib.parse import urljoin

import requests
from flask import Blueprint, Response, g, request

from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("gateway", __name__)

SERVICE_MAP = {
    "auth": "http://auth_service:5001/auth/",
    "organization": "http://organization_service:5002/organization/",
    "user": "http://user_service:5003/users/",
    "patient": "http://patient_service:5004/patients/",
    "device": "http://device_service:5005/devices/",
    "influx": "http://influx_service:5006/influx/",
    "inference": "http://inference_service:5007/inference/",
    "alerts": "http://alert_service:5008/alerts/",
    "notifications": "http://notification_service:5009/notifications/",
    "media": "http://media_service:5010/media/",
    "audit": "http://audit_service:5011/audit/",
}


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "gateway", "status": "healthy", "routes": len(SERVICE_MAP)})


@bp.route("/routes", methods=["GET"])
def list_routes() -> "Response":
    routes = [
        {"service": name, "base_url": url.rstrip("/")}
        for name, url in SERVICE_MAP.items()
    ]
    return render_response({"routes": routes}, meta={"total": len(routes)})


@bp.route("/echo", methods=["POST"])
def echo() -> "Response":
    payload, content_type = parse_request_data(request)
    meta = {"content_type": content_type}
    return render_response({"echo": payload}, status_code=201, meta=meta)


@bp.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def proxy(path: str):
    service_key, _, remainder = path.partition("/")
    target_base = SERVICE_MAP.get(service_key)
    if not target_base:
        raise APIError("Unknown service", status_code=404, error_id="HG-GW-UNKNOWN-SERVICE")
    target_url = urljoin(target_base, remainder)

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }
    request_id = request.headers.get("X-Request-ID") or getattr(g, "request_id", None)
    if request_id:
        headers["X-Request-ID"] = request_id

    data = request.get_data()
    params = request.args

    response = requests.request(
        method=request.method,
        url=target_url,
        headers=headers,
        params=params,
        data=data,
        cookies=request.cookies,
        allow_redirects=False,
        timeout=int(os.getenv("GATEWAY_TIMEOUT_SECONDS", "15")),
    )

    proxy_response = Response(
        response.content,
        status=response.status_code,
        headers={k: v for k, v in response.headers.items() if k.lower() != "content-length"},
    )
    proxy_response.headers["X-Request-ID"] = headers.get("X-Request-ID", "")
    return proxy_response


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/gateway")
