"""Organization service exposing organization management endpoints."""
from __future__ import annotations

import copy
import datetime as dt
from typing import Dict, List

from flask import Blueprint, request

from common.auth import require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("organization", __name__)

ORGANIZATION_PROFILE: Dict[str, Dict] = {
    "default": {
        "id": "org-1",
        "name": "HeartGuard Inc.",
        "website": "https://heartguard.example.com",
        "policy_version": "2024-01",
        "support_email": "support@heartguard.example.com",
        "logo_url": "https://cdn.heartguard.example.com/logo.png",
    }
}

ORG_INVITATIONS: List[Dict] = [
    {
        "id": "inv-1",
        "email": "new-clinician@example.com",
        "role": "clinician",
        "expires_at": (dt.datetime.utcnow() + dt.timedelta(days=7)).isoformat() + "Z",
    }
]


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "organization", "status": "healthy"})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def get_profile() -> "Response":
    profile = copy.deepcopy(ORGANIZATION_PROFILE["default"])
    return render_response({"organization": profile})


@bp.route("", methods=["PUT"])
@require_auth(required_roles=["admin", "org_admin"])
def update_profile() -> "Response":
    payload, _ = parse_request_data(request)
    profile = ORGANIZATION_PROFILE["default"]
    profile.update({k: v for k, v in payload.items() if k in profile})
    profile["updated_at"] = dt.datetime.utcnow().isoformat() + "Z"
    return render_response({"organization": profile})


@bp.route("/invitations", methods=["GET"])
@require_auth(optional=True)
def list_invitations() -> "Response":
    return render_response({"invitations": ORG_INVITATIONS}, meta={"total": len(ORG_INVITATIONS)})


@bp.route("/invitations", methods=["POST"])
@require_auth(required_roles=["admin", "org_admin"])
def create_invitation() -> "Response":
    payload, _ = parse_request_data(request)
    email = payload.get("email")
    role = payload.get("role", "user")
    if not email:
        raise APIError("email is required", status_code=400, error_id="HG-ORG-VALIDATION")
    invitation = {
        "id": f"inv-{len(ORG_INVITATIONS) + 1}",
        "email": email,
        "role": role,
        "expires_at": (dt.datetime.utcnow() + dt.timedelta(days=7)).isoformat() + "Z",
    }
    ORG_INVITATIONS.append(invitation)
    return render_response({"invitation": invitation}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/organization")
