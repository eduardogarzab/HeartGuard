"""Auth service routes bound to the backend PostgreSQL schema."""
from __future__ import annotations

import datetime as dt
import os
import uuid

from flask import Blueprint, current_app, request
from sqlalchemy import and_

from common.auth import get_jwt_manager, issue_tokens, require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import (
    Permission,
    RefreshToken,
    Role,
    User,
    UserRole,
    create_default_admin,
    ensure_roles,
    hash_refresh_token,
    refresh_token_matches,
    resolve_user_status,
)

bp = Blueprint("auth", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response(
        {
            "service": "auth",
            "status": "healthy",
            "users": User.query.count(),
            "roles": Role.query.count(),
        }
    )


@bp.route("/register", methods=["POST"])
def register() -> "Response":
    payload, _ = parse_request_data(request)
    email = payload.get("email")
    password = payload.get("password")
    roles = payload.get("roles", ["caregiver"])
    status_code = payload.get("status", "active")
    full_name = payload.get("name") or payload.get("full_name") or email.split("@")[0]
    if not email or not password:
        raise APIError("Email and password are required", status_code=400, error_id="HG-AUTH-VALIDATION")
    existing = User.query.filter_by(email=email).first()
    if existing:
        raise APIError("User already exists", status_code=409, error_id="HG-AUTH-CONFLICT")
    try:
        db_roles = ensure_roles(roles)
    except ValueError as exc:
        raise APIError(str(exc), status_code=400, error_id="HG-AUTH-ROLE") from exc
    try:
        status = resolve_user_status(status_code)
    except ValueError as exc:
        raise APIError(str(exc), status_code=400, error_id="HG-AUTH-STATUS") from exc

    user = User(
        id=str(uuid.uuid4()),
        name=full_name,
        email=email,
        user_status_id=status.id,
        two_factor_enabled=False,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    for role in db_roles:
        db.session.add(UserRole(user_id=user.id, role_id=role.id, assigned_at=dt.datetime.utcnow()))

    db.session.commit()
    db.session.refresh(user)
    tokens = _issue_and_store_tokens(user)
    return render_response(
        {
            "user": {"id": user.id, "email": user.email, "roles": [role.name for role in user.roles]},
            "tokens": tokens,
        },
        status_code=201,
    )


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
    return render_response({"tokens": tokens, "user": {"id": user.id, "roles": [role.name for role in user.roles]}})


@bp.route("/refresh", methods=["POST"])
def refresh() -> "Response":
    payload, _ = parse_request_data(request)
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise APIError("refresh_token is required", status_code=400, error_id="HG-AUTH-VALIDATION")
    manager = get_jwt_manager()
    try:
        decoded = manager.decode(refresh_token)
    except Exception as exc:
        raise APIError("Invalid refresh token", status_code=401, error_id="HG-AUTH-REFRESH-DECODE") from exc
    if decoded.get("type") != "refresh":
        raise APIError("Provided token is not a refresh token", status_code=401, error_id="HG-AUTH-REFRESH-TYPE")

    user_id = decoded.get("sub")
    if not user_id:
        raise APIError("Refresh token missing subject", status_code=401, error_id="HG-AUTH-REFRESH-SUBJECT")

    token_entry = _find_refresh_token(user_id, refresh_token)
    if token_entry is None:
        raise APIError("Refresh token is not recognized", status_code=401, error_id="HG-AUTH-REFRESH")
    if token_entry.expires_at < dt.datetime.utcnow():
        token_entry.revoked_at = dt.datetime.utcnow()
        db.session.commit()
        raise APIError("Refresh token expired", status_code=401, error_id="HG-AUTH-REFRESH-EXPIRED")

    user = User.query.get(user_id)
    if not user:
        raise APIError("User not found", status_code=404, error_id="HG-AUTH-USER-NOTFOUND")

    token_entry.revoked_at = dt.datetime.utcnow()
    db.session.commit()

    tokens = _issue_and_store_tokens(user)
    return render_response({"tokens": tokens})


@bp.route("/logout", methods=["POST"])
def logout() -> "Response":
    payload, _ = parse_request_data(request)
    refresh_token = payload.get("refresh_token")
    if refresh_token:
        manager = get_jwt_manager()
        try:
            decoded = manager.decode(refresh_token)
        except Exception as exc:
            raise APIError("Invalid refresh token", status_code=401, error_id="HG-AUTH-LOGOUT-TOKEN") from exc
        user_id = decoded.get("sub")
        if not user_id:
            raise APIError("Refresh token missing subject", status_code=401, error_id="HG-AUTH-LOGOUT-SUBJECT")
        token_entry = _find_refresh_token(user_id, refresh_token)
        if token_entry:
            token_entry.revoked_at = dt.datetime.utcnow()
            db.session.commit()
    return render_response({"message": "Logged out"}, status_code=200)


@bp.route("/roles", methods=["GET"])
@require_auth(optional=True)
def list_roles() -> "Response":
    roles = [
        {"id": role.id, "name": role.name, "description": role.description}
        for role in Role.query.order_by(Role.name).all()
    ]
    return render_response({"roles": roles}, meta={"total": len(roles)})


@bp.route("/permissions", methods=["GET"])
@require_auth(optional=True)
def list_permissions() -> "Response":
    permission_rows = (
        Permission.query.order_by(Permission.code).all()
    )
    permissions = [
        {"code": permission.code, "description": permission.description}
        for permission in permission_rows
    ]
    return render_response({"permissions": permissions}, meta={"total": len(permissions)})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/auth")
    with app.app_context():
        try:
            create_default_admin(
                os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com"),
                os.getenv("DEFAULT_ADMIN_PASSWORD", "ChangeMe123!"),
                roles=["superadmin"],
            )
        except ValueError as exc:
            current_app.logger.warning("default_admin_setup_failed error=%s", exc)


def _issue_and_store_tokens(user: User) -> dict:
    role_names = [role.name for role in user.roles]
    tokens = issue_tokens(user.id, role_names)
    manager = get_jwt_manager()
    decoded_refresh = manager.decode(tokens["refresh_token"])
    expires = dt.datetime.utcfromtimestamp(decoded_refresh["exp"])
    hashed_token = hash_refresh_token(tokens["refresh_token"])
    refresh_entry = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hashed_token,
        issued_at=dt.datetime.utcnow(),
        expires_at=expires,
    )
    db.session.add(refresh_entry)
    db.session.commit()
    current_app.logger.info("issued_tokens user_id=%s", user.id)
    return tokens


def _find_refresh_token(user_id: str, raw_token: str) -> RefreshToken | None:
    candidate = (
        RefreshToken.query.filter(
            and_(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        )
        .order_by(RefreshToken.issued_at.desc())
        .all()
    )
    for token in candidate:
        if refresh_token_matches(token.token_hash, raw_token):
            return token
    return None
