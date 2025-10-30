import json
import os
import logging
import html
import uuid
from datetime import datetime
from functools import wraps

import jwt
import xmltodict
from dicttoxml import dicttoxml
from flask import Flask, request, g, make_response
from dotenv import load_dotenv

from db import init_db, session_scope, AuditEvent

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=os.getenv("audit_LOG_LEVEL", "INFO"))
logger = logging.getLogger("audit-service")

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("audit_ALLOWED_ORIGINS", "*").split(",")]
JWT_SECRET = os.getenv("auth_JWT_SECRET", os.getenv("gateway_JWT_SECRET", "super-secret"))

init_db()

REQUEST_METRICS = {"requests": 0, "errors": 0, "latency_sum": 0.0}


def render(data, status=200, root="response"):
    accept = request.headers.get("Accept", "application/json")
    if "application/xml" in accept and "json" not in accept:
        xml_body = dicttoxml(data, custom_root=root, attr_type=False).decode("utf-8")
        resp = make_response(xml_body, status)
        resp.headers["Content-Type"] = "application/xml"
        return resp
    resp = make_response(json.dumps(data), status)
    resp.headers["Content-Type"] = "application/json"
    return resp


def error(code, message, status=400):
    return render({"error": {"code": code, "message": message}}, status=status, root="Error")


def parse_body():
    if request.method not in {"POST", "PUT", "PATCH"}:
        return {}
    content_type = request.headers.get("Content-Type", "application/json").split(";")[0]
    if "application/json" in content_type:
        data = request.get_json(silent=True)
        if data is None:
            raise ValueError("Invalid JSON body")
        return data
    if "application/xml" in content_type:
        try:
            parsed = xmltodict.parse(request.data or b"")
            root = next(iter(parsed.values())) if parsed else {}
            return dict(root)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("Invalid XML body") from exc
    raise ValueError("Unsupported Content-Type")


def sanitize(data):
    return {k: html.escape(v.strip()) if isinstance(v, str) else v for k, v in data.items()}


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error("AUDIT_401", "Authorization required", status=401)
        token = auth_header.split(" ", 1)[1]
        try:
            claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return error("AUDIT_401", "Token expired", status=401)
        except jwt.InvalidTokenError:
            return error("AUDIT_401", "Invalid token", status=401)
        g.claims = claims
        return f(*args, **kwargs)

    return decorated


def require_role(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.claims.get("role") not in roles:
                return error("AUDIT_403", "Forbidden", status=403)
            return f(*args, **kwargs)

        return decorated

    return wrapper


def serialize_event(event: AuditEvent):
    metadata = {}
    if event.details:
        try:
            metadata = json.loads(event.details)
        except json.JSONDecodeError:
            metadata = {}
    return {
        "event_id": event.event_id,
        "service": event.service,
        "actor": event.actor,
        "action": event.action,
        "resource": event.resource,
        "metadata": metadata,
        "created_at": event.created_at.isoformat() if event.created_at else None
    }


@app.before_request
def before_request():
    request.start_time = datetime.utcnow()


@app.after_request
def after_request(response):
    latency = (datetime.utcnow() - getattr(request, "start_time", datetime.utcnow())).total_seconds() * 1000
    REQUEST_METRICS["requests"] += 1
    REQUEST_METRICS["latency_sum"] += latency
    if response.status_code >= 400:
        REQUEST_METRICS["errors"] += 1
    origin = request.headers.get("Origin")
    if "*" in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
    elif origin and origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, X-Request-ID"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.route("/audit/health", methods=["GET"])
def health():
    return render({"status": "ok", "service": "audit"})


@app.route("/audit/metrics", methods=["GET"])
def metrics():
    avg = REQUEST_METRICS["latency_sum"] / REQUEST_METRICS["requests"] if REQUEST_METRICS["requests"] else 0
    return render({
        "requests_total": REQUEST_METRICS["requests"],
        "errors_total": REQUEST_METRICS["errors"],
        "latency_avg_ms": round(avg, 2)
    })


@app.route("/audit/events", methods=["POST"])
@token_required
def create_event():
    try:
        payload = sanitize(parse_body())
    except ValueError as exc:
        return error("AUDIT_415", str(exc), status=415)
    required = {"service", "action"}
    if not required.issubset(payload):
        return error("AUDIT_400", "Missing fields", status=400)
    event = AuditEvent(
        event_id=str(uuid.uuid4()),
        service=payload["service"],
        actor=payload.get("actor", g.claims.get("email")),
        action=payload["action"],
        resource=payload.get("resource"),
        details=json.dumps(payload.get("metadata", {}))
    )
    with session_scope() as session:
        session.add(event)
        session.flush()
        return render(serialize_event(event), status=201, root="AuditEvent")


@app.route("/audit/events", methods=["GET"])
@token_required
@require_role("admin")
def list_events():
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    with session_scope() as session:
        query = session.query(AuditEvent).order_by(AuditEvent.created_at.desc())
        total = query.count()
        events = query.offset(offset).limit(limit).all()
        payload = {
            "total": total,
            "limit": limit,
            "offset": offset,
            "events": [serialize_event(evt) for evt in events]
        }
        return render(payload, root="AuditEvents")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("audit_PORT", 5006)))
