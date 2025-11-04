"""Device management endpoints."""
from __future__ import annotations

from flask import Blueprint, Request, request

from ..auth import AuthContext, require_org_admin
from ..repositories.devices import DevicesRepository
from ..repositories.patients import PatientsRepository
from ..request_utils import parse_payload
from ..xml import xml_error_response, xml_response

bp = Blueprint("devices", __name__, url_prefix="/admin/organizations/<org_id>/devices")
_repo = DevicesRepository()
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


def _coerce_bool(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "t", "yes", "y"}:
        return True
    if lowered in {"0", "false", "f", "no", "n"}:
        return False
    return default


def _trim(value: object) -> str | None:
    if value is None:
        return None
    return str(value).strip() or None


def _validate_patient(org_id: str, patient_id: str | None):
    if not patient_id:
        return None
    patient = _patients_repo.get_patient(patient_id)
    if not patient:
        return xml_error_response("not_found", "Patient not found", status=404)
    if str(patient.get("org_id")) != org_id:
        return xml_error_response("forbidden", "Patient does not belong to this organization", status=403)
    return None


@bp.get("/")
@require_org_admin
def list_devices(org_id: str):
    limit = _coerce_int(request.args.get("limit"), default=50, minimum=1, maximum=200)
    offset = _coerce_int(request.args.get("offset"), default=0, minimum=0)
    active_param = request.args.get("active")
    active = None
    if active_param is not None and active_param.strip() != "":
        active = _coerce_bool(active_param, default=True)
    devices = _repo.list_for_org(org_id, limit=limit, offset=offset, active=active)
    return xml_response({"devices": devices})


@bp.get("/<device_id>")
@require_org_admin
def get_device(org_id: str, device_id: str):
    device = _repo.get(org_id, device_id)
    if not device:
        return xml_error_response("not_found", "Device not found", status=404)
    return xml_response({"device": device})


@bp.post("/")
@require_org_admin
def create_device(org_id: str):
    _auth_context(request)
    payload = parse_payload(request)
    serial = _trim(payload.get("serial"))
    device_type_code = _trim(payload.get("device_type_code"))
    brand = _trim(payload.get("brand"))
    model = _trim(payload.get("model"))
    owner_patient_id = _trim(payload.get("owner_patient_id"))
    active = _coerce_bool(payload.get("active"), default=True)

    if not serial:
        return xml_error_response("invalid_input", "Serial is required", status=400)
    if not device_type_code:
        return xml_error_response("invalid_input", "Device type code is required", status=400)

    error_response = _validate_patient(org_id, owner_patient_id)
    if error_response:
        return error_response

    device = _repo.create(
        org_id,
        serial=serial,
        device_type_code=device_type_code,
        brand=brand,
        model=model,
        owner_patient_id=owner_patient_id,
        active=active,
    )
    if not device:
        return xml_error_response("create_failed", "Device could not be created", status=500)
    return xml_response({"device": device}, status=201)


@bp.patch("/<device_id>")
@require_org_admin
def update_device(org_id: str, device_id: str):
    _auth_context(request)
    existing = _repo.get(org_id, device_id)
    if not existing:
        return xml_error_response("not_found", "Device not found", status=404)

    payload = parse_payload(request)
    serial = _trim(payload.get("serial")) or existing.get("serial")
    device_type_code = _trim(payload.get("device_type_code")) or existing.get("device_type_code")
    brand = _trim(payload.get("brand")) if "brand" in payload else existing.get("brand")
    model = _trim(payload.get("model")) if "model" in payload else existing.get("model")
    owner_patient_id = _trim(payload.get("owner_patient_id")) if "owner_patient_id" in payload else existing.get("owner_patient_id")
    active = _coerce_bool(payload.get("active"), default=bool(existing.get("active")))

    if not serial:
        return xml_error_response("invalid_input", "Serial is required", status=400)
    if not device_type_code:
        return xml_error_response("invalid_input", "Device type code is required", status=400)

    error_response = _validate_patient(org_id, owner_patient_id)
    if error_response:
        return error_response

    updated = _repo.update(
        org_id,
        device_id,
        serial=serial,
        device_type_code=device_type_code,
        brand=brand,
        model=model,
        owner_patient_id=owner_patient_id,
        active=active,
    )
    if not updated:
        return xml_error_response("update_failed", "Device could not be updated", status=500)
    return xml_response({"device": updated})


@bp.delete("/<device_id>")
@require_org_admin
def delete_device(org_id: str, device_id: str):
    _auth_context(request)
    existing = _repo.get(org_id, device_id)
    if not existing:
        return xml_error_response("not_found", "Device not found", status=404)
    deleted = _repo.delete(device_id)
    if not deleted:
        return xml_error_response("delete_failed", "Device could not be deleted", status=500)
    return xml_response({"deleted": True})
