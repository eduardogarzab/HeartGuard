"""Dashboard endpoints for organization administrators."""
from __future__ import annotations

from flask import Blueprint, request

from ..auth import require_org_admin
from ..repositories.analytics import AnalyticsRepository
from ..repositories.organizations import OrganizationsRepository
from ..xml import xml_error_response, xml_response

bp = Blueprint("dashboard", __name__, url_prefix="/admin/organizations/<org_id>/dashboard")
_org_repo = OrganizationsRepository()
_analytics_repo = AnalyticsRepository()


@bp.get("/")
@require_org_admin
def organization_dashboard(org_id: str):
    org = _org_repo.get(org_id)
    if not org:
        return xml_error_response("not_found", "Organization not found", status=404)

    stats = _org_repo.stats(org_id)
    days = _parse_days(request.args.get("days"))

    risk_levels = _analytics_repo.patient_risk_breakdown(org_id)
    device_status = _analytics_repo.device_status_breakdown(org_id)
    alert_outcomes = _analytics_repo.alert_outcome_breakdown(org_id, days=days)
    response_stats = _analytics_repo.alert_response_stats(org_id, days=days)
    alerts_created = _analytics_repo.alerts_created_count(org_id, days=days)
    invitation_status = _analytics_repo.invitation_status_breakdown(org_id)

    payload = {
        "organization": org,
        "stats": stats,
        "period_days": days,
        "risk_levels": risk_levels,
        "device_status": device_status,
        "alert_outcomes": alert_outcomes,
        "response_stats": response_stats,
        "alerts_created": alerts_created,
        "invitation_status": invitation_status,
    }
    return xml_response(payload, root="dashboard")


def _parse_days(value: str | None) -> int:
    if not value:
        return 30
    try:
        parsed = int(value)
    except ValueError:
        return 30
    return max(parsed, 1)
