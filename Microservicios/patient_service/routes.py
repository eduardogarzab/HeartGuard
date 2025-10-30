"""Patient service managing clinical subject data."""
from __future__ import annotations

import datetime as dt
import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import (
    CareTeam,
    CareTeamMember,
    CaregiverPatient,
    CaregiverRelationshipType,
    Patient,
    RiskLevel,
    Sex,
)

bp = Blueprint("patients", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response(
        {
            "service": "patient",
            "status": "healthy",
            "patients": Patient.query.count(),
        }
    )


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_patients() -> "Response":
    patients = [
        _serialize_patient(patient)
        for patient in Patient.query.order_by(Patient.created_at.desc()).limit(200).all()
    ]
    return render_response({"patients": patients}, meta={"total": len(patients)})


@bp.route("", methods=["POST"])
@require_auth(required_roles=["clinician", "superadmin"])
def create_patient() -> "Response":
    payload, _ = parse_request_data(request)
    person_name = payload.get("person_name")
    if not person_name:
        first_name = payload.get("first_name")
        last_name = payload.get("last_name")
        if not first_name or not last_name:
            raise APIError(
                "person_name or first_name/last_name are required",
                status_code=400,
                error_id="HG-PATIENT-VALIDATION",
            )
        person_name = f"{first_name} {last_name}".strip()

    org_id = payload.get("org_id")
    if not org_id:
        raise APIError("org_id is required", status_code=400, error_id="HG-PATIENT-ORG")

    birthdate = payload.get("birthdate")
    birthdate_obj = None
    if birthdate:
        try:
            birthdate_obj = dt.date.fromisoformat(birthdate)
        except ValueError as exc:
            raise APIError("birthdate must be ISO formatted (YYYY-MM-DD)", status_code=400, error_id="HG-PATIENT-DATE") from exc

    sex_code = payload.get("sex_code") or payload.get("sex")
    sex = Sex.query.filter_by(code=sex_code).first() if sex_code else None
    if sex_code and not sex:
        raise APIError("sex_code is invalid", status_code=400, error_id="HG-PATIENT-SEX")

    risk_code = payload.get("risk_level_code")
    risk_level = RiskLevel.query.filter_by(code=risk_code).first() if risk_code else None
    if risk_code and not risk_level:
        raise APIError("risk_level_code is invalid", status_code=400, error_id="HG-PATIENT-RISK")

    patient = Patient(
        id=str(uuid.uuid4()),
        org_id=org_id,
        person_name=person_name,
        birthdate=birthdate_obj,
        sex_id=sex.id if sex else None,
        risk_level_id=risk_level.id if risk_level else None,
        profile_photo_url=payload.get("profile_photo_url"),
        created_at=dt.datetime.utcnow(),
    )
    db.session.add(patient)
    db.session.commit()
    return render_response({"patient": _serialize_patient(patient)}, status_code=201)


@bp.route("/<patient_id>", methods=["GET"])
@require_auth(optional=True)
def get_patient(patient_id: str) -> "Response":
    patient = _get_patient(patient_id)
    return render_response({"patient": _serialize_patient(patient)})


@bp.route("/<patient_id>/care-team", methods=["GET"])
@require_auth(optional=True)
def get_care_team(patient_id: str) -> "Response":
    patient = _get_patient(patient_id)
    care_teams = [_serialize_team(team) for team in patient.care_teams]
    caregivers = [_serialize_caregiver(link) for link in patient.caregivers]
    return render_response({"care_teams": care_teams, "caregivers": caregivers})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/patients")


def _get_patient(patient_id: str) -> Patient:
    patient = Patient.query.get(patient_id)
    if not patient:
        raise APIError("Patient not found", status_code=404, error_id="HG-PATIENT-NOT-FOUND")
    return patient


def _serialize_patient(patient: Patient) -> dict:
    sex = patient.sex.code if patient.sex else None
    risk = patient.risk_level.code if patient.risk_level else None
    return {
        "id": patient.id,
        "person_name": patient.person_name,
        "org_id": patient.org_id,
        "birthdate": patient.birthdate.isoformat() if patient.birthdate else None,
        "sex_code": sex,
        "risk_level_code": risk,
        "profile_photo_url": patient.profile_photo_url,
        "created_at": (patient.created_at or dt.datetime.utcnow()).isoformat() + "Z",
    }


def _serialize_team(team: CareTeam) -> dict:
    members = [
        {
            "user_id": member.user_id,
            "role_id": member.role_id,
            "joined_at": member.joined_at.isoformat() + "Z",
        }
        for member in team.members
    ]
    return {
        "id": team.id,
        "name": team.name,
        "members": members,
    }


def _serialize_caregiver(link: CaregiverPatient) -> dict:
    rel = CaregiverRelationshipType.query.get(link.rel_type_id) if link.rel_type_id else None
    return {
        "patient_id": link.patient_id,
        "caregiver_id": link.user_id,
        "relationship": rel.code if rel else None,
        "is_primary": link.is_primary,
        "started_at": link.started_at.isoformat() + "Z",
        "ended_at": link.ended_at.isoformat() + "Z" if link.ended_at else None,
        "note": link.note,
    }
