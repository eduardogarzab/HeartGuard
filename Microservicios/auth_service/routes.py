"""Auth service routes implementing JWT issuance and RBAC scaffolding."""
from __future__ import annotations

import uuid
from typing import Dict

from flask import Blueprint, request

from common.auth import get_jwt_manager, issue_tokens, require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("auth", __name__)

USERS: Dict[str, Dict] = {
    "admin@example.com": {
        "id": "usr-1",
        "email": "admin@example.com",
        "password": "Admin123!",
        "roles": ["admin"],
    },
    "clinician@example.com": {
        "id": "usr-2",
        "email": "clinician@example.com",
        "password": "Clinician123!",
        "roles": ["clinician"],
    },
}

REFRESH_STORE: Dict[str, str] = {}
AVAILABLE_ROLES = ["admin", "clinician", "org_admin", "user", "caregiver"]


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "auth", "status": "healthy", "users": len(USERS)})


@bp.route("/register", methods=["POST"])
def register() -> "Response":
    payload, _ = parse_request_data(request)
    email = payload.get("email")
    password = payload.get("password")
    roles = payload.get("roles", ["user"])
    if not email or not password:
        raise APIError("Email and password are required", status_code=400, error_id="HG-AUTH-VALIDATION")
    if email in USERS:
        raise APIError("User already exists", status_code=409, error_id="HG-AUTH-CONFLICT")
    user_id = f"usr-{uuid.uuid4()}"
    USERS[email] = {"id": user_id, "email": email, "password": password, "roles": roles}
    tokens = issue_tokens(user_id, roles)
    REFRESH_STORE[tokens["refresh_token"]] = email
    return render_response({"user": {"id": user_id, "email": email, "roles": roles}, "tokens": tokens}, status_code=201)


@bp.route("/login", methods=["POST"])
def login() -> "Response":
    payload, _ = parse_request_data(request)
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        raise APIError("Email and password are required", status_code=400, error_id="HG-AUTH-VALIDATION")
    user = USERS.get(email)
    if not user or user["password"] != password:
        raise APIError("Invalid credentials", status_code=401, error_id="HG-AUTH-CREDENTIALS")
    tokens = issue_tokens(user["id"], user["roles"])
    REFRESH_STORE[tokens["refresh_token"]] = email
    return render_response({"tokens": tokens, "user": {"id": user["id"], "roles": user["roles"]}})


@bp.route("/refresh", methods=["POST"])
def refresh() -> "Response":
    payload, _ = parse_request_data(request)
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise APIError("refresh_token is required", status_code=400, error_id="HG-AUTH-VALIDATION")
    if refresh_token not in REFRESH_STORE:
        raise APIError("Refresh token is not recognized", status_code=401, error_id="HG-AUTH-REFRESH")
    manager = get_jwt_manager()
    decoded = manager.decode(refresh_token)
    if decoded.get("type") != "refresh":
        raise APIError("Provided token is not a refresh token", status_code=401, error_id="HG-AUTH-REFRESH-TYPE")
    email = REFRESH_STORE[refresh_token]
    user = USERS[email]
    tokens = issue_tokens(user["id"], user["roles"])
    REFRESH_STORE[tokens["refresh_token"]] = email
    return render_response({"tokens": tokens})


@bp.route("/logout", methods=["POST"])
def logout() -> "Response":
    payload, _ = parse_request_data(request)
    refresh_token = payload.get("refresh_token")
    if refresh_token and refresh_token in REFRESH_STORE:
        REFRESH_STORE.pop(refresh_token, None)
    return render_response({"message": "Logged out"}, status_code=200)


@bp.route("/roles", methods=["GET"])
@require_auth(optional=True)
def list_roles() -> "Response":
    return render_response({"roles": AVAILABLE_ROLES}, meta={"total": len(AVAILABLE_ROLES)})


@bp.route("/permissions", methods=["GET"])
@require_auth(optional=True)
def list_permissions() -> "Response":
    permissions = [
        "auth:login",
        "auth:refresh",
        "user:read",
        "user:update",
        "organization:manage",
        "alert:ack",
        "media:upload",
    ]
    return render_response({"permissions": permissions}, meta={"total": len(permissions)})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/auth")
