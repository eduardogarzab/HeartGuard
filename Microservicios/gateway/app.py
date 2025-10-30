import os
from typing import Any, Dict, Optional

import requests
from flask import Flask, g, request
import jwt

from .error_handler import register_error_handlers
from .middleware import get_metrics, init_app
from .rate_limit import check_rate_limit
from .rbac import check_access
from .utils_format import error_response, make_response, parse_body

app = Flask(__name__)

init_app(app)
register_error_handlers(app)

JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret")
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
SERVICE_URLS = {
    "auth": os.getenv("AUTH_URL", "http://auth:5001"),
    "organization": os.getenv("ORG_URL", "http://organization:5002"),
    "user": os.getenv("USER_URL", "http://user:5003"),
    "media": os.getenv("MEDIA_URL", "http://media:5004"),
    "timeseries": os.getenv("INFLUX_URL", "http://timeseries:5005"),
    "audit": os.getenv("AUDIT_URL", "http://audit:5006"),
}


@app.before_request
def enforce_cors_and_rate_limits():
    if request.method == "OPTIONS":
        return _options_response()
    origin = request.headers.get("Origin")
    if origin and origin not in ALLOWED_ORIGINS and "*" not in ALLOWED_ORIGINS:
        return error_response(403, "Origin not allowed")
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    if not check_rate_limit(client_ip, request.path):
        return error_response(429, "Rate limit exceeded")


def _options_response():
    resp = make_response({"status": "ok"}, status=204)
    return resp


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin and (origin in ALLOWED_ORIGINS or "*" in ALLOWED_ORIGINS):
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Headers"] = "Authorization,Content-Type,Accept,X-Request-ID"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers.setdefault("Vary", "Origin")
    return response


def _decode_jwt(required: bool = True) -> Optional[Dict[str, Any]]:
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        if required:
            raise PermissionError("Missing bearer token")
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        g.user_id = payload.get("sub")
        g.user_role = payload.get("role")
        g.org_id = payload.get("org_id")
        return payload
    except jwt.ExpiredSignatureError:
        raise PermissionError("Token expired")
    except jwt.InvalidTokenError:
        raise PermissionError("Invalid token")


def _authorized(path: str, required: bool = True, extra_context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    payload = _decode_jwt(required=required)
    if not payload:
        return None
    allowed = check_access(payload.get("role"), path, payload.get("sub"), payload.get("org_id"), extra_context)
    if not allowed:
        raise PermissionError("Forbidden")
    return payload


def _permission_error_response(exc: PermissionError):
    message = str(exc)
    status = 403
    lowered = message.lower()
    if any(keyword in lowered for keyword in ["missing", "expired", "invalid", "bearer"]):
        status = 401
    return error_response(status, message)


def _proxy_request(method: str, service: str, endpoint: str, *, json_body: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, files: Any = None, data: Any = None, headers: Optional[Dict[str, str]] = None):
    base_url = SERVICE_URLS[service]
    url = f"{base_url}{endpoint}"
    outbound_headers = {
        "Accept": "application/json",
        "X-Request-ID": getattr(g, "request_id", ""),
    }
    if g.get("user_id"):
        outbound_headers["X-User-ID"] = str(g.user_id)
    if g.get("user_role"):
        outbound_headers["X-User-Role"] = str(g.user_role)
    if g.get("org_id"):
        outbound_headers["X-Org-ID"] = str(g.org_id)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        outbound_headers["Authorization"] = auth_header
    if headers:
        outbound_headers.update(headers)
    if json_body is not None:
        outbound_headers.setdefault("Content-Type", "application/json")

    try:
        response = requests.request(
            method,
            url,
            json=json_body,
            params=params,
            files=files,
            data=data,
            headers=outbound_headers,
            timeout=15,
        )
    except requests.RequestException as exc:
        return error_response(502, f"Downstream {service} service unavailable", {"error": str(exc)})

    return _format_downstream_response(response)


def _format_downstream_response(response: requests.Response):
    content_type = response.headers.get("Content-Type", "application/json")
    status = response.status_code
    try:
        if "application/json" in content_type:
            payload = response.json()
            body = payload
            root_tag = "response"
        elif "application/xml" in content_type:
            import xmltodict

            parsed = xmltodict.parse(response.text)
            payload = dict(parsed)
            if isinstance(payload, dict) and len(payload) == 1:
                root_tag = next(iter(payload.keys()))
                body = payload[root_tag]
            else:
                root_tag = "response"
                body = payload
        else:
            body = {"raw": response.text}
            root_tag = "response"
    except Exception as exc:  # pragma: no cover - fallback
        body = {"raw": response.text, "error": str(exc)}
        root_tag = "response"
    if not isinstance(body, dict):
        body = {"data": body}
    return make_response(body, status=status, root_tag=root_tag)


@app.route("/health", methods=["GET"])
@app.route("/gateway/health", methods=["GET"])
def health():
    return make_response({"status": "ok", "service": "gateway"})


@app.route("/ready", methods=["GET"])
@app.route("/gateway/ready", methods=["GET"])
def ready():
    dependencies = {}
    from .rate_limit import get_client  # local import to avoid circular

    try:
        get_client().ping()
        dependencies["redis"] = True
    except Exception as exc:  # pragma: no cover - runtime env
        dependencies["redis"] = str(exc)
    healthy = all(v is True for v in dependencies.values())
    status = 200 if healthy else 503
    return make_response({"status": "ready" if healthy else "degraded", "dependencies": dependencies}, status=status)


@app.route("/metrics", methods=["GET"])
@app.route("/gateway/metrics", methods=["GET"])
def metrics():
    return make_response(get_metrics(), root_tag="Metrics")


@app.route("/auth/register", methods=["POST"])
def gateway_register():
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    return _proxy_request("POST", "auth", "/auth/register", json_body=body)


@app.route("/auth/login", methods=["POST"])
def gateway_login():
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    return _proxy_request("POST", "auth", "/auth/login", json_body=body)


@app.route("/auth/refresh", methods=["POST"])
def gateway_refresh():
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    return _proxy_request("POST", "auth", "/auth/refresh", json_body=body)


@app.route("/auth/logout", methods=["POST"])
def gateway_logout():
    try:
        _authorized("/auth/logout", required=True)
    except PermissionError as exc:
        return _permission_error_response(exc)
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    return _proxy_request("POST", "auth", "/auth/logout", json_body=body)


@app.route("/user/me", methods=["GET"])
def get_user_me():
    try:
        payload = _authorized("/user/me", required=True, extra_context={"requested_user_id": request.args.get("user_id", None)})
    except PermissionError as exc:
        return _permission_error_response(exc)
    return _proxy_request("GET", "user", "/user/me")


@app.route("/user/me", methods=["PUT"])
def update_user_me():
    try:
        payload = _authorized("/user/me", required=True, extra_context={"requested_user_id": getattr(g, "user_id", None)})
    except PermissionError as exc:
        return _permission_error_response(exc)
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    body.setdefault("user_id", payload.get("sub"))
    return _proxy_request("PUT", "user", "/user/me", json_body=body)


@app.route("/organization/info", methods=["GET"])
def organization_info():
    try:
        _authorized("/organization/info", required=True)
    except PermissionError as exc:
        return _permission_error_response(exc)
    return _proxy_request("GET", "organization", "/organization/info")


@app.route("/organization/info", methods=["PUT"])
def update_organization_info():
    try:
        _authorized("/organization/info", required=True)
    except PermissionError as exc:
        return _permission_error_response(exc)
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    return _proxy_request("PUT", "organization", "/organization/info", json_body=body)


@app.route("/media/upload", methods=["POST"])
def media_upload():
    try:
        _authorized("/media/upload", required=True)
    except PermissionError as exc:
        return _permission_error_response(exc)
    if request.content_type and "multipart/form-data" in request.content_type:
        files = {name: (file.filename, file.stream, file.content_type) for name, file in request.files.items()}
        data = request.form.to_dict(flat=True)
        return _proxy_request("POST", "media", "/media/upload", files=files, data=data)
    raw = request.get_data()
    headers = {"Content-Type": request.headers.get("Content-Type", "application/octet-stream")}
    return _proxy_request("POST", "media", "/media/upload", data=raw, headers=headers)


@app.route("/media/file/<media_id>", methods=["GET"])
def media_get(media_id: str):
    try:
        _authorized("/media/file", required=True)
    except PermissionError as exc:
        return _permission_error_response(exc)
    return _proxy_request("GET", "media", f"/media/file/{media_id}")


@app.route("/media/list", methods=["GET"])
def media_list():
    try:
        _authorized("/media/list", required=True)
    except PermissionError as exc:
        return _permission_error_response(exc)
    return _proxy_request("GET", "media", "/media/list")


@app.route("/media/file/<media_id>", methods=["DELETE"])
def media_delete(media_id: str):
    try:
        _authorized("/media/file", required=True)
    except PermissionError as exc:
        return _permission_error_response(exc)
    return _proxy_request("DELETE", "media", f"/media/file/{media_id}")


@app.route("/timeseries/write", methods=["POST"])
def timeseries_write():
    try:
        payload = _authorized("/timeseries/write", required=True)
    except PermissionError as exc:
        return _permission_error_response(exc)
    if request.headers.get("Content-Type", "").startswith("text/plain"):
        data = request.get_data()
        headers = {"Content-Type": request.headers.get("Content-Type")}
        return _proxy_request("POST", "timeseries", "/timeseries/write", data=data, headers=headers)
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    return _proxy_request("POST", "timeseries", "/timeseries/write", json_body=body)


@app.route("/timeseries/query", methods=["GET"])
def timeseries_query():
    try:
        payload = _authorized(
            "/timeseries/query",
            required=True,
            extra_context={"user_id": request.args.get("user_id")},
        )
    except PermissionError as exc:
        return _permission_error_response(exc)
    return _proxy_request("GET", "timeseries", "/timeseries/query", params=request.args.to_dict(flat=True))


@app.route("/audit/event", methods=["POST"])
def audit_event():
    try:
        _authorized("/audit", required=True)
    except PermissionError as exc:
        return _permission_error_response(exc)
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    return _proxy_request("POST", "audit", "/audit/event", json_body=body)


@app.route("/audit/events", methods=["GET"])
def audit_events():
    try:
        _authorized("/audit", required=True)
    except PermissionError as exc:
        return _permission_error_response(exc)
    return _proxy_request("GET", "audit", "/audit/events", params=request.args.to_dict(flat=True))


if __name__ == "__main__":
    port = int(os.getenv("GATEWAY_PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
