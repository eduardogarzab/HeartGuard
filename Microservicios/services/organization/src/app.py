import json
import os
import logging
import html
from datetime import datetime
from functools import wraps

import jwt
import xmltodict
from dicttoxml import dicttoxml
from flask import Flask, request, g, make_response
from dotenv import load_dotenv

from db import init_db, session_scope, Organization

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=os.getenv("organization_LOG_LEVEL", "INFO"))
logger = logging.getLogger("organization-service")

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("organization_ALLOWED_ORIGINS", "*").split(",")]
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
            return error("ORG_401", "Authorization required", status=401)
        token = auth_header.split(" ", 1)[1]
        try:
            claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return error("ORG_401", "Token expired", status=401)
        except jwt.InvalidTokenError:
            return error("ORG_401", "Invalid token", status=401)
        g.claims = claims
        return f(*args, **kwargs)

    return decorated


@app.before_request
def before_request():
    request.start_time = datetime.utcnow()
    request.request_id = request.headers.get("X-Request-ID")


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
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response


@app.route("/organization/health", methods=["GET"])
def health():
    return render({"status": "ok", "service": "organization"})


@app.route("/organization/metrics", methods=["GET"])
def metrics():
    avg = REQUEST_METRICS["latency_sum"] / REQUEST_METRICS["requests"] if REQUEST_METRICS["requests"] else 0
    return render({
        "requests_total": REQUEST_METRICS["requests"],
        "errors_total": REQUEST_METRICS["errors"],
        "latency_avg_ms": round(avg, 2)
    })


@app.route("/organization", methods=["GET"])
@token_required
def get_org():
    org_id = g.claims.get("org_id")
    if not org_id:
        return error("ORG_400", "Token missing organization", status=400)
    with session_scope() as session:
        organization = session.get(Organization, org_id)
        if not organization:
            return error("ORG_404", "Organization not found", status=404)
        data = {
            "id": organization.id,
            "name": organization.name,
            "logo_url": organization.logo_url,
            "policies": organization.policies,
            "contact_email": organization.contact_email,
            "contact_phone": organization.contact_phone,
            "settings": organization.settings
        }
        return render(data, root="Organization")


@app.route("/organization", methods=["PUT"])
@token_required
def update_org():
    role = g.claims.get("role")
    if role not in {"admin", "manager"}:
        return error("ORG_403", "Forbidden", status=403)
    try:
        payload = sanitize(parse_body())
    except ValueError as exc:
        return error("ORG_415", str(exc), status=415)
    allowed_fields = {"name", "logo_url", "policies", "contact_email", "contact_phone", "settings"}
    updates = {k: v for k, v in payload.items() if k in allowed_fields}
    if not updates:
        return error("ORG_400", "No valid fields", status=400)
    org_id = g.claims.get("org_id")
    with session_scope() as session:
        organization = session.get(Organization, org_id)
        if not organization:
            organization = Organization(id=org_id, name=updates.get("name", "Organization"))
            session.add(organization)
            session.flush()
        for key, value in updates.items():
            setattr(organization, key, value)
        organization.updated_at = datetime.utcnow()
        session.flush()
        data = {
            "id": organization.id,
            "name": organization.name,
            "logo_url": organization.logo_url,
            "policies": organization.policies,
            "contact_email": organization.contact_email,
            "contact_phone": organization.contact_phone,
            "settings": organization.settings
        }
        return render(data, root="Organization")


@app.route("/organization/policies", methods=["GET"])
@token_required
def policies():
    org_id = g.claims.get("org_id")
    with session_scope() as session:
        organization = session.get(Organization, org_id)
        policies_text = organization.policies if organization else ""
        return render({"policies": policies_text}, root="Policies")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("organization_PORT", 5002)))
