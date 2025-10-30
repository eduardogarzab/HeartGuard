import os
from typing import Dict

from flask import Flask, g, request

from .error_handler import register_error_handlers
from .middleware import get_metrics, init_app
from .models import create_user, get_user_by_id, verify_credentials
from .tokens import (
    generate_access_token,
    generate_refresh_token,
    is_refresh_token_valid,
    revoke_refresh_token,
    store_refresh_token,
)
from .utils_format import error_response, make_response, parse_body

app = Flask(__name__)
init_app(app)
register_error_handlers(app)

JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret")
JWT_EXPIRES_IN = int(os.getenv("JWT_EXPIRES_IN", "900"))
REFRESH_TOKEN_TTL = int(os.getenv("REFRESH_TOKEN_TTL", "604800"))


@app.route("/health", methods=["GET"])
def health():
    return make_response({"status": "ok", "service": "auth"})


@app.route("/ready", methods=["GET"])
def ready():
    from .tokens import _get_client

    status = 200
    details: Dict[str, str] = {}
    try:
        _get_client().ping()
        details["redis"] = "ok"
    except Exception as exc:  # pragma: no cover - depends on runtime
        details["redis"] = str(exc)
        status = 503
    return make_response({"status": "ready" if status == 200 else "degraded", "dependencies": details}, status=status)


@app.route("/metrics", methods=["GET"])
def metrics():
    return make_response(get_metrics(), root_tag="Metrics")


# POST /auth/register
# JSON Request example:
# {
#   "email": "admin@example.com",
#   "password": "Secret123",
#   "name": "Admin",
#   "org_id": "org-1"
# }
# XML Request example:
# <AuthRegister>
#   <email>admin@example.com</email>
#   <password>Secret123</password>
#   <name>Admin</name>
#   <org_id>org-1</org_id>
# </AuthRegister>
# Response JSON/XML:
# {
#   "user": {
#     "user_id": "...",
#     "org_id": "org-1",
#     "role": "org_admin"
#   }
# }
@app.route("/auth/register", methods=["POST"])
def register():
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    required = ["email", "password", "name", "org_id"]
    missing = [field for field in required if field not in body]
    if missing:
        return error_response(400, f"Missing fields: {', '.join(missing)}")
    try:
        user_info = create_user(body["email"], body["password"], body["name"], body["org_id"])
    except ValueError as exc:
        return error_response(409, str(exc))
    return make_response({"user": user_info}, status=201, root_tag="AuthRegisterResponse")


# POST /auth/login
# Request JSON/XML:
# {
#   "email": "admin@example.com",
#   "password": "Secret123"
# }
# Response JSON/XML:
# {
#   "access_token": "...",
#   "expires_in": 900,
#   "refresh_token": "...",
#   "refresh_expires_in": 604800,
#   "token_type": "Bearer",
#   "role": "org_admin"
# }
@app.route("/auth/login", methods=["POST"])
def login():
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    required = ["email", "password"]
    missing = [field for field in required if field not in body]
    if missing:
        return error_response(400, f"Missing fields: {', '.join(missing)}")
    record = verify_credentials(body["email"], body["password"])
    if not record:
        return error_response(401, "Invalid credentials")
    access_token = generate_access_token(record["user_id"], record["role"], record["org_id"], JWT_EXPIRES_IN, JWT_SECRET)
    refresh_token = generate_refresh_token()
    store_refresh_token(refresh_token, record["user_id"])
    response_body = {
        "access_token": access_token,
        "expires_in": JWT_EXPIRES_IN,
        "refresh_token": refresh_token,
        "refresh_expires_in": REFRESH_TOKEN_TTL,
        "token_type": "Bearer",
        "role": record["role"],
    }
    return make_response(response_body, root_tag="AuthToken")


# POST /auth/refresh
# Request:
# {
#   "refresh_token": "..."
# }
# Response:
# {
#   "access_token": "...",
#   "expires_in": 900,
#   "token_type": "Bearer"
# }
@app.route("/auth/refresh", methods=["POST"])
def refresh():
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    token = body.get("refresh_token")
    if not token:
        return error_response(400, "Missing refresh_token")
    user_id = is_refresh_token_valid(token)
    if not user_id:
        return error_response(401, "Invalid or expired refresh token")
    user = get_user_by_id(user_id)
    if not user:
        return error_response(401, "User not found")
    access_token = generate_access_token(user["user_id"], user["role"], user["org_id"], JWT_EXPIRES_IN, JWT_SECRET)
    return make_response({"access_token": access_token, "expires_in": JWT_EXPIRES_IN, "token_type": "Bearer"}, root_tag="AuthRefreshResponse")


# POST /auth/logout
# Request:
# {
#   "refresh_token": "..."
# }
# Response:
# {
#   "status": "logged_out"
# }
@app.route("/auth/logout", methods=["POST"])
def logout():
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    token = body.get("refresh_token")
    if not token:
        return error_response(400, "Missing refresh_token")
    revoke_refresh_token(token)
    return make_response({"status": "logged_out"}, root_tag="AuthLogoutResponse")


if __name__ == "__main__":
    port = int(os.getenv("AUTH_PORT", "5001"))
    app.run(host="0.0.0.0", port=port)
