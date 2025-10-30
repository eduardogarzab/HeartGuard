"""Patient service managing clinical subject data."""
from __future__ import annotations

import datetime as dt
from typing import Dict, List

from flask import Blueprint, request

from common.auth import require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("patients", __name__)

PATIENTS: Dict[str, Dict] = {
    "pat-1": {
        "id": "pat-1",
        "mrn": "MRN-1001",
        "first_name": "Elena",
        "last_name": "Heart",
        "birth_date": "1985-05-20",
        "sex": "F",
        "organization_id": "org-1",
    }
}

CARE_TEAMS: Dict[str, List[Dict]] = {
    "pat-1": [
        {
            "id": "team-1",
            "name": "Primary Care",
            "members": [
                {"user_id": "usr-2", "role": "clinician"},
                {"user_id": "usr-1", "role": "admin"},
            ],
        }
    ]
}

CAREGIVER_LINKS: List[Dict] = [
    {"caregiver_id": "usr-1", "patient_id": "pat-1", "relationship": "spouse"}
]


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "patient", "status": "healthy", "patients": len(PATIENTS)})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_patients() -> "Response":
    return render_response({"patients": list(PATIENTS.values())}, meta={"total": len(PATIENTS)})


@bp.route("", methods=["POST"])
@require_auth(required_roles=["clinician", "admin"])
def create_patient() -> "Response":
    payload, _ = parse_request_data(request)
    first_name = payload.get("first_name")
    last_name = payload.get("last_name")
    if not first_name or not last_name:
        raise APIError("first_name and last_name are required", status_code=400, error_id="HG-PATIENT-VALIDATION")
    patient_id = f"pat-{len(PATIENTS) + 1}"
    patient = {
        "id": patient_id,
        "mrn": payload.get("mrn", f"MRN-{len(PATIENTS) + 1000}"),
        "first_name": first_name,
        "last_name": last_name,
        "birth_date": payload.get("birth_date"),
        "sex": payload.get("sex", "U"),
        "organization_id": payload.get("organization_id", "org-1"),
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    PATIENTS[patient_id] = patient
    return render_response({"patient": patient}, status_code=201)


@bp.route("/<patient_id>", methods=["GET"])
@require_auth(optional=True)
def get_patient(patient_id: str) -> "Response":
    patient = PATIENTS.get(patient_id)
    if not patient:
        raise APIError("Patient not found", status_code=404, error_id="HG-PATIENT-NOT-FOUND")
    return render_response({"patient": patient})


@bp.route("/<patient_id>/care-team", methods=["GET"])
@require_auth(optional=True)
def get_care_team(patient_id: str) -> "Response":
    team = CARE_TEAMS.get(patient_id, [])
    caregivers = [link for link in CAREGIVER_LINKS if link["patient_id"] == patient_id]
    return render_response({"care_teams": team, "caregivers": caregivers})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/patients")
