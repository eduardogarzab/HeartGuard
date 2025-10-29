"""Read-only reporting endpoints."""

from __future__ import annotations

from flask import Blueprint, g, request

from repository import RepositoryError, get_overview_metrics
from utils import create_response, require_auth

bp = Blueprint("analytics_reports", __name__, url_prefix="/v1/metrics")


@bp.get("/overview")
@require_auth
def overview_metrics():
    """Return aggregated activity metrics for admins and superadmins."""

    if g.role not in {"admin", "superadmin"}:
        return create_response(message="Forbidden", status_code=403)

    requested_org = request.args.get("org_id") if g.role == "superadmin" else g.org_id

    try:
        metrics = get_overview_metrics(requested_org, is_superadmin=(g.role == "superadmin"))
    except RepositoryError as exc:
        return create_response(message=str(exc), status_code=400)

    return create_response(data=metrics)

