"""Organization service exposing organization management endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta
import uuid

from flask import Blueprint, Response, g, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response
import models
# Models accessed via models. models.Organization

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
    expires_at = now + timedelta(hours=ttl_hours)
    token = uuid.uuid4().hex

    created_by = user_uuid

    invitation = models.OrgInvitation(
        organization=organization,
        role=role,
        email=email,
        expires_at=expires_at,
        token=token,
        created_at=now,
    )
    if created_by:
        invitation.created_by = created_by

    db.session.add(invitation)
    db.session.commit()

    return render_response({"invitation": invitation.to_dict()}, status_code=201)


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


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/organization")
