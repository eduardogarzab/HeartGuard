"""models.Patient service managing clinical subject data."""
from __future__ import annotations

import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response
import models
# Models accessed via models. models.Patient

bp = Blueprint("patients", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "patient", "status": "healthy"})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_patients() -> "Response":
    patients = [p.to_dict() for p in models.Patient.query.all()]
    return render_response({"patients": patients}, meta={"total": len(patients)})


@bp.route("", methods=["POST"])
@require_auth(required_roles=["clinician", "admin"])
def create_patient() -> "Response":
    payload, _ = parse_request_data(request)
    person_name = payload.get("person_name")
    if not person_name:
        raise APIError("person_name is required", status_code=400, error_id="HG-PATIENT-VALIDATION")

    new_patient = models.Patient(person_name=person_name, org_id=payload.get("org_id"))

    db.session.add(new_patient)
    db.session.commit()

    return render_response({"patient": new_patient.to_dict()}, status_code=201)


@bp.route("/<patient_id>", methods=["GET"])
@require_auth(optional=True)
def get_patient(patient_id: str) -> "Response":
    patient = models.Patient.query.get(patient_id)
    if not patient:
        raise APIError("models.Patient not found", status_code=404, error_id="HG-PATIENT-NOT-FOUND")
    return render_response({"patient": patient.to_dict()})


@bp.route("/<patient_id>/care-team", methods=["GET"])
@require_auth(optional=True)
def get_care_team(patient_id: str) -> "Response":
    # This route is not yet migrated to the database.
    team = []
    caregivers = []
    return render_response({"care_teams": team, "caregivers": caregivers})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/patients")
