"""Auth service routes implementing JWT issuance and RBAC scaffolding."""
from __future__ import annotations

from typing import Iterable, Sequence

from flask import Blueprint, Response, request

from common.auth import get_jwt_manager, issue_tokens, require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

# Use absolute import to avoid relative import issues
import models


def _collect_user_roles(user: "models.User") -> tuple[list[str], str | None, str | None]:
    """Return combined global/org roles and preferred organization context."""

    global_roles_query = (
        models.Role.query
        .join(models.UserRole, models.UserRole.role_id == models.Role.id)
        .filter(models.UserRole.user_id == user.id)
    )
    global_roles = [role.name.lower() for role in global_roles_query if role.name]

    memberships: Sequence[models.UserOrgMembership] = (
        models.UserOrgMembership.query
        .filter_by(user_id=user.id)
        .join(models.Organization, models.UserOrgMembership.org_id == models.Organization.id)
        .join(models.OrgRole, models.UserOrgMembership.org_role_id == models.OrgRole.id)
        .order_by(models.UserOrgMembership.joined_at.asc())
        .all()
    )

    org_roles = [
        membership.org_role.code.lower()
        for membership in memberships
        if membership.org_role and membership.org_role.code
    ]

    preferred_membership = next(
        (
            m
            for m in memberships
            if m.org_role and m.org_role.code and m.org_role.code.lower() == "org_admin"
        ),
        None,
    )
    if preferred_membership is None and memberships:
        preferred_membership = memberships[0]

    org_id = str(preferred_membership.organization.id) if preferred_membership and preferred_membership.organization else None
    organization_name = preferred_membership.organization.name if preferred_membership and preferred_membership.organization else None

    roles = sorted({*global_roles, *org_roles})
    if not roles:
        roles = ["user"]
    return roles, org_id, organization_name


def _serialize_auth_response(tokens: dict, user_id: str, roles: Iterable[str], org_id: str | None, organization_name: str | None) -> dict:
    """Create a response payload matching the expectations of the frontend."""

    payload = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "expires_in": tokens["expires_in"],
        "token_type": tokens["token_type"],
        "roles": ",".join(roles),
        "user_id": user_id,
    }

    payload["org_id"] = org_id or ""
    payload["organization_name"] = organization_name or ""
    return payload

bp = Blueprint("auth", __name__)

@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "auth", "status": "healthy"})


@bp.route("/register", methods=["POST"])
def register() -> "Response":
    payload, _ = parse_request_data(request)
    email = payload.get("email")
    password = payload.get("password")
    name = payload.get("name")

    if not email or not password or not name:
        raise APIError("Email, password, and name are required", status_code=400, error_id="HG-AUTH-VALIDATION")

    if models.User.query.filter_by(email=email).first():
        raise APIError("User already exists", status_code=409, error_id="HG-AUTH-CONFLICT")

    # This is a placeholder for the user_status_id. In a real application,
    # you would fetch this from a 'user_statuses' table.
    user_status_id = "405673b4-f543-4982-b0f9-52f375d85a12"  # 'active' status from user_statuses table

    new_user = models.User(name=name, email=email, user_status_id=user_status_id)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    # In a real RBAC system, you would fetch roles from the database.
    # For now, we'll pass an empty list.
    tokens = issue_tokens(str(new_user.id), [])
    return render_response({"user": new_user.to_dict(), "tokens": tokens}, status_code=201)


@bp.route("/login", methods=["POST"])
def login() -> "Response":
    payload, _ = parse_request_data(request)
    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        raise APIError("Email and password are required", status_code=400, error_id="HG-AUTH-VALIDATION")

    user = models.User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise APIError("Invalid credentials", status_code=401, error_id="HG-AUTH-CREDENTIALS")

    roles, org_id, organization_name = _collect_user_roles(user)
    tokens = issue_tokens(str(user.id), roles, org_id=org_id)
    response_payload = _serialize_auth_response(tokens, str(user.id), roles, org_id, organization_name)
    return render_response(response_payload)


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
        raise APIError("Refresh token is not recognized", status_code=401, error_id="HG-AUTH-REFRESH") from exc

    if decoded.get("type") != "refresh":
        raise APIError("Provided token is not a refresh token", status_code=401, error_id="HG-AUTH-REFRESH-TYPE")

    user = models.User.query.get(decoded.get("sub"))
    if not user:
        raise APIError("User not found for refresh token", status_code=401, error_id="HG-AUTH-USER-NOT-FOUND")

    roles, org_id, organization_name = _collect_user_roles(user)
    tokens = issue_tokens(str(user.id), roles, org_id=org_id)
    response_payload = _serialize_auth_response(tokens, str(user.id), roles, org_id, organization_name)
    return render_response(response_payload)


@bp.route("/logout", methods=["POST"])
def logout() -> "Response":
    return render_response({"message": "Logged out"}, status_code=200)


@bp.route("/permissions", methods=["GET"])
@require_auth(optional=True)
def list_permissions() -> "Response":
    # This should be fetched from the 'permissions' table in a real application.
    permissions = []
    return render_response({"permissions": permissions}, meta={"total": len(permissions)})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/auth")
