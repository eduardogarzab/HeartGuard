"""User service reflecting the shared users table."""
from __future__ import annotations

import datetime as dt

from flask import Blueprint, g, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import Organization, Role, User, UserOrgMembership, UserStatus

bp = Blueprint("users", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response(
        {
            "service": "user",
            "status": "healthy",
            "users": User.query.count(),
            "organizations": Organization.query.count(),
        }
    )


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_users() -> "Response":
    users = [
        _serialize_user(user)
        for user in User.query.order_by(User.created_at.desc()).limit(200).all()
    ]
    return render_response({"users": users}, meta={"total": len(users)})


@bp.route("/<user_id>", methods=["GET"])
@require_auth(optional=True)
def get_user(user_id: str) -> "Response":
    user = _get_user(user_id)
    return render_response({"user": _serialize_user(user)})


@bp.route("/<user_id>", methods=["PATCH"])
@require_auth(required_roles=["superadmin", "clinician", "ops"])
def update_user(user_id: str) -> "Response":
    payload, _ = parse_request_data(request)
    user = _get_user(user_id)

    if "status" in payload:
        status = UserStatus.query.filter_by(code=payload["status"]).first()
        if not status:
            raise APIError("Invalid status code", status_code=400, error_id="HG-USER-STATUS")
        user.user_status_id = status.id

    if "roles" in payload:
        _update_roles(user, payload["roles"])

    for key in ["name", "profile_photo_url", "two_factor_enabled"]:
        if key in payload:
            setattr(user, key, payload[key])

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

    for key in ["name", "profile_photo_url", "two_factor_enabled"]:
        if key in payload:
            setattr(user, key, payload[key])

    user.updated_at = dt.datetime.utcnow()
    db.session.commit()
    return render_response({"user": _serialize_user(user)})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/users")


def _get_user(user_id: str) -> User:
    user = User.query.get(user_id)
    if not user:
        raise APIError("User not found", status_code=404, error_id="HG-USER-NOT-FOUND")
    return user


def _serialize_user(user: User) -> dict:
    memberships = UserOrgMembership.query.filter_by(user_id=user.id).all()
    orgs = [
        {
            "org_id": membership.org_id,
            "role_id": membership.org_role_id,
            "joined_at": membership.joined_at.isoformat() + "Z",
        }
        for membership in memberships
    ]
    status = UserStatus.query.get(user.user_status_id)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "status": status.code if status else None,
        "two_factor_enabled": user.two_factor_enabled,
        "profile_photo_url": user.profile_photo_url,
        "roles": [role.name for role in user.roles],
        "organizations": orgs,
        "created_at": (user.created_at or dt.datetime.utcnow()).isoformat() + "Z",
        "updated_at": (user.updated_at or dt.datetime.utcnow()).isoformat() + "Z",
    }


def _update_roles(user: User, role_names: list[str]) -> None:
    desired = {name for name in role_names}
    current_names = {role.name for role in user.roles}

    for role in list(user.roles):
        if role.name not in desired:
            user.roles.remove(role)

    missing = desired - current_names
    if missing:
        db_roles = Role.query.filter(Role.name.in_(missing)).all()
        found = {role.name for role in db_roles}
        unfound = missing - found
        if unfound:
            raise APIError(
                f"Roles no válidos: {', '.join(sorted(unfound))}",
                status_code=400,
                error_id="HG-USER-ROLE",
            )
        for role in db_roles:
            if role not in user.roles:
                user.roles.append(role)
