"""Organization service backed by the backend PostgreSQL schema."""
from __future__ import annotations

import datetime as dt
import uuid

from flask import Blueprint, g, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import Organization, OrgInvitation, OrgRole

bp = Blueprint("organization", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response(
        {
            "service": "organization",
            "status": "healthy",
            "organizations": Organization.query.count(),
            "invitations": OrgInvitation.query.count(),
        }
    )


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def get_organization() -> "Response":
    org_id = request.args.get("org_id")
    org_code = request.args.get("code")
    query = Organization.query
    if org_id:
        query = query.filter_by(id=org_id)
    elif org_code:
        query = query.filter_by(code=org_code)
    organization = query.first()
    if not organization:
        raise APIError("Organization not found", status_code=404, error_id="HG-ORG-NOT-FOUND")
    return render_response({"organization": _serialize_org(organization)})


@bp.route("", methods=["PUT"])
@require_auth(required_roles=["superadmin", "org_admin"])
def update_organization() -> "Response":
    payload, _ = parse_request_data(request)
    org_id = payload.get("id") or payload.get("org_id")
    if not org_id:
        raise APIError("id is required", status_code=400, error_id="HG-ORG-ID")
    organization = Organization.query.get(org_id)
    if not organization:
        raise APIError("Organization not found", status_code=404, error_id="HG-ORG-NOT-FOUND")
    for field in ["name", "code"]:
        if field in payload:
            setattr(organization, field, payload[field])
    db.session.commit()
    return render_response({"organization": _serialize_org(organization)})


@bp.route("/invitations", methods=["GET"])
@require_auth(optional=True)
def list_invitations() -> "Response":
    org_id = request.args.get("org_id")
    query = OrgInvitation.query
    if org_id:
        query = query.filter_by(org_id=org_id)
    invitations = [
        _serialize_invitation(invitation)
        for invitation in query.order_by(OrgInvitation.created_at.desc()).all()
    ]
    return render_response({"invitations": invitations}, meta={"total": len(invitations)})


@bp.route("/invitations", methods=["POST"])
@require_auth(required_roles=["superadmin", "org_admin"])
def create_invitation() -> "Response":
    payload, _ = parse_request_data(request)
    email = payload.get("email")
    if not email:
        raise APIError("email is required", status_code=400, error_id="HG-ORG-EMAIL")

    org_id = payload.get("org_id")
    if not org_id and payload.get("org_code"):
        organization = Organization.query.filter_by(code=payload["org_code"]).first()
        if not organization:
            raise APIError("Organization not found", status_code=404, error_id="HG-ORG-NOT-FOUND")
        org_id = organization.id
    if not org_id:
        raise APIError("org_id is required", status_code=400, error_id="HG-ORG-ID")

    role_code = payload.get("role_code") or payload.get("org_role_code")
    if not role_code:
        raise APIError("role_code is required", status_code=400, error_id="HG-ORG-ROLE")
    org_role = OrgRole.query.filter_by(code=role_code).first()
    if not org_role:
        raise APIError("Role code not found", status_code=404, error_id="HG-ORG-ROLE-NOTFOUND")

    expires_in = int(payload.get("expires_in_days", 7))
    expires_at = dt.datetime.utcnow() + dt.timedelta(days=max(expires_in, 1))

    invitation = OrgInvitation(
        id=str(uuid.uuid4()),
        org_id=org_id,
        email=email,
        org_role_id=org_role.id,
        token=str(uuid.uuid4()),
        expires_at=expires_at,
        created_by=g.current_user.get("sub") if getattr(g, "current_user", None) else None,
        created_at=dt.datetime.utcnow(),
    )
    db.session.add(invitation)
    db.session.commit()
    return render_response({"invitation": _serialize_invitation(invitation)}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/organization")


def _serialize_org(organization: Organization) -> dict:
    return {
        "id": organization.id,
        "code": organization.code,
        "name": organization.name,
        "created_at": organization.created_at.isoformat() + "Z",
    }


def _serialize_invitation(invitation: OrgInvitation) -> dict:
    role = OrgRole.query.get(invitation.org_role_id)
    return {
        "id": invitation.id,
        "org_id": invitation.org_id,
        "email": invitation.email,
        "role_code": role.code if role else None,
        "token": invitation.token,
        "expires_at": invitation.expires_at.isoformat() + "Z",
        "created_at": invitation.created_at.isoformat() + "Z",
        "created_by": invitation.created_by,
    }
