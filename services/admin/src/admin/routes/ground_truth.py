"""Ground truth label endpoints for organization administrators."""
from __future__ import annotations

from flask import Blueprint, Request, request

from ..auth import AuthContext, require_org_admin
from .. import db
from ..repositories.ground_truth import GroundTruthRepository
from ..repositories.patients import PatientsRepository
from ..request_utils import parse_payload
from ..xml import xml_error_response, xml_response

bp = Blueprint(
    "ground_truth",
    __name__,
    url_prefix="/admin/organizations/<org_id>/patients/<patient_id>/ground-truth",
)
_repo = GroundTruthRepository()
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


def _ensure_org_member(org_id: str, user_id: str | None):
    if not user_id:
        return None
    query = """
        SELECT 1
        FROM user_org_membership
        WHERE org_id = %(org_id)s AND user_id = %(user_id)s
        LIMIT 1
    """
    result = db.fetch_one(query, {"org_id": org_id, "user_id": user_id})
    if result is None:
        return xml_error_response("forbidden", "User is not part of this organization", status=403)
    return None


@bp.get("/")
@require_org_admin
def list_ground_truth(org_id: str, patient_id: str):
    error = _ensure_patient(org_id, patient_id)
    if error:
        return error
    limit = _coerce_int(request.args.get("limit"), default=100, minimum=1, maximum=200)
    offset = _coerce_int(request.args.get("offset"), default=0, minimum=0)
    labels = _repo.list_for_patient(patient_id, limit=limit, offset=offset)
    return xml_response({"ground_truth_labels": labels})


@bp.post("/")
@require_org_admin
def create_ground_truth(org_id: str, patient_id: str):
    _auth_context(request)
    error = _ensure_patient(org_id, patient_id)
    if error:
        return error
    payload = parse_payload(request)
    event_type_code = _trim(payload.get("event_type_code"))
    onset = _trim(payload.get("onset"))
    offset_at = _trim(payload.get("offset_at"))
    annotated_by_user_id = _trim(payload.get("annotated_by_user_id"))
    source = _trim(payload.get("source"))
    note = _trim(payload.get("note"))

    if not event_type_code:
        return xml_error_response("invalid_input", "Event type code is required", status=400)
    if not onset:
        return xml_error_response("invalid_input", "Onset timestamp is required", status=400)

    error = _ensure_org_member(org_id, annotated_by_user_id)
    if error:
        return error

    event_type_id = _repo.resolve_event_type_id(event_type_code)
    if not event_type_id:
        return xml_error_response("invalid_input", "Unknown event type code", status=400)

    created = _repo.create(
        patient_id,
        event_type_id=event_type_id,
        onset=onset,
        offset_at=offset_at,
        annotated_by_user_id=annotated_by_user_id,
        source=source,
        note=note,
    )
    if not created:
        return xml_error_response("create_failed", "Ground truth label could not be created", status=500)
    label = _repo.get(created["id"])
    return xml_response({"ground_truth_label": label or created}, status=201)


@bp.patch("/<label_id>")
@require_org_admin
def update_ground_truth(org_id: str, patient_id: str, label_id: str):
    _auth_context(request)
    error = _ensure_patient(org_id, patient_id)
    if error:
        return error
    existing = _repo.get(label_id)
    if not existing or existing.get("patient_id") != patient_id:
        return xml_error_response("not_found", "Ground truth label not found", status=404)

    payload = parse_payload(request)
    event_type_code = _trim(payload.get("event_type_code")) if "event_type_code" in payload else None
    onset = _trim(payload.get("onset")) if "onset" in payload else None
    offset_at = _trim(payload.get("offset_at")) if "offset_at" in payload else None
    annotated_by_user_id = _trim(payload.get("annotated_by_user_id")) if "annotated_by_user_id" in payload else None
    source = _trim(payload.get("source")) if "source" in payload else None
    note = _trim(payload.get("note")) if "note" in payload else None

    if annotated_by_user_id is not None:
        error = _ensure_org_member(org_id, annotated_by_user_id)
        if error:
            return error

    event_type_id = None
    if event_type_code is not None:
        event_type_id = _repo.resolve_event_type_id(event_type_code)
        if not event_type_id:
            return xml_error_response("invalid_input", "Unknown event type code", status=400)

    updated = _repo.update(
        label_id,
        event_type_id=event_type_id,
        onset=onset,
        offset_at=offset_at,
        annotated_by_user_id=annotated_by_user_id,
        source=source,
        note=note,
    )
    if not updated:
        return xml_error_response("update_failed", "Ground truth label could not be updated", status=500)
    label = _repo.get(label_id)
    return xml_response({"ground_truth_label": label or updated})


@bp.delete("/<label_id>")
@require_org_admin
def delete_ground_truth(org_id: str, patient_id: str, label_id: str):
    _auth_context(request)
    error = _ensure_patient(org_id, patient_id)
    if error:
        return error
    existing = _repo.get(label_id)
    if not existing or existing.get("patient_id") != patient_id:
        return xml_error_response("not_found", "Ground truth label not found", status=404)
    deleted = _repo.delete(label_id)
    if not deleted:
        return xml_error_response("delete_failed", "Ground truth label could not be deleted", status=500)
    return xml_response({"deleted": True})
