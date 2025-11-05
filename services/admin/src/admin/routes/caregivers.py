"""Caregiver assignment endpoints."""
from __future__ import annotations

from flask import Blueprint, request

from ..auth import require_org_admin
from ..repositories.caregivers import CaregiversRepository
from ..request_utils import parse_payload
from ..xml import xml_error_response, xml_response

bp = Blueprint("caregivers", __name__, url_prefix="/admin/organizations/<org_id>/caregivers")
_repo = CaregiversRepository()


@bp.get("/relationship-types")
@require_org_admin
def list_relationship_types(org_id: str):
    types_ = _repo.list_relationship_types()
    return xml_response({"relationship_types": types_})


@bp.get("/assignments")
@require_org_admin
def list_assignments(org_id: str):
    assignments = _repo.list_assignments(org_id)
    return xml_response({"assignments": assignments})


@bp.post("/assignments")
@require_org_admin
def create_assignment(org_id: str):
    payload = parse_payload(request)
    patient_id = (payload.get("patient_id") or "").strip()
    caregiver_id = (payload.get("caregiver_id") or "").strip()
    relationship_type_id = _clean_value(payload.get("relationship_type_id"))
    is_primary = _to_bool(payload.get("is_primary"), default=False)
    started_at = _clean_value(payload.get("started_at"))
    ended_at = _clean_value(payload.get("ended_at"))
    note = _clean_value(payload.get("note"))

    if not patient_id or not caregiver_id:
        return xml_error_response("invalid_input", "patient_id and caregiver_id are required", status=400)

    assignment = _repo.create_assignment(
        org_id,
        patient_id,
        caregiver_id,
        relationship_type_id=relationship_type_id,
        is_primary=is_primary,
        started_at=started_at,
        ended_at=ended_at,
        note=note,
    )
    if not assignment:
        return xml_error_response("create_failed", "Assignment could not be created", status=400)
    return xml_response({"assignment": assignment}, status=201)


@bp.patch("/assignments/<patient_id>/<caregiver_id>")
@require_org_admin
def update_assignment(org_id: str, patient_id: str, caregiver_id: str):
    payload = parse_payload(request)
    relationship_type_id_raw = payload.get("relationship_type_id")
    clear_relationship = relationship_type_id_raw == "" or relationship_type_id_raw == "__clear__"
    relationship_type_id = _clean_value(relationship_type_id_raw)
    is_primary = _to_optional_bool(payload.get("is_primary"))
    started_at = _clean_value(payload.get("started_at"))
    ended_at = _clean_value(payload.get("ended_at"))
    note = _clean_value(payload.get("note"))

    assignment = _repo.update_assignment(
        org_id,
        patient_id,
        caregiver_id,
        relationship_type_id=relationship_type_id,
        clear_relationship=clear_relationship,
        is_primary=is_primary,
        started_at=started_at,
        ended_at=ended_at,
        note=note,
    )
    if not assignment:
        return xml_error_response("not_found", "Assignment not found", status=404)
    return xml_response({"assignment": assignment})


@bp.delete("/assignments/<patient_id>/<caregiver_id>")
@require_org_admin
def delete_assignment(org_id: str, patient_id: str, caregiver_id: str):
    _repo.delete_assignment(org_id, patient_id, caregiver_id)
    return xml_response({"deleted": True})


def _clean_value(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed or None
    return str(value)


def _to_bool(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def _to_optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"", "null", "none"}:
        return None
    if lowered in {"1", "true", "t", "yes", "y"}:
        return True
    if lowered in {"0", "false", "f", "no", "n"}:
        return False
    return None
