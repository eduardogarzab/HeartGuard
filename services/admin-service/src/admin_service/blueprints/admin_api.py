"""Admin API blueprint."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from flask import Blueprint, jsonify, request

from ..middleware.auth import org_admin_required
from ..schemas.invitation_schemas import InvitationRequest
from ..schemas.patient_schemas import PatientCreateRequest, PatientUpdateRequest
from ..schemas.user_schemas import (
    AssignRoleRequest,
    CareTeamAssignmentRequest,
    UserInvitationResponse,
    UserResponse,
)
from ..services.invitation_service import InvitationService

admin_api_bp = Blueprint("admin_api", __name__)
invitation_service = InvitationService()


@admin_api_bp.route("/organizations/<uuid:org_id>/invite", methods=["POST"])
@org_admin_required(roles=["org_admin"])
def invite_user(org_id: UUID):
    """Invite a new user to the organization."""
    payload = request.get_json(silent=True) or {}
    data = InvitationRequest(**payload)
    invitation = invitation_service.create_invitation(org_id=org_id, request=data)
    response = UserInvitationResponse(invitation_token=invitation["token"])
    return jsonify(response.dict()), HTTPStatus.CREATED


@admin_api_bp.route("/organizations/<uuid:org_id>/users", methods=["GET"])
@org_admin_required()
def list_users(org_id: UUID):
    """Return users for the organization."""
    users = invitation_service.list_org_users(org_id=org_id)
    response = [UserResponse(**user).dict() for user in users]
    return jsonify(response), HTTPStatus.OK


@admin_api_bp.route("/organizations/<uuid:org_id>/users/<uuid:user_id>/role", methods=["PUT"])
@org_admin_required(roles=["org_admin"])
def update_user_role(org_id: UUID, user_id: UUID):
    """Update a user's role in the organization."""
    payload = request.get_json(silent=True) or {}
    data = AssignRoleRequest(**payload)
    invitation_service.update_user_role(org_id=org_id, user_id=user_id, request=data)
    return jsonify({"status": "updated"}), HTTPStatus.OK


@admin_api_bp.route("/organizations/<uuid:org_id>/users/<uuid:user_id>", methods=["DELETE"])
@org_admin_required(roles=["org_admin"])
def remove_user(org_id: UUID, user_id: UUID):
    """Remove a user from the organization."""
    invitation_service.remove_user(org_id=org_id, user_id=user_id)
    return "", HTTPStatus.NO_CONTENT


@admin_api_bp.route("/organizations/<uuid:org_id>/patients", methods=["GET"])
@org_admin_required()
def list_patients(org_id: UUID):
    """Return patients for the organization."""
    patients = invitation_service.list_patients(org_id=org_id)
    return jsonify(patients), HTTPStatus.OK


@admin_api_bp.route("/organizations/<uuid:org_id>/patients", methods=["POST"])
@org_admin_required()
def create_patient(org_id: UUID):
    """Create a patient within the organization."""
    payload = request.get_json(silent=True) or {}
    data = PatientCreateRequest(**payload)
    patient = invitation_service.create_patient(org_id=org_id, request=data)
    return jsonify(patient), HTTPStatus.CREATED


@admin_api_bp.route("/patients/<uuid:patient_id>", methods=["GET"])
@org_admin_required()
def get_patient(patient_id: UUID):
    """Retrieve a patient ensuring org membership."""
    patient = invitation_service.get_patient(patient_id=patient_id)
    return jsonify(patient), HTTPStatus.OK


@admin_api_bp.route("/patients/<uuid:patient_id>", methods=["PUT"])
@org_admin_required()
def update_patient(patient_id: UUID):
    """Update patient information."""
    payload = request.get_json(silent=True) or {}
    data = PatientUpdateRequest(**payload)
    patient = invitation_service.update_patient(patient_id=patient_id, request=data)
    return jsonify(patient), HTTPStatus.OK


@admin_api_bp.route("/organizations/<uuid:org_id>/care-teams", methods=["POST"])
@org_admin_required(roles=["org_admin", "care_manager"])
def create_care_team(org_id: UUID):
    """Create a new care team."""
    payload = request.get_json(silent=True) or {}
    care_team = invitation_service.create_care_team(org_id=org_id, payload=payload)
    return jsonify(care_team), HTTPStatus.CREATED


@admin_api_bp.route("/care-teams/<uuid:team_id>/assign-patient", methods=["POST"])
@org_admin_required()
def assign_patient_to_team(team_id: UUID):
    """Assign a patient to a care team."""
    payload = request.get_json(silent=True) or {}
    data = CareTeamAssignmentRequest(**payload)
    result = invitation_service.assign_patient_to_team(team_id=team_id, request=data)
    return jsonify(result), HTTPStatus.OK


@admin_api_bp.route("/care-teams/<uuid:team_id>/assign-user", methods=["POST"])
@org_admin_required()
def assign_user_to_team(team_id: UUID):
    """Assign a user to a care team."""
    payload = request.get_json(silent=True) or {}
    data = CareTeamAssignmentRequest(**payload)
    result = invitation_service.assign_user_to_team(team_id=team_id, request=data)
    return jsonify(result), HTTPStatus.OK


@admin_api_bp.route("/organizations/<uuid:org_id>/stats", methods=["GET"])
@org_admin_required()
def get_org_stats(org_id: UUID):
    """Return organization statistics."""
    stats = invitation_service.get_org_stats(org_id=org_id)
    return jsonify(stats), HTTPStatus.OK


@admin_api_bp.route("/organizations/<uuid:org_id>/alerts", methods=["GET"])
@org_admin_required()
def get_org_alerts(org_id: UUID):
    """Return organization alerts."""
    alerts = invitation_service.get_org_alerts(org_id=org_id)
    return jsonify(alerts), HTTPStatus.OK


__all__ = ["admin_api_bp"]
