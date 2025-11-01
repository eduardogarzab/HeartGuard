"""Gateway service routes implementing a reverse proxy."""
from __future__ import annotations

import os

import requests
from flask import Blueprint, Response, g, request

from common.errors import APIError

bp = Blueprint("gateway", __name__)

SERVICE_MAP = {
    "auth": {
        "url": f"http://auth_service:{os.getenv('AUTH_PORT', 5001)}",
        "prefix": "/auth"
    },
    "organization": {
        "url": f"http://organization_service:{os.getenv('ORGANIZATION_PORT', 5002)}",
        "prefix": "/organization"
    },
    "user": {
        "url": f"http://user_service:{os.getenv('USER_PORT', 5003)}",
        "prefix": "/users"
    },
    "users": {
        "url": f"http://user_service:{os.getenv('USER_PORT', 5003)}",
        "prefix": "/users"
    },
    "patient": {
        "url": f"http://patient_service:{os.getenv('PATIENT_PORT', 5004)}",
        "prefix": "/patients"
    },
    "patients": {
        "url": f"http://patient_service:{os.getenv('PATIENT_PORT', 5004)}",
        "prefix": "/patients"
    },
    "device": {
        "url": f"http://device_service:{os.getenv('DEVICE_PORT', 5005)}",
        "prefix": "/devices"
    },
    "devices": {
        "url": f"http://device_service:{os.getenv('DEVICE_PORT', 5005)}",
        "prefix": "/devices"
    },
    "influx": {
        "url": f"http://influx_service:{os.getenv('INFLUX_SERVICE_PORT', 5006)}",
        "prefix": "/influx"
    },
    "inference": {
        "url": f"http://inference_service:{os.getenv('INFERENCE_PORT', 5007)}",
        "prefix": "/inference"
    },
    "alert": {
        "url": f"http://alert_service:{os.getenv('ALERT_PORT', 5008)}",
        "prefix": "/alerts"
    },
    "alerts": {
        "url": f"http://alert_service:{os.getenv('ALERT_PORT', 5008)}",
        "prefix": "/alerts"
    },
    "notification": {
        "url": f"http://notification_service:{os.getenv('NOTIFICATION_PORT', 5009)}",
        "prefix": "/notifications"
    },
    "notifications": {
        "url": f"http://notification_service:{os.getenv('NOTIFICATION_PORT', 5009)}",
        "prefix": "/notifications"
    },
    "media": {
        "url": f"http://media_service:{os.getenv('MEDIA_PORT', 5010)}",
        "prefix": "/media"
    },
    "audit": {
        "url": f"http://audit_service:{os.getenv('AUDIT_PORT', 5011)}",
        "prefix": "/audit"
    },
}


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return {"service": "gateway", "status": "healthy"}


@bp.route('/<service_name>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], defaults={'path': ''})
@bp.route('/<service_name>/<path:path>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def proxy(service_name: str, path: str = "") -> Response:
    """Generic reverse proxy to internal services."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Proxy called: service_name={service_name}, path={path}")
    
    service_config = SERVICE_MAP.get(service_name)
    if not service_config:
        raise APIError("Unknown service", status_code=404, error_id="HG-GW-UNKNOWN-SERVICE")

    service_url = service_config["url"]
    service_prefix = service_config["prefix"]

    req_id = request.headers.get("X-Request-ID") or g.request_id
    proxied_headers = {
        "Authorization": request.headers.get("Authorization"),
        "X-Request-ID": req_id,
        "Content-Type": request.headers.get("Content-Type", "application/json"),
        "Accept": request.headers.get("Accept", "application/json"),
    }

    try:
        # Build target URL: service_url + service_prefix + path
        if path:
            target_url = f"{service_url}{service_prefix}/{path}"
        else:
            target_url = f"{service_url}{service_prefix}"
        
        if request.query_string:
            target_url += f"?{request.query_string.decode('utf-8')}"

        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={k: v for k, v in proxied_headers.items() if v is not None},
            json=request.get_json(silent=True),
            data=request.get_data() if not request.is_json else None,
            timeout=10,
        )

        response = Response(resp.content, resp.status_code, resp.headers.items())

        for header in ['Content-Encoding', 'Transfer-Encoding', 'Connection']:
            if header in response.headers:
                del response.headers[header]

        return response

    except requests.exceptions.ConnectionError as exc:
        raise APIError("Service unavailable", status_code=503, error_id="HG-GW-SERVICE-UNAVAILABLE") from exc
    except requests.exceptions.Timeout as exc:
        raise APIError("Service timed out", status_code=504, error_id="HG-GW-SERVICE-TIMEOUT") from exc


def register_blueprint(app):
    """Register the gateway blueprint."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Registering gateway blueprint with url_prefix='/'")
    app.register_blueprint(bp, url_prefix="/")
