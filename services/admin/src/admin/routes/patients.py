"""Patient management endpoints."""
from __future__ import annotations

from flask import Blueprint, request

from ..auth import require_org_admin
from ..repositories.patients import PatientsRepository
from ..xml import xml_error_response, xml_response
from ..request_utils import parse_payload

bp = Blueprint("patients", __name__, url_prefix="/admin/organizations/<org_id>/patients")
_repo = PatientsRepository()


def _validate_org(patient: dict[str, object] | None, org_id: str):
    if not patient:
        return xml_error_response("not_found", "Patient not found", status=404)
    if str(patient.get("org_id")) != org_id:
        return xml_error_response("forbidden", "Patient does not belong to this organization", status=403)
    return None


@bp.get("/")
@require_org_admin
def list_patients(org_id: str):
    patients = _repo.list_by_org(org_id)
    return xml_response({"patients": patients})


@bp.post("/")
@require_org_admin
def create_patient(org_id: str):
    payload = parse_payload(request)
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or payload.get("raw_password")
    birthdate = payload.get("birthdate")
    risk_level_id = payload.get("risk_level_id")

    if not name:
        return xml_error_response("invalid_input", "Name is required", status=400)
    if not email:
        return xml_error_response("invalid_input", "Email is required", status=400)
    if not password:
        return xml_error_response("invalid_input", "Password is required", status=400)

    patient = _repo.create_patient(
        org_id=org_id,
        name=name,
        email=email,
        raw_password=password,
        birthdate=birthdate,
        risk_level_id=risk_level_id,
    )

    error_response = _validate_org(patient, org_id)
    if error_response:
        return error_response

    return xml_response({"patient": patient}, status=201)


@bp.get("/<patient_id>")
@require_org_admin
def get_patient(org_id: str, patient_id: str):
    patient = _repo.get_patient(patient_id)
    error_response = _validate_org(patient, org_id)
    if error_response:
        return error_response
    return xml_response({"patient": patient})


@bp.patch("/<patient_id>")
@require_org_admin
def update_patient(org_id: str, patient_id: str):
    payload = parse_payload(request)
    patient = _repo.get_patient(patient_id)
    error_response = _validate_org(patient, org_id)
    if error_response:
        return error_response

    updated = _repo.update_patient(
        patient_id,
        name=(payload.get("name") or None),
        birthdate=payload.get("birthdate"),
        risk_level_id=payload.get("risk_level_id"),
    )
    if not updated:
        return xml_error_response("update_failed", "Patient could not be updated", status=500)
    return xml_response({"patient": updated})


@bp.delete("/<patient_id>")
@require_org_admin
def delete_patient(org_id: str, patient_id: str):
    patient = _repo.get_patient(patient_id)
    error_response = _validate_org(patient, org_id)
    if error_response:
        return error_response
    _repo.delete_patient(patient_id)
    return xml_response({"deleted": True})
