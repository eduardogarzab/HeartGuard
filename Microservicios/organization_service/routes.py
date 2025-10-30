"""Organization service exposing organization management endpoints."""
from __future__ import annotations

import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response
from .models import Organization

bp = Blueprint("organization", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "organization", "status": "healthy"})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_organizations() -> "Response":
    organizations = [o.to_dict() for o in Organization.query.all()]
    return render_response({"organizations": organizations}, meta={"total": len(organizations)})


@bp.route("", methods=["POST"])
@require_auth(required_roles=["admin"])
def create_organization() -> "Response":
    payload, _ = parse_request_data(request)
    name = payload.get("name")
    code = payload.get("code")
    if not name or not code:
        raise APIError("name and code are required", status_code=400, error_id="HG-ORG-VALIDATION")

    new_org = Organization(name=name, code=code)

    db.session.add(new_org)
    db.session.commit()

    return render_response({"organization": new_org.to_dict()}, status_code=201)


@bp.route("/<org_id>", methods=["GET"])
@require_auth(optional=True)
def get_organization(org_id: str) -> "Response":
    org = Organization.query.get(org_id)
    if not org:
        raise APIError("Organization not found", status_code=404, error_id="HG-ORG-NOT-FOUND")
    return render_response({"organization": org.to_dict()})


@bp.route("/invitations", methods=["GET"])
@require_auth(optional=True)
def list_invitations() -> "Response":
    # This would query the 'org_invitations' table in a real application.
    return render_response({"invitations": []}, meta={"total": 0})


@bp.route("/invitations", methods=["POST"])
@require_auth(required_roles=["admin", "org_admin"])
def create_invitation() -> "Response":
    # This would create a new entry in the 'org_invitations' table.
    payload, _ = parse_request_data(request)
    email = payload.get("email")
    if not email:
        raise APIError("email is required", status_code=400, error_id="HG-ORG-VALIDATION")

    # Placeholder for the new invitation
    new_invitation = {"id": str(uuid.uuid4()), "email": email}

    return render_response({"invitation": new_invitation}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/organization")
