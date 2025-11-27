"""Care team endpoints."""
from __future__ import annotations

from flask import Blueprint, request

from ..auth import require_org_admin
from ..repositories.care_teams import CareTeamsRepository
from ..request_utils import parse_payload
from ..xml import xml_error_response, xml_response

bp = Blueprint("care_teams", __name__, url_prefix="/admin/organizations/<org_id>/care-teams")
_repo = CareTeamsRepository()


# Specific routes must come before generic patterns
@bp.get("/member-roles")
@require_org_admin
def list_member_roles(org_id: str):
    roles = _repo.list_member_roles()
    return xml_response({"member_roles": roles})


# Root level operations
@bp.get("/")
@require_org_admin
def list_care_teams(org_id: str):
    teams = _repo.list_for_org(org_id)
    return xml_response({"care_teams": teams})


@bp.post("/")
@require_org_admin
def create_care_team(org_id: str):
    payload = parse_payload(request)
    name = (payload.get("name") or "").strip()
    if not name:
        return xml_error_response("invalid_input", "Name is required", status=400)
    team = _repo.create(org_id, name)
    if not team:
        return xml_error_response("create_failed", "Care team could not be created", status=500)
    return xml_response({"care_team": team}, status=201)


# Individual care team operations
@bp.route("/<care_team_id>", methods=["GET", "PATCH", "DELETE"])
@require_org_admin
def manage_care_team(org_id: str, care_team_id: str):
    if request.method == "GET":
        team = _repo.get(care_team_id, org_id)
        if not team:
            return xml_error_response("not_found", "Care team not found", status=404)
        members = _repo.list_members(care_team_id, org_id)
        patients = _repo.list_patients(care_team_id, org_id)
        return xml_response({
            "care_team": team,
            "members": members,
            "patients": patients,
        })
    elif request.method == "PATCH":
        payload = parse_payload(request)
        name = (payload.get("name") or None)
        team = _repo.update(care_team_id, org_id, name)
        if not team:
            return xml_error_response("not_found", "Care team not found", status=404)
        return xml_response({"care_team": team})
    else:  # DELETE
        team = _repo.get(care_team_id, org_id)
        if not team:
            return xml_error_response("not_found", "Care team not found", status=404)
        dependencies = _repo.dependency_counts(care_team_id, org_id)
        if dependencies and (dependencies["member_count"] > 0 or dependencies["patient_count"] > 0):
            return xml_error_response(
                "conflict",
                "Care team has assigned members or patients. Remove them before deleting the team.",
                status=409,
            )
        _repo.delete(care_team_id, org_id)
        return xml_response({"deleted": True})


# Care team members
@bp.route("/<care_team_id>/members", methods=["GET", "POST"])
@require_org_admin
def manage_care_team_members(org_id: str, care_team_id: str):
    if request.method == "GET":
        members = _repo.list_members(care_team_id, org_id)
        return xml_response({"members": members})
    else:  # POST
        payload = parse_payload(request)
        user_id = (payload.get("user_id") or "").strip()
        role_id = (payload.get("role_id") or "").strip()
        if not user_id or not role_id:
            return xml_error_response("invalid_input", "user_id and role_id are required", status=400)
        member = _repo.add_member(care_team_id, org_id, user_id, role_id)
        if not member:
            return xml_error_response("create_failed", "Member could not be added", status=400)
        return xml_response({"member": member}, status=201)


@bp.route("/<care_team_id>/members/<user_id>", methods=["PATCH", "DELETE"])
@require_org_admin
def manage_care_team_member(org_id: str, care_team_id: str, user_id: str):
    if request.method == "PATCH":
        payload = parse_payload(request)
        role_id = (payload.get("role_id") or "").strip()
        if not role_id:
            return xml_error_response("invalid_input", "role_id is required", status=400)
        member = _repo.update_member(care_team_id, org_id, user_id, role_id)
        if not member:
            return xml_error_response("not_found", "Member not found", status=404)
        return xml_response({"member": member})
    else:  # DELETE
        _repo.remove_member(care_team_id, org_id, user_id)
        return xml_response({"deleted": True})


# Care team patients
@bp.route("/<care_team_id>/patients", methods=["GET", "POST"])
@require_org_admin
def manage_care_team_patients(org_id: str, care_team_id: str):
    if request.method == "GET":
        patients = _repo.list_patients(care_team_id, org_id)
        return xml_response({"patients": patients})
    else:  # POST
        payload = parse_payload(request)
        patient_id = (payload.get("patient_id") or "").strip()
        if not patient_id:
            return xml_error_response("invalid_input", "patient_id is required", status=400)
        patient = _repo.add_patient(care_team_id, org_id, patient_id)
        if not patient:
            return xml_error_response("create_failed", "Patient could not be assigned", status=400)
        return xml_response({"patient": patient}, status=201)


@bp.route("/<care_team_id>/patients/<patient_id>", methods=["DELETE"])
@require_org_admin
def remove_patient_from_care_team(org_id: str, care_team_id: str, patient_id: str):
    _repo.remove_patient(care_team_id, org_id, patient_id)
    return xml_response({"deleted": True})
