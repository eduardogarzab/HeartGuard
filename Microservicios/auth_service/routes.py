"""Auth service routes implementing JWT issuance and RBAC scaffolding."""
from __future__ import annotations

import datetime as dt
import os
import uuid

from flask import Blueprint, current_app, request

from common.auth import get_jwt_manager, issue_tokens, require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import RefreshToken, User, create_default_admin

bp = Blueprint("auth", __name__)

AVAILABLE_ROLES = ["admin", "clinician", "org_admin", "user", "caregiver"]


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "auth", "status": "healthy", "users": User.query.count()})


@bp.route("/register", methods=["POST"])
def register() -> "Response":
    payload, _ = parse_request_data(request)
    email = payload.get("email")
    password = payload.get("password")
    roles = payload.get("roles", ["user"])
    if not email or not password:
        raise APIError("Email and password are required", status_code=400, error_id="HG-AUTH-VALIDATION")
    existing = User.query.filter_by(email=email).first()
    if existing:
        raise APIError("User already exists", status_code=409, error_id="HG-AUTH-CONFLICT")
    user = User(id=f"usr-{uuid.uuid4()}", email=email, roles=roles)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    tokens = _issue_and_store_tokens(user)
    return render_response({"user": {"id": user.id, "email": user.email, "roles": roles}, "tokens": tokens}, status_code=201)


@bp.route("/login", methods=["POST"])
def login() -> "Response":
    payload, _ = parse_request_data(request)
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        raise APIError("Email and password are required", status_code=400, error_id="HG-AUTH-VALIDATION")
    user = User.query.filter_by(email=email).first()
    if not user or not user.verify_password(password):
        raise APIError("Invalid credentials", status_code=401, error_id="HG-AUTH-CREDENTIALS")
    tokens = _issue_and_store_tokens(user)
    return render_response({"tokens": tokens, "user": {"id": user.id, "roles": user.roles}})


@bp.route("/refresh", methods=["POST"])
def refresh() -> "Response":
    payload, _ = parse_request_data(request)
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise APIError("refresh_token is required", status_code=400, error_id="HG-AUTH-VALIDATION")
    token_entry = RefreshToken.query.filter_by(token=refresh_token).first()
    if not token_entry:
        raise APIError("Refresh token is not recognized", status_code=401, error_id="HG-AUTH-REFRESH")
    if token_entry.expires_at and token_entry.expires_at < dt.datetime.utcnow():
        db.session.delete(token_entry)
        db.session.commit()
        raise APIError("Refresh token expired", status_code=401, error_id="HG-AUTH-REFRESH-EXPIRED")
    manager = get_jwt_manager()
    decoded = manager.decode(refresh_token)
    if decoded.get("type") != "refresh":
        raise APIError("Provided token is not a refresh token", status_code=401, error_id="HG-AUTH-REFRESH-TYPE")
    user = token_entry.user
    tokens = _issue_and_store_tokens(user)
    return render_response({"tokens": tokens})


@bp.route("/logout", methods=["POST"])
def logout() -> "Response":
    payload, _ = parse_request_data(request)
    refresh_token = payload.get("refresh_token")
    if refresh_token:
        RefreshToken.query.filter_by(token=refresh_token).delete()
        db.session.commit()
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
    with app.app_context():
        create_default_admin(
            os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com"),
            os.getenv("DEFAULT_ADMIN_PASSWORD", "ChangeMe123!"),
            roles=["admin"],
        )


def _issue_and_store_tokens(user: User) -> dict:
    tokens = issue_tokens(user.id, user.roles)
    manager = get_jwt_manager()
    decoded_refresh = manager.decode(tokens["refresh_token"])
    expires = dt.datetime.utcfromtimestamp(decoded_refresh["exp"])
    RefreshToken.query.filter_by(user_id=user.id).filter(RefreshToken.token == tokens["refresh_token"]).delete()
    db.session.add(
        RefreshToken(
            token=tokens["refresh_token"],
            user_id=user.id,
            expires_at=expires,
        )
    )
    db.session.commit()
    current_app.logger.info("issued_tokens user_id=%s", user.id)
    return tokens
