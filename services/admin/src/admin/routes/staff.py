"""Staff management endpoints."""
from __future__ import annotations

from flask import Blueprint, Request, request

from ..auth import AuthContext, require_org_admin
from ..repositories.staff import StaffRepository
from ..request_utils import parse_payload
from ..xml import xml_error_response, xml_response

bp = Blueprint("staff", __name__, url_prefix="/admin/organizations/<org_id>/staff")
_repo = StaffRepository()


def _auth_context(req: Request) -> AuthContext:
    ctx = getattr(req, "auth_context", None)
    if ctx is None:
        raise RuntimeError("auth context missing")
    return ctx


@bp.get("/")
@require_org_admin
def list_staff(org_id: str):
    members = _repo.list_members(org_id)
    return xml_response({"staff_members": members})


@bp.get("/invitations")
@require_org_admin
def list_invitations(org_id: str):
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    invitations = _repo.list_invitations(org_id, limit=limit, offset=offset)
    return xml_response({"invitations": invitations})


@bp.post("/invitations")
@require_org_admin
def create_invitation(org_id: str):
    ctx = _auth_context(request)
    payload = parse_payload(request)
    email = (payload.get("email") or "").strip().lower()
    role_code = (payload.get("role_code") or "").strip()
    ttl_hours_raw = payload.get("ttl_hours")
    ttl_hours = _coerce_int(ttl_hours_raw) if ttl_hours_raw is not None else None

    if not email:
        return xml_error_response("invalid_input", "Email is required", status=400)
    if not role_code:
        return xml_error_response("invalid_input", "Role code is required", status=400)
    
    # Validate that only org_admin and org_viewer roles are allowed
    if role_code not in ("org_admin", "org_viewer"):
        return xml_error_response("invalid_input", "Only org_admin and org_viewer roles are allowed", status=400)

    invitation = _repo.create_invitation(org_id, ctx.user_id, email, role_code, ttl_hours)
    return xml_response({"invitation": invitation}, status=201)


@bp.delete("/invitations/<invitation_id>")
@require_org_admin
def revoke_invitation(org_id: str, invitation_id: str):
    """Revoke an invitation. Must be defined before generic /<user_id> route."""
    _repo.revoke_invitation(org_id, invitation_id)
    return xml_response({"revoked": True})


@bp.patch("/members/<user_id>")
@require_org_admin
def update_role(org_id: str, user_id: str):
    """Update a staff member's role."""
    payload = parse_payload(request)
    role_code = (payload.get("role_code") or "").strip()
    if not role_code:
        return xml_error_response("invalid_input", "Role code is required", status=400)
    _repo.update_role(org_id, user_id, role_code)
    return xml_response({"updated": True})


@bp.delete("/members/<user_id>")
@require_org_admin
def remove_member(org_id: str, user_id: str):
    """Remove a staff member from the organization."""
    _repo.remove_member(org_id, user_id)
    return xml_response({"deleted": True})


def _coerce_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None
