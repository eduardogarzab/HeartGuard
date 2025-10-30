"""User service managing application user profiles."""
from __future__ import annotations

import copy
import datetime as dt
import datetime as dt

from flask import Blueprint, g, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import UserProfile

bp = Blueprint("users", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "user", "status": "healthy", "users": UserProfile.query.count()})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_users() -> "Response":
    users = [
        _serialize_user(user)
        for user in UserProfile.query.order_by(UserProfile.created_at.desc()).all()
    ]
    return render_response({"users": users}, meta={"total": len(users)})


@bp.route("/<user_id>", methods=["GET"])
@require_auth(optional=True)
def get_user(user_id: str) -> "Response":
    user = _get_user(user_id)
    return render_response({"user": _serialize_user(user)})


@bp.route("/<user_id>", methods=["PATCH"])
@require_auth(required_roles=["admin", "clinician", "org_admin"])
def update_user(user_id: str) -> "Response":
    payload, _ = parse_request_data(request)
    user = _get_user(user_id)
    allowed = {"first_name", "last_name", "language", "timezone", "preferences", "organization_id", "email"}
    for key, value in payload.items():
        if key in allowed:
            setattr(user, key, value)
    user.updated_at = dt.datetime.utcnow()
    db.session.commit()
    return render_response({"user": _serialize_user(user)})


@bp.route("/me", methods=["GET"])
@require_auth()
def get_me() -> "Response":
    user_id = g.current_user.get("sub")
    user = _get_user(user_id)
    return render_response({"user": _serialize_user(user)})


@bp.route("/me", methods=["PATCH"])
@require_auth()
def update_me() -> "Response":
    payload, _ = parse_request_data(request)
    user_id = g.current_user.get("sub")
    user = _get_user(user_id)
    allowed = {"language", "timezone", "preferences"}
    for key, value in payload.items():
        if key in allowed:
            setattr(user, key, value)
    user.updated_at = dt.datetime.utcnow()
    db.session.commit()
    return render_response({"user": _serialize_user(user)})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/users")
    with app.app_context():
        seed_default_users()


def _get_user(user_id: str) -> UserProfile:
    user = UserProfile.query.get(user_id)
    if not user:
        raise APIError("User not found", status_code=404, error_id="HG-USER-NOT-FOUND")
    return user


def _serialize_user(user: UserProfile) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language": user.language,
        "timezone": user.timezone,
        "organization_id": user.organization_id,
        "preferences": user.preferences or {},
        "created_at": (user.created_at or dt.datetime.utcnow()).isoformat() + "Z",
        "updated_at": (user.updated_at or dt.datetime.utcnow()).isoformat() + "Z",
    }


def seed_default_users() -> None:
    if UserProfile.query.count() > 0:
        return
    defaults = [
        UserProfile(
            id="usr-1",
            email="admin@example.com",
            first_name="Alicia",
            last_name="Admin",
            language="es",
            timezone="America/Mexico_City",
            organization_id="org-1",
            preferences={"notifications": True, "theme": "dark"},
        ),
        UserProfile(
            id="usr-2",
            email="clinician@example.com",
            first_name="Carlos",
            last_name="Clinician",
            language="en",
            timezone="America/New_York",
            organization_id="org-1",
            preferences={"notifications": True, "theme": "light"},
        ),
    ]
    for user in defaults:
        db.session.add(user)
    db.session.commit()
