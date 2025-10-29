"""HTTP routes for patient CRUD operations."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from repository import (
    create_patient,
    delete_patient,
    get_patient,
    list_patients,
    update_patient,
    user_belongs_to_org,
)
from responses import err, ok
from services.media import MediaServiceError, request_signed_photo

bp = Blueprint("patients", __name__, url_prefix="/v1/patients")


def _identity() -> Dict[str, Any]:
    ident = get_jwt_identity()
    if not isinstance(ident, dict) or "user_id" not in ident:
        raise ValueError("Identidad inválida")
    return ident


def _parse_birthdate(raw: Optional[str]) -> Tuple[Optional[date], Optional[str]]:
    if raw is None:
        return None, None
    if raw == "":
        return None, "empty"
    try:
        parsed = datetime.strptime(raw, "%Y-%m-%d").date()
        return parsed, None
    except ValueError:
        return None, "invalid"


def _resolve_org_id(ident: Dict[str, Any], provided: Optional[str]) -> Optional[str]:
    return provided or ident.get("org_id") or request.headers.get("X-Org-ID")


def _ensure_membership(user_id: str, org_id: Optional[str]):
    if not org_id or not user_belongs_to_org(user_id, org_id):
        raise PermissionError("No perteneces a esta organización")


def _boolean(value: Optional[str]) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _maybe_attach_signed_photo(patient: Dict[str, Any], auth_header: Optional[str], org_id: str, errors: Dict[str, str]):
    photo_path = patient.get("profile_photo_url")
    if not photo_path:
        return
    try:
        signed = request_signed_photo(photo_path, auth_header, org_id)
    except MediaServiceError as exc:
        errors[patient["id"]] = str(exc)
        return
    if signed:
        patient["profile_photo_signed_url"] = signed.url
        patient["profile_photo_expires_in"] = signed.expires_in


@bp.post("")
@jwt_required()
def create_patient_route():
    try:
        ident = _identity()
    except ValueError as exc:
        return err(str(exc), code="identity_invalid", status=401)

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return err("JSON inválido", code="invalid_json", status=400)

    org_id = _resolve_org_id(ident, payload.get("org_id"))
    if not org_id:
        return err("Organización requerida", code="org_missing", status=400)

    try:
        _ensure_membership(ident["user_id"], org_id)
    except PermissionError as exc:
        return err(str(exc), code="forbidden", status=403)

    name = (payload.get("person_name") or "").strip()
    if not name:
        return err("Nombre es requerido", code="name_required", status=400)

    birthdate_raw = payload.get("birthdate")
    birthdate, birthdate_error = _parse_birthdate(birthdate_raw)
    if birthdate_error == "invalid":
        return err("Fecha de nacimiento inválida (YYYY-MM-DD)", code="birthdate_invalid", status=400)

    sex_id = payload.get("sex_id")
    risk_level_id = payload.get("risk_level_id")
    profile_photo_url = payload.get("profile_photo_url")

    try:
        new_id = create_patient(
            org_id=org_id,
            person_name=name,
            birthdate=birthdate,
            sex_id=sex_id,
            risk_level_id=risk_level_id,
            profile_photo_url=profile_photo_url,
        )
    except Exception as exc:  # pragma: no cover - DB errors bubbled
        return err("No se pudo crear paciente", code="create_error", status=500, details={"error": str(exc)})

    patient = get_patient(new_id)
    return ok({"patient": patient}, status=201)


@bp.get("")
@jwt_required()
def list_patients_route():
    try:
        ident = _identity()
    except ValueError as exc:
        return err(str(exc), code="identity_invalid", status=401)

    limit = request.args.get("limit", type=int) or 50
    offset = request.args.get("offset", type=int) or 0
    if limit < 1 or limit > 200:
        return err("Parámetro limit inválido", code="invalid_limit", status=400)
    if offset < 0:
        return err("Parámetro offset inválido", code="invalid_offset", status=400)

    org_id = _resolve_org_id(ident, request.args.get("org_id"))
    if not org_id:
        return err("Organización requerida", code="org_missing", status=400)

    try:
        _ensure_membership(ident["user_id"], org_id)
    except PermissionError as exc:
        return err(str(exc), code="forbidden", status=403)

    patients = list_patients(org_id, limit=limit, offset=offset)

    include_signed = _boolean(request.args.get("include_photo_signed_url"))
    errors: Dict[str, str] = {}
    auth_header = request.headers.get("Authorization")
    if include_signed:
        for patient in patients:
            _maybe_attach_signed_photo(patient, auth_header, org_id, errors)

    meta = {
        "pagination": {"limit": limit, "offset": offset, "returned": len(patients)},
    }
    if errors:
        meta["photo_errors"] = errors

    return ok({"patients": patients}, meta=meta)


@bp.get("/<patient_id>")
@jwt_required()
def get_patient_route(patient_id: str):
    try:
        ident = _identity()
    except ValueError as exc:
        return err(str(exc), code="identity_invalid", status=401)

    patient = get_patient(patient_id)
    if not patient:
        return err("Paciente no encontrado", code="not_found", status=404)

    org_id = patient.get("org_id")
    try:
        _ensure_membership(ident["user_id"], org_id)
    except PermissionError as exc:
        return err(str(exc), code="forbidden", status=403)

    include_signed = _boolean(request.args.get("include_photo_signed_url"))
    errors: Dict[str, str] = {}
    if include_signed:
        _maybe_attach_signed_photo(patient, request.headers.get("Authorization"), org_id, errors)

    meta = {"photo_errors": errors} if errors else None
    return ok({"patient": patient}, meta=meta)


@bp.patch("/<patient_id>")
@jwt_required()
def update_patient_route(patient_id: str):
    try:
        ident = _identity()
    except ValueError as exc:
        return err(str(exc), code="identity_invalid", status=401)

    existing = get_patient(patient_id)
    if not existing:
        return err("Paciente no encontrado", code="not_found", status=404)

    org_id = existing.get("org_id")
    try:
        _ensure_membership(ident["user_id"], org_id)
    except PermissionError as exc:
        return err(str(exc), code="forbidden", status=403)

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return err("JSON inválido", code="invalid_json", status=400)

    updates: Dict[str, Any] = {}

    if "person_name" in payload:
        name = (payload.get("person_name") or "").strip()
        if not name:
            return err("Nombre es requerido", code="name_required", status=400)
        updates["person_name"] = name

    clear_birthdate = False
    if "birthdate" in payload:
        birthdate_raw = payload.get("birthdate")
        if birthdate_raw in (None, ""):
            clear_birthdate = True
        else:
            birthdate, birthdate_error = _parse_birthdate(birthdate_raw)
            if birthdate_error:
                return err("Fecha de nacimiento inválida (YYYY-MM-DD)", code="birthdate_invalid", status=400)
            updates["birthdate"] = birthdate

    if "sex_id" in payload:
        updates["sex_id"] = payload.get("sex_id")
    if "risk_level_id" in payload:
        updates["risk_level_id"] = payload.get("risk_level_id")
    if "profile_photo_url" in payload:
        updates["profile_photo_url"] = payload.get("profile_photo_url")

    try:
        updated = update_patient(
            patient_id,
            person_name=updates.get("person_name"),
            birthdate=updates.get("birthdate"),
            clear_birthdate=clear_birthdate,
            sex_id=updates.get("sex_id"),
            risk_level_id=updates.get("risk_level_id"),
            profile_photo_url=updates.get("profile_photo_url"),
        )
    except Exception as exc:  # pragma: no cover - DB errors bubbled
        return err("No se pudo actualizar paciente", code="update_error", status=500, details={"error": str(exc)})

    if not updated:
        return err("Sin cambios", code="no_changes", status=400)

    patient = get_patient(patient_id)
    return ok({"patient": patient})


@bp.delete("/<patient_id>")
@jwt_required()
def delete_patient_route(patient_id: str):
    try:
        ident = _identity()
    except ValueError as exc:
        return err(str(exc), code="identity_invalid", status=401)

    patient = get_patient(patient_id)
    if not patient:
        return err("Paciente no encontrado", code="not_found", status=404)

    org_id = patient.get("org_id")
    try:
        _ensure_membership(ident["user_id"], org_id)
    except PermissionError as exc:
        return err(str(exc), code="forbidden", status=403)

    try:
        deleted = delete_patient(patient_id)
    except Exception as exc:  # pragma: no cover
        return err("No se pudo eliminar paciente", code="delete_error", status=500, details={"error": str(exc)})

    if not deleted:
        return err("Paciente no encontrado", code="not_found", status=404)

    return ok({"deleted": True, "patient_id": patient_id})
