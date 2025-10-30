"""User service managing application user profiles."""
from __future__ import annotations

import copy
import datetime as dt
from typing import Dict

from flask import Blueprint, g, request

from common.auth import require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("users", __name__)

USER_STORE: Dict[str, Dict] = {
    "usr-1": {
        "id": "usr-1",
        "email": "admin@example.com",
        "first_name": "Alicia",
        "last_name": "Admin",
        "language": "es",
        "timezone": "America/Mexico_City",
        "organization_id": "org-1",
        "preferences": {"notifications": True, "theme": "dark"},
    },
    "usr-2": {
        "id": "usr-2",
        "email": "clinician@example.com",
        "first_name": "Carlos",
        "last_name": "Clinician",
        "language": "en",
        "timezone": "America/New_York",
        "organization_id": "org-1",
        "preferences": {"notifications": True, "theme": "light"},
    },
}


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "user", "status": "healthy", "users": len(USER_STORE)})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_users() -> "Response":
    return render_response({"users": list(USER_STORE.values())}, meta={"total": len(USER_STORE)})


@bp.route("/<user_id>", methods=["GET"])
@require_auth(optional=True)
def get_user(user_id: str) -> "Response":
    user = USER_STORE.get(user_id)
    if not user:
        raise APIError("User not found", status_code=404, error_id="HG-USER-NOT-FOUND")
    return render_response({"user": user})


@bp.route("/<user_id>", methods=["PATCH"])
@require_auth(required_roles=["admin", "clinician", "org_admin"])
def update_user(user_id: str) -> "Response":
    payload, _ = parse_request_data(request)
    user = USER_STORE.get(user_id)
    if not user:
        raise APIError("User not found", status_code=404, error_id="HG-USER-NOT-FOUND")
    allowed = {"first_name", "last_name", "language", "timezone", "preferences"}
    for key, value in payload.items():
        if key in allowed:
            user[key] = value
    user["updated_at"] = dt.datetime.utcnow().isoformat() + "Z"
    return render_response({"user": user})


@bp.route("/me", methods=["GET"])
@require_auth()
def get_me() -> "Response":
    user_id = g.current_user.get("sub")
    user = USER_STORE.get(user_id)
    if not user:
        raise APIError("User not found", status_code=404, error_id="HG-USER-NOT-FOUND")
    return render_response({"user": user})


@bp.route("/me", methods=["PATCH"])
@require_auth()
def update_me() -> "Response":
    payload, _ = parse_request_data(request)
    user_id = g.current_user.get("sub")
    user = USER_STORE.get(user_id)
    if not user:
        raise APIError("User not found", status_code=404, error_id="HG-USER-NOT-FOUND")
    allowed = {"language", "timezone", "preferences"}
    for key, value in payload.items():
        if key in allowed:
            user[key] = value
    user["updated_at"] = dt.datetime.utcnow().isoformat() + "Z"
    return render_response({"user": user})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/users")
