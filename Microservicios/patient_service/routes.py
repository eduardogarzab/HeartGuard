"""Patient service managing clinical subject data."""
from __future__ import annotations

import datetime as dt
import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import CareTeam, CareTeamMember, CaregiverLink, Patient

bp = Blueprint("patients", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "patient", "status": "healthy", "patients": Patient.query.count()})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_patients() -> "Response":
    patients = [
        _serialize_patient(patient)
        for patient in Patient.query.order_by(Patient.created_at.desc()).all()
    ]
    return render_response({"patients": patients}, meta={"total": len(patients)})


@bp.route("", methods=["POST"])
@require_auth(required_roles=["clinician", "admin"])
def create_patient() -> "Response":
    payload, _ = parse_request_data(request)
    first_name = payload.get("first_name")
    last_name = payload.get("last_name")
    if not first_name or not last_name:
        raise APIError("first_name and last_name are required", status_code=400, error_id="HG-PATIENT-VALIDATION")
    patient = Patient(
        id=f"pat-{uuid.uuid4()}",
        mrn=payload.get("mrn", f"MRN-{int(dt.datetime.utcnow().timestamp())}"),
        first_name=first_name,
        last_name=last_name,
        birth_date=payload.get("birth_date"),
        sex=payload.get("sex", "U"),
        organization_id=payload.get("organization_id", "org-1"),
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
    caregivers = [_serialize_caregiver(link) for link in patient.caregiver_links]
    return render_response({"care_teams": care_teams, "caregivers": caregivers})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/patients")
    with app.app_context():
        _seed_defaults()


def _get_patient(patient_id: str) -> Patient:
    patient = Patient.query.get(patient_id)
    if not patient:
        raise APIError("Patient not found", status_code=404, error_id="HG-PATIENT-NOT-FOUND")
    return patient


def _serialize_patient(patient: Patient) -> dict:
    return {
        "id": patient.id,
        "mrn": patient.mrn,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "birth_date": patient.birth_date,
        "sex": patient.sex,
        "organization_id": patient.organization_id,
        "created_at": (patient.created_at or dt.datetime.utcnow()).isoformat() + "Z",
        "updated_at": (patient.updated_at or dt.datetime.utcnow()).isoformat() + "Z",
    }


def _serialize_team(team: CareTeam) -> dict:
    return {
        "id": team.id,
        "name": team.name,
        "members": [
            {"user_id": member.user_id, "role": member.role}
            for member in team.members
        ],
    }


def _serialize_caregiver(link: CaregiverLink) -> dict:
    return {
        "id": link.id,
        "caregiver_id": link.caregiver_id,
        "patient_id": link.patient_id,
        "relationship": link.relationship,
    }


def _seed_defaults() -> None:
    if Patient.query.count() > 0:
        return
    patient = Patient(
        id="pat-1",
        mrn="MRN-1001",
        first_name="Elena",
        last_name="Heart",
        birth_date="1985-05-20",
        sex="F",
        organization_id="org-1",
    )
    db.session.add(patient)
    team = CareTeam(id="team-1", patient=patient, name="Primary Care")
    db.session.add(team)
    db.session.add(CareTeamMember(id=f"tm-{uuid.uuid4()}", team=team, user_id="usr-2", role="clinician"))
    db.session.add(CareTeamMember(id=f"tm-{uuid.uuid4()}", team=team, user_id="usr-1", role="admin"))
    db.session.add(CaregiverLink(id=f"cg-{uuid.uuid4()}", caregiver_id="usr-1", patient=patient, relationship="spouse"))
    db.session.commit()
