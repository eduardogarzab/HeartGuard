import json
import os
import uuid
import logging
import html
from datetime import datetime, timedelta
from functools import wraps

import xmltodict
from dicttoxml import dicttoxml
from flask import Flask, request, g, make_response
from dotenv import load_dotenv
import redis

from db import init_db, session_scope, User, Organization, RefreshToken, RevokedToken
from security import hash_password, verify_password, generate_access_token, generate_refresh_token, decode_token, REFRESH_TOKEN_TTL

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=os.getenv("auth_LOG_LEVEL", "INFO"))
logger = logging.getLogger("auth-service")

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("auth_ALLOWED_ORIGINS", "*").split(",")]
REDIS_URL = os.getenv("auth_REDIS_URL")
redis_client = None
if REDIS_URL:
    try:
        redis_client = redis.Redis.from_url(REDIS_URL)
        redis_client.ping()
    except redis.RedisError:
        logger.warning("Redis no disponible, lista de revocación solo en base de datos")
        redis_client = None

init_db()

REQUEST_METRICS = {
    "requests": 0,
    "errors": 0,
    "latency_sum": 0.0
}

ROLES = ["admin", "manager", "user"]


def to_xml(data, root="response"):
    xml_bytes = dicttoxml(data, custom_root=root, attr_type=False)
    return xml_bytes.decode("utf-8")


def render_response(data, status=200, root="response"):
    accept = request.headers.get("Accept", "application/json")
    if "application/xml" in accept and "json" not in accept:
        xml_body = to_xml(data, root=root)
        response = make_response(xml_body, status)
        response.headers["Content-Type"] = "application/xml"
        return response
    response = make_response(json.dumps(data), status)
    response.headers["Content-Type"] = "application/json"
    return response


def render_error(code, message, status=400):
    payload = {"error": {"code": code, "message": message}}
    return render_response(payload, status=status, root="Error")


def parse_payload():
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


def sanitize_dict(data: dict):
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
            return render_error("AUTH_401", "Authorization header missing", status=401)
        token = auth_header.split(" ", 1)[1]
        try:
            claims = decode_token(token)
        except Exception:  # noqa: BLE001
            return render_error("AUTH_401", "Invalid or expired token", status=401)
        jti = claims.get("jti")
        if is_token_revoked(jti):
            return render_error("AUTH_401", "Token revoked", status=401)
        user = get_user(claims.get("sub"))
        if not user:
            return render_error("AUTH_404", "User not found", status=404)
        g.current_user = user
        g.token_claims = claims
        return f(*args, **kwargs)

    return decorated


def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            claims = getattr(g, "token_claims", {})
            if claims.get("role") not in roles:
                return render_error("AUTH_403", "Forbidden", status=403)
            return f(*args, **kwargs)

        return decorated

    return wrapper


def get_user(user_id):
    with session_scope() as session:
        user = session.get(User, user_id)
        if user:
            session.expunge(user)
        return user


def is_token_revoked(jti):
    if not jti:
        return False
    if redis_client:
        if redis_client.get(f"revoked:{jti}"):
            return True
    with session_scope() as session:
        return session.query(RevokedToken).filter_by(jti=jti).first() is not None


def revoke_token(jti, ttl_seconds=REFRESH_TOKEN_TTL):
    if not jti:
        return
    with session_scope() as session:
        if not session.query(RevokedToken).filter_by(jti=jti).first():
            session.add(RevokedToken(jti=jti))
    if redis_client:
        redis_client.setex(f"revoked:{jti}", ttl_seconds, "1")


@app.before_request
def before_request():
    request.start_time = datetime.utcnow()
    request.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))


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
    response.headers["X-Request-ID"] = getattr(request, "request_id", "")
    return response


@app.errorhandler(Exception)
def handle_exception(exc):  # noqa: ANN001
    logger.exception("Unhandled exception", extra={"request_id": getattr(request, "request_id", ""), "error": str(exc)})
    REQUEST_METRICS["errors"] += 1
    return render_error("AUTH_500", "Internal server error", status=500)


@app.route("/auth/health", methods=["GET"])
def health():
    return render_response({"status": "ok", "service": "auth"})


@app.route("/auth/ready", methods=["GET"])
def ready():
    try:
        with session_scope() as session:
            session.execute("SELECT 1")
        return render_response({"status": "ready"})
    except Exception as exc:  # noqa: BLE001
        return render_error("AUTH_READY", f"Database error: {exc}", status=503)


@app.route("/auth/metrics", methods=["GET"])
def metrics():
    avg_latency = REQUEST_METRICS["latency_sum"] / REQUEST_METRICS["requests"] if REQUEST_METRICS["requests"] else 0
    data = {
        "requests_total": REQUEST_METRICS["requests"],
        "errors_total": REQUEST_METRICS["errors"],
        "latency_avg_ms": round(avg_latency, 2)
    }
    return render_response(data)


@app.route("/auth/register", methods=["POST"])
def register():
    try:
        payload = sanitize_dict(parse_payload())
    except ValueError as exc:
        return render_error("AUTH_415", str(exc), status=415)
    required = {"email", "password", "role"}
    if not required.issubset(payload):
        return render_error("AUTH_400", "Missing fields", status=400)
    if payload["role"] not in ROLES:
        return render_error("AUTH_400", "Invalid role", status=400)
    with session_scope() as session:
        if session.query(User).filter_by(email=payload["email"]).first():
            return render_error("AUTH_409", "Email already registered", status=409)
        org_id = payload.get("organization_id")
        if org_id:
            organization = session.get(Organization, org_id)
            if not organization:
                return render_error("AUTH_400", "Organization not found", status=400)
        else:
            organization = session.query(Organization).first()
            if not organization:
                organization = Organization(name=os.getenv("auth_DEFAULT_ORG_NAME", "HeartGuard"))
                session.add(organization)
                session.flush()
        user = User(
            id=str(uuid.uuid4()),
            email=payload["email"],
            password_hash=hash_password(payload["password"]),
            role=payload["role"],
            organization_id=organization.id,
            first_name=payload.get("first_name"),
            last_name=payload.get("last_name")
        )
        session.add(user)
        session.flush()
        response_data = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "organization_id": user.organization_id
        }
        return render_response(response_data, status=201, root="RegisterResponse")


@app.route("/auth/login", methods=["POST"])
def login():
    try:
        payload = sanitize_dict(parse_payload())
    except ValueError as exc:
        return render_error("AUTH_415", str(exc), status=415)
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        return render_error("AUTH_400", "Email and password are required", status=400)
    with session_scope() as session:
        user = session.query(User).filter_by(email=email).first()
        if not user or not verify_password(password, user.password_hash):
            return render_error("AUTH_401", "Invalid credentials", status=401)
        access_token, access_jti = generate_access_token(user)
        refresh_token, refresh_jti = generate_refresh_token(user)
        expires_at = datetime.utcnow() + timedelta(seconds=REFRESH_TOKEN_TTL)
        session.add(RefreshToken(jti=refresh_jti, user_id=user.id, expires_at=expires_at))
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": int(os.getenv("auth_JWT_EXPIRES_IN", "3600")),
        "token_type": "Bearer"
    }
    return render_response(data, root="LoginResponse")


@app.route("/auth/profile", methods=["GET"])
@token_required
def profile():
    user = g.current_user
    data = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "organization_id": user.organization_id,
        "first_name": user.first_name,
        "last_name": user.last_name
    }
    return render_response(data, root="User")


@app.route("/auth/roles", methods=["GET"])
def roles():
    return render_response({"roles": ROLES}, root="Roles")


@app.route("/auth/refresh", methods=["POST"])
def refresh():
    try:
        payload = sanitize_dict(parse_payload())
    except ValueError as exc:
        return render_error("AUTH_415", str(exc), status=415)
    token = payload.get("refresh_token") or payload.get("token")
    if not token:
        return render_error("AUTH_400", "refresh_token is required", status=400)
    try:
        decoded = decode_token(token)
    except Exception:  # noqa: BLE001
        return render_error("AUTH_401", "Invalid refresh token", status=401)
    if decoded.get("type") != "refresh":
        return render_error("AUTH_400", "Invalid token type", status=400)
    jti = decoded.get("jti")
    if is_token_revoked(jti):
        return render_error("AUTH_401", "Refresh token revoked", status=401)
    user = get_user(decoded.get("sub"))
    if not user:
        return render_error("AUTH_404", "User not found", status=404)
    revoke_token(jti)
    access_token, access_jti = generate_access_token(user)
    refresh_token, refresh_jti = generate_refresh_token(user)
    expires_at = datetime.utcnow() + timedelta(seconds=REFRESH_TOKEN_TTL)
    with session_scope() as session:
        session.add(RefreshToken(jti=refresh_jti, user_id=user.id, expires_at=expires_at))
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": int(os.getenv("auth_JWT_EXPIRES_IN", "3600")),
        "token_type": "Bearer"
    }
    return render_response(data, root="LoginResponse")


@app.route("/auth/logout", methods=["POST"])
@token_required
def logout():
    claims = g.token_claims
    revoke_token(claims.get("jti"), ttl_seconds=int(os.getenv("auth_JWT_EXPIRES_IN", "3600")))
    try:
        payload = sanitize_dict(parse_payload())
    except ValueError:
        payload = {}
    refresh_token = payload.get("refresh_token")
    if refresh_token:
        try:
            decoded = decode_token(refresh_token)
            revoke_token(decoded.get("jti"))
        except Exception:  # noqa: BLE001
            pass
    return render_response({"status": "logged_out"}, root="LogoutResponse")


@app.route("/auth/token/introspect", methods=["POST"])
def introspect():
    try:
        payload = sanitize_dict(parse_payload())
    except ValueError as exc:
        return render_error("AUTH_415", str(exc), status=415)
    token = payload.get("token")
    if not token:
        return render_error("AUTH_400", "token is required", status=400)
    try:
        decoded = decode_token(token)
    except Exception:  # noqa: BLE001
        return render_response({"active": False}, root="IntrospectResponse")
    if is_token_revoked(decoded.get("jti")):
        return render_response({"active": False}, root="IntrospectResponse")
    return render_response({"active": True, "claims": decoded}, root="IntrospectResponse")


@app.route("/auth/setup/default", methods=["POST"])
def setup_default():
    """Crea usuario y organización por defecto si no existen."""
    org_name = os.getenv("auth_DEFAULT_ORG_NAME", "HeartGuard")
    admin_email = os.getenv("auth_DEFAULT_ADMIN_EMAIL", "admin@heartguard.io")
    admin_password = os.getenv("auth_DEFAULT_ADMIN_PASSWORD", "ChangeMe123!")
    with session_scope() as session:
        organization = session.query(Organization).filter_by(name=org_name).first()
        if not organization:
            organization = Organization(name=org_name)
            session.add(organization)
            session.flush()
        user = session.query(User).filter_by(email=admin_email).first()
        if not user:
            user = User(
                id=str(uuid.uuid4()),
                email=admin_email,
                password_hash=hash_password(admin_password),
                role="admin",
                organization_id=organization.id,
                first_name="System",
                last_name="Administrator"
            )
            session.add(user)
        return render_response({"status": "ok", "admin_email": admin_email}, root="SetupResponse")


def bootstrap_default_admin():
    org_name = os.getenv("auth_DEFAULT_ORG_NAME", "HeartGuard")
    admin_email = os.getenv("auth_DEFAULT_ADMIN_EMAIL", "admin@heartguard.io")
    admin_password = os.getenv("auth_DEFAULT_ADMIN_PASSWORD", "ChangeMe123!")
    with session_scope() as session:
        organization = session.query(Organization).filter_by(name=org_name).first()
        if not organization:
            organization = Organization(name=org_name)
            session.add(organization)
            session.flush()
        user = session.query(User).filter_by(email=admin_email).first()
        if not user:
            user = User(
                id=str(uuid.uuid4()),
                email=admin_email,
                password_hash=hash_password(admin_password),
                role="admin",
                organization_id=organization.id
            )
            session.add(user)


bootstrap_default_admin()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("auth_PORT", "5001")))
