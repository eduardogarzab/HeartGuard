"""Organization service exposing organization management endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

from flask import Blueprint, Response, current_app, g, request
from itsdangerous import BadSignature, URLSafeSerializer

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response
import dicttoxml
import models
# Models accessed via models. models.Organization
from sqlalchemy import text

bp = Blueprint("organization", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "organization", "status": "healthy"})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_organizations() -> "Response":
    organizations = [o.to_dict() for o in models.Organization.query.all()]
    return render_response({"organizations": organizations}, meta={"total": len(organizations)})


@bp.route("", methods=["POST"])
@require_auth(required_roles=["admin"])
def create_organization() -> "Response":
    payload, _ = parse_request_data(request)
    name = payload.get("name")
    code = payload.get("code")
    if not name or not code:
        raise APIError("name and code are required", status_code=400, error_id="HG-ORG-VALIDATION")

    new_org = models.Organization(name=name, code=code)

    db.session.add(new_org)
    db.session.commit()

    return render_response({"organization": new_org.to_dict()}, status_code=201)


@bp.route("/<org_id>", methods=["GET"])
@require_auth(optional=True)
def get_organization(org_id: str) -> "Response":
    org = models.Organization.query.get(org_id)
    if not org:
        raise APIError("models.Organization not found", status_code=404, error_id="HG-ORG-NOT-FOUND")
    return render_response({"organization": org.to_dict()})


@bp.route("/invitations", methods=["GET"])
@require_auth(optional=True)
def list_invitations() -> "Response":
    org_id = request.args.get("org_id")
    try:
        invitations_query = models.OrgInvitationQuery.for_org(org_id)
    except (TypeError, ValueError) as exc:
        raise APIError("org_id must be a valid UUID", status_code=400, error_id="HG-ORG-INVITE-BAD-ORG") from exc

    invitations = [invite.to_dict() for invite in invitations_query.all()]
    return render_response({"invitations": invitations}, meta={"total": len(invitations)})


@bp.route("/invitations", methods=["POST"])
@require_auth(required_roles=["admin", "org_admin"])
def create_invitation() -> "Response":
    payload, _ = parse_request_data(request)
    org_id = payload.get("org_id")
    email = payload.get("email")
    role_identifier = payload.get("role") or payload.get("org_role_id")
    ttl_value = payload.get("ttl_hours")

    if not org_id:
        raise APIError("org_id is required", status_code=400, error_id="HG-ORG-INVITE-VALIDATION")
    if not role_identifier:
        raise APIError("role is required", status_code=400, error_id="HG-ORG-INVITE-VALIDATION")
    if ttl_value is None:
        raise APIError("ttl_hours is required", status_code=400, error_id="HG-ORG-INVITE-VALIDATION")

    try:
        ttl_hours = int(ttl_value)
    except (TypeError, ValueError) as exc:
        raise APIError("ttl_hours must be an integer", status_code=400, error_id="HG-ORG-INVITE-VALIDATION") from exc

    if ttl_hours < 1 or ttl_hours > 720:
        raise APIError("ttl_hours must be between 1 and 720", status_code=400, error_id="HG-ORG-INVITE-TTL-RANGE")

    try:
        org_uuid = uuid.UUID(str(org_id))
    except (TypeError, ValueError) as exc:
        raise APIError("org_id must be a valid UUID", status_code=400, error_id="HG-ORG-INVITE-BAD-ORG") from exc

    organization = db.session.get(models.Organization, org_uuid)
    if not organization:
        raise APIError("Organization not found", status_code=404, error_id="HG-ORG-NOT-FOUND")

    current_user_payload = getattr(g, "current_user", {}) or {}
    if not isinstance(current_user_payload, dict):
        current_user_payload = {}

    token_roles = current_user_payload.get("roles", [])
    if isinstance(token_roles, str):
        token_roles = [token_roles]
    user_roles = {str(role).lower() for role in token_roles if isinstance(role, str)}

    preferred_org_id = current_user_payload.get("org_id")
    user_uuid = None
    user_id_claim = current_user_payload.get("sub")
    if user_id_claim:
        try:
            user_uuid = uuid.UUID(str(user_id_claim))
        except (TypeError, ValueError):
            user_uuid = None

    if "admin" not in user_roles:
        if preferred_org_id and str(preferred_org_id) != str(org_uuid):
            raise APIError(
                "Insufficient permissions for organization",
                status_code=403,
                error_id="HG-ORG-INVITE-FORBIDDEN",
            )
        if not user_uuid:
            raise APIError(
                "Authenticated user is missing or invalid",
                status_code=403,
                error_id="HG-ORG-INVITE-FORBIDDEN",
            )
        membership = (
            models.UserOrgMembership.query.join(
                models.OrgRole,
                models.UserOrgMembership.org_role_id == models.OrgRole.id,
            )
            .filter(
                models.UserOrgMembership.org_id == org_uuid,
                models.UserOrgMembership.user_id == user_uuid,
            )
            .first()
        )
        if (
            not membership
            or not membership.role
            or (membership.role.code or "").lower() != "org_admin"
        ):
            raise APIError(
                "Insufficient permissions for organization",
                status_code=403,
                error_id="HG-ORG-INVITE-FORBIDDEN",
            )

    role = _resolve_org_role(role_identifier)
    if not role:
        raise APIError("Organization role not found", status_code=404, error_id="HG-ORG-ROLE-NOT-FOUND")

    now = datetime.utcnow()

    created_by = user_uuid

    invitation_payload = _create_invitation(
        organization=organization,
        role=role,
        email=email,
        ttl_hours=ttl_hours,
        created_by=created_by,
        now=now,
    )

    return render_response({"invitation": invitation_payload}, status_code=201)


@bp.route("/invitations/<invitation_id>/cancel", methods=["POST"])
@require_auth(required_roles=["admin", "org_admin"])
def cancel_invitation(invitation_id: str) -> "Response":
    try:
        invitation_uuid = uuid.UUID(str(invitation_id))
    except (TypeError, ValueError) as exc:
        raise APIError("invitation_id must be a valid UUID", status_code=400, error_id="HG-ORG-INVITE-BAD-ID") from exc

    invitation = db.session.get(models.OrgInvitation, invitation_uuid)
    if not invitation or invitation.revoked_at or invitation.used_at:
        raise APIError(
            "Invitation not found or already processed",
            status_code=404,
            error_id="HG-ORG-INVITE-NOT-FOUND",
        )

    invitation.revoked_at = datetime.utcnow()
    db.session.commit()

    return Response(status=204)


@bp.route("/invitations/<token>/validate", methods=["GET"])
def validate_invitation(token: str) -> "Response":
    invitation = models.OrgInvitation.query.filter_by(token=token).first()
    if not invitation:
        return _render_invitation_xml(
            token,
            result="invalid",
            reason="not_found",
            http_status=404,
        )

    state, reason = _determine_invitation_state(invitation)
    payload = invitation.to_dict()
    payload["state"] = state
    if reason:
        payload["reason"] = reason
    return _render_invitation_xml(token, payload=payload, result="valid" if state == "pending" else state)


@bp.route("/invitations/<token>/consume", methods=["POST"])
def consume_invitation(token: str) -> "Response":
    invitation = models.OrgInvitation.query.filter_by(token=token).first()
    if not invitation:
        return _render_invitation_xml(
            token,
            result="invalid",
            reason="not_found",
            http_status=404,
        )

    state, reason = _determine_invitation_state(invitation)
    if state != "pending":
        payload = invitation.to_dict()
        payload["state"] = state
        if reason:
            payload["reason"] = reason
        return _render_invitation_xml(token, payload=payload, result=state, http_status=409)

    invitation.used_at = datetime.utcnow()
    db.session.commit()

    payload = invitation.to_dict()
    payload["state"] = "used"
    return _render_invitation_xml(token, payload=payload, result="used")


def _resolve_org_role(identifier: str | None):
    if not identifier:
        return None

    candidate = None
    try:
        candidate_uuid = uuid.UUID(str(identifier))
    except (TypeError, ValueError):
        candidate_uuid = None

    if candidate_uuid:
        candidate = db.session.get(models.OrgRole, candidate_uuid)
    if not candidate:
        candidate = models.OrgRole.query.filter(
            db.func.lower(models.OrgRole.code) == str(identifier).lower()
        ).first()
    return candidate


def _create_invitation(*, organization, role, email, ttl_hours: int, created_by, now: datetime) -> dict[str, object]:
    engine = db.session.get_bind()
    if engine and engine.dialect.name == "postgresql":
        statement = text(
            "SELECT * FROM heartguard.sp_org_invitation_create(:org_id, :org_role_id, :email, :ttl_hours, :created_by)"
        )
        params = {
            "org_id": organization.id,
            "org_role_id": role.id,
            "email": email,
            "ttl_hours": ttl_hours,
            "created_by": created_by,
        }
        result = db.session.execute(statement, params)
        row = result.mappings().first()
        db.session.commit()
        if not row:
            raise APIError(
                "Failed to create invitation",
                status_code=500,
                error_id="HG-ORG-INVITE-SP-FAILED",
            )
        return _serialize_invitation_row(row)

    expires_at = now + timedelta(hours=ttl_hours)
    invitation = models.OrgInvitation(
        organization=organization,
        role=role,
        email=email,
        expires_at=expires_at,
        created_at=now,
    )
    if created_by:
        invitation.created_by = created_by

    db.session.add(invitation)
    db.session.commit()
    return invitation.to_dict()


def _serialize_invitation_row(row) -> dict[str, object]:
    def _iso(value):
        if not value:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    row_dict = dict(row)
    def _string(value):
        if value is None:
            return None
        return str(value)

    payload = {
        "id": _string(row_dict.get("id")),
        "org_id": _string(row_dict.get("org_id")),
        "email": row_dict.get("email"),
        "role": row_dict.get("org_role_code"),
        "status": row_dict.get("status"),
        "token": row_dict.get("token"),
        "created_at": _iso(row_dict.get("created_at")),
        "expires_at": _iso(row_dict.get("expires_at")),
        "used_at": _iso(row_dict.get("used_at")),
        "revoked_at": _iso(row_dict.get("revoked_at")),
        "org_role_id": _string(row_dict.get("org_role_id")),
        "created_by": _string(row_dict.get("created_by")),
    }
    return payload


def _determine_invitation_state(invitation: models.OrgInvitation) -> tuple[str, str | None]:
    if invitation.revoked_at:
        return "revoked", "Invitation has been revoked"
    if invitation.used_at:
        return "used", "Invitation has already been used"
    expires_at = models.OrgInvitation._coerce_datetime(invitation.expires_at)
    now_utc = datetime.now(timezone.utc)
    if expires_at and expires_at <= now_utc:
        return "expired", "Invitation has expired"
    return "pending", None


def _render_invitation_xml(token: str, *, result: str, payload: dict[str, object] | None = None, reason: str | None = None, http_status: int = 200) -> "Response":
    if payload is None:
        payload = {"token": token}
    if "token" not in payload:
        payload["token"] = token
    payload["result"] = result
    if reason and "reason" not in payload:
        payload["reason"] = reason

    xml_body = dicttoxml.dicttoxml({"invitation": payload}, custom_root="response", attr_type=False)
    response = Response(xml_body, status=http_status, mimetype="application/xml")
    return response


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/organization")
