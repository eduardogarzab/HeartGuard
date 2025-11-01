"""models.Patient service managing clinical subject data."""
from __future__ import annotations

import os
import uuid
from typing import Any

import requests
from flask import Blueprint, current_app, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response
import models
# Models accessed via models. models.Patient

bp = Blueprint("patients", __name__)


def _patient_item_name(item: Any) -> str:
    """Return the XML tag name for list items in patient responses."""

    if isinstance(item, dict):
        keys = set(item.keys())
        if {"severity", "status", "created_at"}.issubset(keys):
            return "Alert"
    return "Patient"


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "patient", "status": "healthy"})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_patients() -> "Response":
    org_id_param = request.args.get("org_id")
    if not org_id_param:
        raise APIError("org_id is required", status_code=400, error_id="HG-PATIENT-ORG-ID-REQUIRED")

    try:
        org_uuid = uuid.UUID(org_id_param)
    except (ValueError, TypeError) as exc:
        raise APIError("org_id must be a valid UUID", status_code=400, error_id="HG-PATIENT-ORG-ID-INVALID") from exc

    patients = models.PatientQuery.list_with_details(org_uuid)
    return render_response({"patients": patients}, meta={"total": len(patients)}, xml_item_name=_patient_item_name)


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


def _organization_service_base_url() -> str:
    base_url = current_app.config.get("ORGANIZATION_SERVICE_URL")
    if base_url:
        return base_url.rstrip("/")
    env_url = os.getenv("ORGANIZATION_SERVICE_URL", "http://organization-service:5002/organization")
    current_app.config["ORGANIZATION_SERVICE_URL"] = env_url
    return env_url.rstrip("/")


def _call_organization_service(method: str, path: str, **kwargs) -> requests.Response:
    url = f"{_organization_service_base_url()}{path}"
    timeout = current_app.config.get("ORGANIZATION_HTTP_TIMEOUT", 5)
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
    except requests.RequestException as exc:  # pragma: no cover - network failure
        raise APIError(
            "Failed to contact organization service",
            status_code=502,
            error_id="HG-PATIENT-ORG-SERVICE",
        ) from exc

    if response.status_code >= 400:
        message = "Organization service error"
        try:
            payload = response.json()
            message = (
                payload.get("error", {}).get("message")
                or payload.get("message")
                or message
            )
        except ValueError:
            if response.text:
                message = response.text
        raise APIError(message, status_code=response.status_code, error_id="HG-PATIENT-ORG-SERVICE")

    return response


def _fetch_invitation_details(signed_token: str) -> dict:
    response = _call_organization_service(
        "GET",
        f"/invitations/{signed_token}/validate",
        headers={"Accept": "application/json"},
    )
    return response.json().get("data") or {}


def _consume_invitation_token(signed_token: str, payload: dict) -> None:
    _call_organization_service(
        "POST",
        f"/invitations/{signed_token}/consume",
        headers={"Accept": "application/json"},
        json=payload,
    )


@bp.route("/register", methods=["POST"])
def register_from_invitation() -> "Response":
    payload, _ = parse_request_data(request)

    signed_token = payload.get("invite_token") or payload.get("token")
    person_name = (payload.get("person_name") or payload.get("name") or "").strip()

    if not signed_token:
        raise APIError("invite_token is required", status_code=400, error_id="HG-PATIENT-INVITE-TOKEN")
    if not person_name:
        raise APIError("person_name is required", status_code=400, error_id="HG-PATIENT-VALIDATION")

    invitation = _fetch_invitation_details(str(signed_token))
    invitation_data = invitation.get("invitation") or {}

    try:
        org_uuid = uuid.UUID(str(invitation_data.get("org_id")))
    except (TypeError, ValueError) as exc:
        raise APIError("Invitation organization invalid", status_code=400, error_id="HG-PATIENT-INVITE-ORG") from exc

    new_patient = models.Patient(person_name=person_name, org_id=org_uuid)
    db.session.add(new_patient)
    db.session.flush()

    try:
        _consume_invitation_token(
            signed_token,
            {
                "action": "accept",
                "consumer_type": "patient",
                "consumer_id": str(new_patient.id),
            },
        )
    except APIError:
        db.session.rollback()
        raise

    db.session.commit()

    response_payload = {
        "patient": new_patient.to_dict(),
        "metadata": invitation.get("metadata"),
    }
    return render_response(response_payload, status_code=201, xml_item_name=_patient_item_name)


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
