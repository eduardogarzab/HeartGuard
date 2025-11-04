"""Care team endpoints."""
from __future__ import annotations

from flask import Blueprint, request

from ..auth import require_org_admin
from ..repositories.care_teams import CareTeamsRepository
from ..request_utils import parse_payload
from ..xml import xml_error_response, xml_response

bp = Blueprint("care_teams", __name__, url_prefix="/admin/organizations/<org_id>/care-teams")
_repo = CareTeamsRepository()


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


@bp.patch("/<care_team_id>")
@require_org_admin
def update_care_team(org_id: str, care_team_id: str):
    payload = parse_payload(request)
    name = (payload.get("name") or None)
    team = _repo.update(care_team_id, org_id, name)
    if not team:
        return xml_error_response("not_found", "Care team not found", status=404)
    return xml_response({"care_team": team})


@bp.delete("/<care_team_id>")
@require_org_admin
def delete_care_team(org_id: str, care_team_id: str):
    _repo.delete(care_team_id, org_id)
    return xml_response({"deleted": True})


@bp.get("/<care_team_id>/members")
@require_org_admin
def list_members(org_id: str, care_team_id: str):
    members = _repo.list_members(care_team_id, org_id)
    return xml_response({"members": members})


@bp.post("/<care_team_id>/members")
@require_org_admin
def add_member(org_id: str, care_team_id: str):
    payload = parse_payload(request)
    user_id = (payload.get("user_id") or "").strip()
    role_id = (payload.get("role_id") or "").strip()
    if not user_id or not role_id:
        return xml_error_response("invalid_input", "user_id and role_id are required", status=400)
    member = _repo.add_member(care_team_id, org_id, user_id, role_id)
    if not member:
        return xml_error_response("create_failed", "Member could not be added", status=400)
    return xml_response({"member": member}, status=201)


@bp.patch("/<care_team_id>/members/<user_id>")
@require_org_admin
def update_member(org_id: str, care_team_id: str, user_id: str):
    payload = parse_payload(request)
    role_id = (payload.get("role_id") or "").strip()
    if not role_id:
        return xml_error_response("invalid_input", "role_id is required", status=400)
    member = _repo.update_member(care_team_id, org_id, user_id, role_id)
    if not member:
        return xml_error_response("not_found", "Member not found", status=404)
    return xml_response({"member": member})


@bp.delete("/<care_team_id>/members/<user_id>")
@require_org_admin
def remove_member(org_id: str, care_team_id: str, user_id: str):
    _repo.remove_member(care_team_id, org_id, user_id)
    return xml_response({"deleted": True})


@bp.get("/<care_team_id>/patients")
@require_org_admin
def list_care_team_patients(org_id: str, care_team_id: str):
    patients = _repo.list_patients(care_team_id, org_id)
    return xml_response({"patients": patients})


@bp.post("/<care_team_id>/patients")
@require_org_admin
def add_care_team_patient(org_id: str, care_team_id: str):
    payload = parse_payload(request)
    patient_id = (payload.get("patient_id") or "").strip()
    if not patient_id:
        return xml_error_response("invalid_input", "patient_id is required", status=400)
    patient = _repo.add_patient(care_team_id, org_id, patient_id)
    if not patient:
        return xml_error_response("create_failed", "Patient could not be assigned", status=400)
    return xml_response({"patient": patient}, status=201)


@bp.delete("/<care_team_id>/patients/<patient_id>")
@require_org_admin
def remove_care_team_patient(org_id: str, care_team_id: str, patient_id: str):
    _repo.remove_patient(care_team_id, org_id, patient_id)
    return xml_response({"deleted": True})
