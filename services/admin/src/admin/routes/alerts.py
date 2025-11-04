"""Alert management endpoints."""
from __future__ import annotations

from flask import Blueprint, Request, request

from ..auth import AuthContext, require_org_admin
from ..repositories.alerts import AlertsRepository
from ..request_utils import parse_payload
from ..xml import xml_error_response, xml_response

bp = Blueprint("alerts", __name__, url_prefix="/admin/organizations/<org_id>/alerts")
_repo = AlertsRepository()


def _auth_context(req: Request) -> AuthContext:
    ctx = getattr(req, "auth_context", None)
    if ctx is None:
        raise RuntimeError("auth context missing")
    return ctx


@bp.get("/")
@require_org_admin
def list_alerts(org_id: str):
    status_code = request.args.get("status")
    level_code = request.args.get("level")
    limit = _coerce_int(request.args.get("limit"), default=50, minimum=1, maximum=200)
    offset = _coerce_int(request.args.get("offset"), default=0, minimum=0)
    from_ts = request.args.get("from")
    to_ts = request.args.get("to")

    alerts = _repo.list_alerts(
        org_id,
        status_code=status_code,
        level_code=level_code,
        limit=limit,
        offset=offset,
        from_ts=from_ts,
        to_ts=to_ts,
    )
    return xml_response({"alerts": alerts})


@bp.get("/<alert_id>")
@require_org_admin
def get_alert(org_id: str, alert_id: str):
    alert = _repo.get_alert(org_id, alert_id)
    if not alert:
        return xml_error_response("not_found", "Alert not found", status=404)
    acks = _repo.list_acks(alert_id)
    resolutions = _repo.list_resolutions(alert_id)
    payload = {
        "alert": alert,
        "acks": acks,
        "resolutions": resolutions,
    }
    return xml_response(payload)


@bp.post("/<alert_id>/ack")
@require_org_admin
def acknowledge_alert(org_id: str, alert_id: str):
    auth_ctx = _auth_context(request)
    alert = _repo.get_alert(org_id, alert_id)
    if not alert:
        return xml_error_response("not_found", "Alert not found", status=404)
    payload = parse_payload(request)
    note = _clean_text(payload.get("note"))
    ack = _repo.acknowledge(alert_id, auth_ctx.user_id, note)
    if not ack:
        return xml_error_response("create_failed", "Acknowledgement could not be stored", status=500)
    return xml_response({"ack": ack}, status=201)


@bp.post("/<alert_id>/resolve")
@require_org_admin
def resolve_alert(org_id: str, alert_id: str):
    auth_ctx = _auth_context(request)
    alert = _repo.get_alert(org_id, alert_id)
    if not alert:
        return xml_error_response("not_found", "Alert not found", status=404)
    payload = parse_payload(request)
    outcome = _clean_text(payload.get("outcome"))
    note = _clean_text(payload.get("note"))
    resolution = _repo.resolve(alert_id, auth_ctx.user_id, outcome, note)
    if not resolution:
        return xml_error_response("create_failed", "Resolution could not be stored", status=500)
    return xml_response({"resolution": resolution}, status=201)


def _coerce_int(value: str | None, *, default: int, minimum: int, maximum: int | None = None) -> int:
    if value is None or value.strip() == "":
        result = default
    else:
        try:
            result = int(value)
        except ValueError:
            result = default
    if result < minimum:
        result = minimum
    if maximum is not None and result > maximum:
        result = maximum
    return result


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed or None
    return str(value)
