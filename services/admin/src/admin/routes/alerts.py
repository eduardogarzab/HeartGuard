"""Alert management endpoints."""
from __future__ import annotations

from flask import Blueprint, Request, request

from ..auth import AuthContext, require_org_admin
from ..repositories.alerts import AlertsRepository
from ..repositories.patients import PatientsRepository
from ..request_utils import parse_payload
from ..xml import xml_error_response, xml_response

bp = Blueprint("alerts", __name__, url_prefix="/admin/organizations/<org_id>/alerts")
_repo = AlertsRepository()
_patients_repo = PatientsRepository()


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


@bp.post("/")
@require_org_admin
def create_alert(org_id: str):
    _auth_context(request)
    payload = parse_payload(request)
    patient_id = _trim(payload.get("patient_id"))
    alert_type_code = _trim(payload.get("alert_type_code"))
    alert_level_code = _trim(payload.get("alert_level_code"))
    status_code = _trim(payload.get("status_code"))
    description = _clean_text(payload.get("description"))
    model_id = _trim(payload.get("model_id"))
    inference_id = _trim(payload.get("inference_id"))
    wkt = _location_wkt(payload)
    if ("latitude" in payload or "longitude" in payload) and wkt is None:
        return xml_error_response("invalid_input", "Latitude/longitude are invalid", status=400)

    error = _ensure_patient(org_id, patient_id)
    if error:
        return error
    if not alert_type_code:
        return xml_error_response("invalid_input", "alert_type_code is required", status=400)
    if not alert_level_code:
        return xml_error_response("invalid_input", "alert_level_code is required", status=400)
    if not status_code:
        return xml_error_response("invalid_input", "status_code is required", status=400)

    created = _repo.create_alert(
        patient_id,
        alert_type_code=alert_type_code,
        alert_level_code=alert_level_code,
        status_code=status_code,
        description=description,
        model_id=model_id,
        inference_id=inference_id,
        location_wkt=wkt,
    )
    if not created:
        return xml_error_response("create_failed", "Alert could not be created", status=500)
    detail = _repo.get_alert(org_id, created.get("id"))
    return xml_response({"alert": detail or created}, status=201)


@bp.patch("/<alert_id>")
@require_org_admin
def update_alert_details(org_id: str, alert_id: str):
    _auth_context(request)
    existing = _repo.get_alert(org_id, alert_id)
    if not existing:
        return xml_error_response("not_found", "Alert not found", status=404)

    payload = parse_payload(request)
    patient_id = existing.get("patient_id")
    if "patient_id" in payload:
        new_patient_id = _trim(payload.get("patient_id"))
        if not new_patient_id:
            return xml_error_response("invalid_input", "patient_id cannot be empty", status=400)
        if new_patient_id != patient_id:
            return xml_error_response("invalid_input", "patient_id cannot be changed", status=400)

    alert_type_code = _trim(payload.get("alert_type_code")) or existing.get("type_code")
    alert_level_code = _trim(payload.get("alert_level_code")) or existing.get("level_code")
    status_code = _trim(payload.get("status_code")) or existing.get("status_code")
    description = (
        _clean_text(payload.get("description"))
        if "description" in payload
        else existing.get("description")
    )
    model_id = (
        _trim(payload.get("model_id"))
        if "model_id" in payload
        else existing.get("created_by_model_id")
    )
    inference_id = (
        _trim(payload.get("inference_id"))
        if "inference_id" in payload
        else existing.get("source_inference_id")
    )
    wkt = None
    if any(key in payload for key in ("location_wkt", "latitude", "longitude")):
        wkt = _location_wkt(payload)
        if ("latitude" in payload or "longitude" in payload) and wkt is None:
            return xml_error_response("invalid_input", "Latitude/longitude are invalid", status=400)

    updated = _repo.update_alert(
        alert_id,
        alert_type_code=alert_type_code,
        alert_level_code=alert_level_code,
        status_code=status_code,
        description=description,
        model_id=model_id,
        inference_id=inference_id,
        location_wkt=wkt,
    )
    if not updated:
        return xml_error_response("update_failed", "Alert could not be updated", status=500)
    detail = _repo.get_alert(org_id, alert_id)
    return xml_response({"alert": detail or updated})


@bp.delete("/<alert_id>")
@require_org_admin
def delete_alert(org_id: str, alert_id: str):
    _auth_context(request)
    alert = _repo.get_alert(org_id, alert_id)
    if not alert:
        return xml_error_response("not_found", "Alert not found", status=404)
    deleted = _repo.delete_alert(alert_id)
    if not deleted:
        return xml_error_response("delete_failed", "Alert could not be deleted", status=500)
    return xml_response({"deleted": True})


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


def _trim(value: object) -> str | None:
    if value is None:
        return None
    return str(value).strip() or None


def _ensure_patient(org_id: str, patient_id: str | None):
    if not patient_id:
        return xml_error_response("invalid_input", "patient_id is required", status=400)
    patient = _patients_repo.get_patient(patient_id)
    if not patient:
        return xml_error_response("not_found", "Patient not found", status=404)
    if str(patient.get("org_id")) != org_id:
        return xml_error_response("forbidden", "Patient does not belong to this organization", status=403)
    return None


def _location_wkt(payload: dict[str, object]) -> str | None:
    wkt = _trim(payload.get("location_wkt"))
    lat = payload.get("latitude")
    lon = payload.get("longitude")
    if wkt:
        return wkt
    if lat is None or lon is None:
        return None
    try:
        latitude = float(str(lat).strip())
        longitude = float(str(lon).strip())
    except (TypeError, ValueError):
        return None
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None
    return f"POINT({longitude} {latitude})"
