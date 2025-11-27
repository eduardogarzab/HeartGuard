"""Organization related endpoints."""
from __future__ import annotations

from flask import Blueprint, Request, request

from ..auth import AuthContext, require_org_admin
from ..repositories.organizations import OrganizationsRepository
from ..xml import xml_error_response, xml_response

bp = Blueprint("organizations", __name__, url_prefix="/admin/organizations")
_repo = OrganizationsRepository()


def _auth_context(req: Request) -> AuthContext:
    ctx = getattr(req, "auth_context", None)
    if ctx is None:
        raise RuntimeError("auth context missing")
    return ctx


@bp.get("/")
@require_org_admin
def list_organizations():
    ctx = _auth_context(request)
    items = _repo.list_for_user(ctx.user_id)
    return xml_response({"organizations": items})


@bp.get("/<org_id>")
@require_org_admin
def organization_detail(org_id: str):
    org = _repo.get(org_id)
    if not org:
        return xml_error_response("not_found", "Organization not found", status=404)
    stats = _repo.stats(org_id)
    payload = {"organization": org, "stats": stats}
    return xml_response(payload)
