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

from db import init_db, session_scope, User

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=os.getenv("user_LOG_LEVEL", "INFO"))
logger = logging.getLogger("user-service")

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("user_ALLOWED_ORIGINS", "*").split(",")]
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
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, str):
            cleaned[key] = html.escape(value.strip())
        else:
            cleaned[key] = value
    return cleaned


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error("USER_401", "Authorization required", status=401)
        token = auth_header.split(" ", 1)[1]
        try:
            claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return error("USER_401", "Token expired", status=401)
        except jwt.InvalidTokenError:
            return error("USER_401", "Invalid token", status=401)
        g.claims = claims
        return f(*args, **kwargs)

    return decorated


def require_role(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.claims.get("role") not in roles:
                return error("USER_403", "Forbidden", status=403)
            return f(*args, **kwargs)

        return decorated

    return wrapper


def serialize_user(user: User):
    preferences = {}
    if user.preferences:
        try:
            preferences = json.loads(user.preferences)
        except json.JSONDecodeError:
            preferences = {}
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "organization_id": user.organization_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "preferences": preferences,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
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
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response


@app.route("/users/health", methods=["GET"])
def health():
    return render({"status": "ok", "service": "user"})


@app.route("/users/metrics", methods=["GET"])
def metrics():
    avg = REQUEST_METRICS["latency_sum"] / REQUEST_METRICS["requests"] if REQUEST_METRICS["requests"] else 0
    return render({
        "requests_total": REQUEST_METRICS["requests"],
        "errors_total": REQUEST_METRICS["errors"],
        "latency_avg_ms": round(avg, 2)
    })


@app.route("/users/me", methods=["GET"])
@token_required
def me():
    user_id = g.claims.get("sub")
    with session_scope() as session:
        user = session.get(User, user_id)
        if not user:
            return error("USER_404", "User not found", status=404)
        return render(serialize_user(user), root="User")


@app.route("/users/me", methods=["PUT"])
@token_required
def update_me():
    try:
        payload = sanitize(parse_body())
    except ValueError as exc:
        return error("USER_415", str(exc), status=415)
    allowed = {"first_name", "last_name", "preferences"}
    updates = {k: v for k, v in payload.items() if k in allowed}
    if not updates:
        return error("USER_400", "No valid fields", status=400)
    user_id = g.claims.get("sub")
    with session_scope() as session:
        user = session.get(User, user_id)
        if not user:
            return error("USER_404", "User not found", status=404)
        if "preferences" in updates:
            prefs = updates["preferences"]
            if isinstance(prefs, str):
                try:
                    prefs_json = json.loads(prefs)
                except json.JSONDecodeError:
                    prefs_json = {}
            else:
                prefs_json = prefs
            updates["preferences"] = json.dumps(prefs_json)
        for key, value in updates.items():
            setattr(user, key, value)
        user.updated_at = datetime.utcnow()
        session.flush()
        return render(serialize_user(user), root="User")


@app.route("/users/<user_id>", methods=["GET"])
@token_required
@require_role("admin")
def get_user(user_id):
    with session_scope() as session:
        user = session.get(User, user_id)
        if not user:
            return error("USER_404", "User not found", status=404)
        return render(serialize_user(user), root="User")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("user_PORT", 5003)))
