"""Organization service exposing organization management endpoints."""
from __future__ import annotations

import datetime as dt
import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import OrganizationInvitation, OrganizationProfile

bp = Blueprint("organization", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "organization", "status": "healthy", "invitations": OrganizationInvitation.query.count()})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def get_profile() -> "Response":
    profile = OrganizationProfile.query.get("default")
    if profile is None:
        profile = OrganizationProfile(
            id="default",
            name="HeartGuard Inc.",
            website="https://heartguard.example.com",
            policy_version="2024-01",
            support_email="support@heartguard.example.com",
            logo_url="https://cdn.heartguard.example.com/logo.png",
        )
        db.session.add(profile)
        db.session.commit()
    return render_response({"organization": _serialize_profile(profile)})


@bp.route("", methods=["PUT"])
@require_auth(required_roles=["admin", "org_admin"])
def update_profile() -> "Response":
    payload, _ = parse_request_data(request)
    profile = OrganizationProfile.query.get("default")
    if profile is None:
        raise APIError("Organization profile not found", status_code=404, error_id="HG-ORG-NOT-FOUND")
    for field in ["name", "website", "policy_version", "support_email", "logo_url"]:
        if field in payload:
            setattr(profile, field, payload[field])
    profile.updated_at = dt.datetime.utcnow()
    db.session.commit()
    return render_response({"organization": _serialize_profile(profile)})


@bp.route("/invitations", methods=["GET"])
@require_auth(optional=True)
def list_invitations() -> "Response":
    invitations = [
        _serialize_invitation(invitation)
        for invitation in OrganizationInvitation.query.order_by(OrganizationInvitation.created_at.desc()).all()
    ]
    return render_response({"invitations": invitations}, meta={"total": len(invitations)})


@bp.route("/invitations", methods=["POST"])
@require_auth(required_roles=["admin", "org_admin"])
def create_invitation() -> "Response":
    payload, _ = parse_request_data(request)
    email = payload.get("email")
    role = payload.get("role", "user")
    if not email:
        raise APIError("email is required", status_code=400, error_id="HG-ORG-VALIDATION")
    invitation = OrganizationInvitation(
        id=f"inv-{uuid.uuid4()}",
        email=email,
        role=role,
        expires_at=dt.datetime.utcnow() + dt.timedelta(days=7),
    )
    db.session.add(invitation)
    db.session.commit()
    return render_response({"invitation": _serialize_invitation(invitation)}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/organization")


def _serialize_profile(profile: OrganizationProfile) -> dict:
    return {
        "id": profile.id,
        "name": profile.name,
        "website": profile.website,
        "policy_version": profile.policy_version,
        "support_email": profile.support_email,
        "logo_url": profile.logo_url,
        "updated_at": (profile.updated_at or dt.datetime.utcnow()).isoformat() + "Z",
    }


def _serialize_invitation(invitation: OrganizationInvitation) -> dict:
    return {
        "id": invitation.id,
        "email": invitation.email,
        "role": invitation.role,
        "expires_at": invitation.expires_at.isoformat() + "Z",
        "created_at": invitation.created_at.isoformat() + "Z",
    }
