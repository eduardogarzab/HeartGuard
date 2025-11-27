"""Patient location endpoints for organization administrators."""
from __future__ import annotations

from flask import Blueprint, Request, request

from ..auth import AuthContext, require_org_admin
from ..repositories.patient_locations import PatientLocationsRepository
from ..repositories.patients import PatientsRepository
from ..request_utils import parse_payload
from ..xml import xml_error_response, xml_response

bp = Blueprint(
    "patient_locations",
    __name__,
    url_prefix="/admin/organizations/<org_id>/patients/<patient_id>/locations",
)
_repo = PatientLocationsRepository()
_patients_repo = PatientsRepository()


def _auth_context(req: Request) -> AuthContext:
    ctx = getattr(req, "auth_context", None)
    if ctx is None:
        raise RuntimeError("auth context missing")
    return ctx


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


def _trim(value: object) -> str | None:
    if value is None:
        return None
    return str(value).strip() or None


def _ensure_patient(org_id: str, patient_id: str | None):
    if not patient_id:
        return xml_error_response("invalid_input", "Patient id is required", status=400)
    patient = _patients_repo.get_patient(patient_id)
    if not patient:
        return xml_error_response("not_found", "Patient not found", status=404)
    if str(patient.get("org_id")) != org_id:
        return xml_error_response("forbidden", "Patient does not belong to this organization", status=403)
    return None


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


@bp.get("/")
@require_org_admin
def list_locations(org_id: str, patient_id: str):
    error = _ensure_patient(org_id, patient_id)
    if error:
        return error
    limit = _coerce_int(request.args.get("limit"), default=100, minimum=1, maximum=200)
    offset = _coerce_int(request.args.get("offset"), default=0, minimum=0)
    locations = _repo.list_for_patient(patient_id, limit=limit, offset=offset)
    return xml_response({"locations": locations})


@bp.post("/")
@require_org_admin
def create_location(org_id: str, patient_id: str):
    _auth_context(request)
    error = _ensure_patient(org_id, patient_id)
    if error:
        return error
    payload = parse_payload(request)
    latitude = _to_float(payload.get("latitude"))
    longitude = _to_float(payload.get("longitude"))
    timestamp = _trim(payload.get("timestamp"))
    source = _trim(payload.get("source"))
    accuracy = _to_float(payload.get("accuracy_m"))

    if latitude is None or longitude is None:
        return xml_error_response("invalid_input", "Latitude and longitude are required", status=400)
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return xml_error_response("invalid_input", "Latitude/longitude out of range", status=400)

    created = _repo.create(
        patient_id,
        latitude=latitude,
        longitude=longitude,
        timestamp=timestamp,
        source=source,
        accuracy_m=accuracy,
    )
    if not created:
        return xml_error_response("create_failed", "Location could not be created", status=500)
    return xml_response({"location": created}, status=201)


@bp.delete("/<location_id>")
@require_org_admin
def delete_location(org_id: str, patient_id: str, location_id: str):
    _auth_context(request)
    error = _ensure_patient(org_id, patient_id)
    if error:
        return error
    deleted = _repo.delete(patient_id, location_id)
    if not deleted:
        return xml_error_response("not_found", "Location not found", status=404)
    return xml_response({"deleted": True})
