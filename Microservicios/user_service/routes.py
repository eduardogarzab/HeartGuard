"""User service managing application user profiles."""
from __future__ import annotations

import datetime as dt
import uuid

from flask import Blueprint, g, request
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response
import models

bp = Blueprint("users", __name__)


def _ensure_database_available() -> None:
    if db is None:
        raise APIError(
            "Database not configured for user service",
            status_code=503,
            error_id="HG-USER-NODB",
        )


def _resolve_org_id() -> uuid.UUID:
    """Derive the organization id from query parameters or JWT claims."""

    org_id_param = request.args.get("org_id")
    if org_id_param:
        try:
            return uuid.UUID(org_id_param)
        except ValueError as exc:  # pragma: no cover - defensive conversion
            raise APIError(
                "Invalid org_id format",
                status_code=400,
                error_id="HG-USER-BADORG",
            ) from exc

    current_user = getattr(g, "current_user", {}) or {}
    org_claim = current_user.get("org_id") or current_user.get("organization_id")
    if org_claim is None:
        orgs_claim = current_user.get("org_ids") or current_user.get("organizations")
        if isinstance(orgs_claim, (list, tuple)) and orgs_claim:
            if len(orgs_claim) > 1:
                raise APIError(
                    "Multiple organizations found in token, provide org_id parameter",
                    status_code=400,
                    error_id="HG-USER-MULTIORG",
                )
            org_claim = orgs_claim[0]
        elif isinstance(orgs_claim, str):
            org_claim = orgs_claim

    if not org_claim:
        raise APIError(
            "org_id is required",
            status_code=400,
            error_id="HG-USER-ORG-REQUIRED",
        )

    try:
        return uuid.UUID(str(org_claim))
    except ValueError as exc:
        raise APIError(
            "Invalid org_id format",
            status_code=400,
            error_id="HG-USER-BADORG",
        ) from exc


def _serialize_membership_row(row) -> dict:
    return {
        "id": str(row.user_id),
        "name": row.name,
        "email": row.email,
        "role": row.role_code,
        "status": row.status_code,
        "org_id": str(row.org_id),
    }


def _serialize_user(user: models.User) -> dict:
    status_code = user.status.code if getattr(user, "status", None) else None
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "status": status_code,
    }


def _parse_user_id(user_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(user_id)
    except ValueError as exc:
        raise APIError("Invalid user id", status_code=400, error_id="HG-USER-BADID") from exc


def _load_user(user_uuid: uuid.UUID) -> models.User | None:
    return models.User.query.options(joinedload(models.User.status)).get(user_uuid)


def _update_user_from_payload(user: models.User, payload: dict) -> models.User:
    # Allow updates for basic attributes available in the schema.
    if "name" in payload and isinstance(payload["name"], str) and payload["name"].strip():
        user.name = payload["name"].strip()
    if "status" in payload:
        status_code = payload["status"]
        status = models.UserStatus.query.filter_by(code=status_code).first()
        if not status:
            raise APIError(
                f"Unknown status '{status_code}'",
                status_code=400,
                error_id="HG-USER-STATUS",
            )
        user.user_status_id = status.id

    user.updated_at = dt.datetime.utcnow()
    db.session.commit()
    return _load_user(user.id)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    total_users = 0
    if db is not None:
        try:
            total_users = db.session.query(func.count(models.User.id)).scalar() or 0
        except Exception:
            total_users = 0
    return render_response({"service": "user", "status": "healthy", "users": total_users})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_users() -> "Response":
    _ensure_database_available()
    org_id = _resolve_org_id()

    query = (
        db.session.query(
            models.UserOrgMembership.org_id,
            models.UserOrgMembership.user_id,
            models.User.name,
            models.User.email,
            models.OrgRole.code.label("role_code"),
            models.UserStatus.code.label("status_code"),
        )
        .join(models.User, models.User.id == models.UserOrgMembership.user_id)
        .join(models.OrgRole, models.OrgRole.id == models.UserOrgMembership.org_role_id)
        .join(models.UserStatus, models.UserStatus.id == models.User.user_status_id)
        .filter(models.UserOrgMembership.org_id == org_id)
        .order_by(models.User.name.asc())
    )

    memberships = [_serialize_membership_row(row) for row in query.all()]
    meta = {"total": len(memberships), "org_id": str(org_id)}
    return render_response({"users": memberships}, meta=meta, xml_item_name="User")


@bp.route("/<user_id>", methods=["GET"])
@require_auth(optional=True)
def get_user(user_id: str) -> "Response":
    _ensure_database_available()
    user_uuid = _parse_user_id(user_id)
    user = _load_user(user_uuid)
    if not user:
        raise APIError("User not found", status_code=404, error_id="HG-USER-NOT-FOUND")
    return render_response({"user": _serialize_user(user)})


@bp.route("/<user_id>", methods=["PATCH"])
@require_auth(required_roles=["admin", "clinician", "org_admin"])
def update_user(user_id: str) -> "Response":
    _ensure_database_available()
    payload, _ = parse_request_data(request)
    user_uuid = _parse_user_id(user_id)
    user = _load_user(user_uuid)
    if not user:
        raise APIError("User not found", status_code=404, error_id="HG-USER-NOT-FOUND")

    updated = _update_user_from_payload(user, payload) or user
    return render_response({"user": _serialize_user(updated)})


@bp.route("/me", methods=["GET"])
@require_auth()
def get_me() -> "Response":
    user_id = g.current_user.get("sub")
    if not user_id:
        raise APIError("User not found", status_code=404, error_id="HG-USER-NOT-FOUND")
    return get_user(user_id)


@bp.route("/me", methods=["PATCH"])
@require_auth()
def update_me() -> "Response":
    payload, _ = parse_request_data(request)
    user_id = g.current_user.get("sub")
    if not user_id:
        raise APIError("User not found", status_code=404, error_id="HG-USER-NOT-FOUND")

    # Delegate to shared logic; ignore preference-only fields gracefully.
    if any(key in {"language", "timezone", "preferences"} for key in payload):
        g.logger.info("Ignoring preference fields for user %s - not yet persisted", user_id)

    _ensure_database_available()
    user_uuid = _parse_user_id(user_id)
    user = _load_user(user_uuid)
    if not user:
        raise APIError("User not found", status_code=404, error_id="HG-USER-NOT-FOUND")

    updated = _update_user_from_payload(user, payload) or user
    return render_response({"user": _serialize_user(updated)})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/users")
