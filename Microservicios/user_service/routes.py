"""User service managing application user profiles."""
from __future__ import annotations

import datetime as dt
import os
import uuid

import requests
from flask import Blueprint, current_app, g, request
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response
import models
from werkzeug.security import generate_password_hash

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


def _organization_service_base_url() -> str:
    base_url = current_app.config.get("ORGANIZATION_SERVICE_URL")
    if base_url:
        return base_url.rstrip("/")
    env_url = os.getenv("ORGANIZATION_SERVICE_URL", "http://organization-service:5002/organization")
    current_app.config["ORGANIZATION_SERVICE_URL"] = env_url
    return env_url.rstrip("/")


def _call_organization_service(method: str, path: str, **kwargs) -> requests.Response:
    url = f"{_organization_service_base_url()}{path}"
    timeout = current_app.config.get("ORGANIZATION_HTTP_TIMEOUT", 5)
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
    except requests.RequestException as exc:  # pragma: no cover - network failure
        raise APIError(
            "Failed to contact organization service",
            status_code=502,
            error_id="HG-USER-ORG-SERVICE",
        ) from exc

    if response.status_code >= 400:
        message = "Organization service error"
        try:
            payload = response.json()
            message = (
                payload.get("error", {}).get("message")
                or payload.get("message")
                or message
            )
        except ValueError:
            if response.text:
                message = response.text
        raise APIError(message, status_code=response.status_code, error_id="HG-USER-ORG-SERVICE")

    return response


def _fetch_invitation_details(signed_token: str) -> dict:
    response = _call_organization_service(
        "GET",
        f"/invitations/{signed_token}/validate",
        headers={"Accept": "application/json"},
    )
    data = response.json().get("data") or {}
    return data


def _consume_invitation_token(signed_token: str, payload: dict) -> None:
    _call_organization_service(
        "POST",
        f"/invitations/{signed_token}/consume",
        headers={"Accept": "application/json"},
        json=payload,
    )


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


@bp.route("/register", methods=["POST"])
def register_from_invitation() -> "Response":
    _ensure_database_available()
    payload, _ = parse_request_data(request)

    signed_token = payload.get("invite_token") or payload.get("token")
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password")

    if not signed_token:
        raise APIError("invite_token is required", status_code=400, error_id="HG-USER-INVITE-TOKEN")
    if not name:
        raise APIError("name is required", status_code=400, error_id="HG-USER-NAME")
    if not email:
        raise APIError("email is required", status_code=400, error_id="HG-USER-EMAIL")
    if not password:
        raise APIError("password is required", status_code=400, error_id="HG-USER-PASSWORD")

    invitation = _fetch_invitation_details(str(signed_token))
    invitation_data = invitation.get("invitation") or {}
    metadata = invitation.get("metadata") or {}

    org_id_value = invitation_data.get("org_id")
    role_id_value = invitation_data.get("org_role_id")
    invited_email = invitation_data.get("email")

    try:
        org_uuid = uuid.UUID(str(org_id_value))
    except (TypeError, ValueError) as exc:
        raise APIError("Invitation organization invalid", status_code=400, error_id="HG-USER-INVITE-ORG") from exc

    try:
        role_uuid = uuid.UUID(str(role_id_value))
    except (TypeError, ValueError) as exc:
        raise APIError("Invitation role invalid", status_code=400, error_id="HG-USER-INVITE-ROLE") from exc

    if invited_email and invited_email.lower() != email:
        raise APIError("Email does not match invitation", status_code=400, error_id="HG-USER-INVITE-EMAIL")

    existing = models.User.query.filter(func.lower(models.User.email) == email).first()
    if existing:
        raise APIError("Email already registered", status_code=409, error_id="HG-USER-EMAIL-EXISTS")

    status = models.UserStatus.query.filter_by(code="active").first()
    if not status:
        raise APIError("Active status not configured", status_code=500, error_id="HG-USER-NO-STATUS")

    password_hash = generate_password_hash(password)
    new_user_id = uuid.uuid4()
    new_user = models.User(
        id=new_user_id,
        name=name,
        email=email,
        password_hash=password_hash,
        user_status_id=status.id,
    )

    membership = models.UserOrgMembership(
        org_id=org_uuid,
        user_id=new_user_id,
        org_role_id=role_uuid,
    )

    db.session.add(new_user)
    db.session.add(membership)
    db.session.flush()

    try:
        _consume_invitation_token(
            signed_token,
            {
                "action": "accept",
                "consumer_type": "user",
                "consumer_id": str(new_user.id),
            },
        )
    except APIError:
        db.session.rollback()
        raise

    db.session.commit()

    response_payload = {
        "user": _serialize_user(new_user),
        "membership": {
            "org_id": str(org_uuid),
            "org_role_id": str(role_uuid),
            "organization": metadata.get("organization"),
            "suggested_role": metadata.get("suggested_role"),
        },
    }
    return render_response(response_payload, status_code=201, xml_item_name="User")


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
