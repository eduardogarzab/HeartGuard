"""Proxy para rutas hacia User Service."""
from __future__ import annotations

from http import HTTPStatus
from typing import Iterable

from flask import Blueprint, Response, current_app, jsonify, request

from ..services.user_client import UserClient, UserClientError

bp = Blueprint("user", __name__)


def _get_user_client() -> UserClient:
	return UserClient(
		base_url=current_app.config["USER_SERVICE_URL"],
		timeout=current_app.config["GATEWAY_SERVICE_TIMEOUT"],
	)


def _forward_headers() -> dict[str, str]:
	forwarded = {}
	for header in ("Authorization", "Content-Type", "Accept", "X-Trace-ID", "X-Trace-Id"):
		value = request.headers.get(header)
		if value:
			forwarded[header] = value
	return forwarded


def _filter_response_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
	excluded = {"content-length", "transfer-encoding", "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "upgrade"}
	return {key: value for key, value in headers if key.lower() not in excluded}


def _proxy_user(path: str, method: str | None = None) -> Response:
	method = method or request.method
	headers = _forward_headers()

	json_payload = None
	raw_payload = None
	if method in {"POST", "PATCH", "PUT"}:
		if request.is_json:
			json_payload = request.get_json(silent=True)
		elif request.data:
			raw_payload = request.get_data()

	params = list(request.args.items(multi=True)) if request.args else None

	try:
		client = _get_user_client()
		resp = client.proxy_request(
			method=method,
			path=path,
			headers=headers if headers else None,
			json=json_payload,
			data=raw_payload,
			params=params,
		)
		filtered_headers = _filter_response_headers(resp.headers.items())
		return Response(resp.content, status=resp.status_code, headers=filtered_headers)
	except UserClientError as exc:
		return jsonify({"error": exc.error, "message": exc.message}), exc.status_code
	except Exception as exc:  # pragma: no cover - defensivo
		current_app.logger.error("Error en proxy user: %s", exc, exc_info=True)
		return jsonify({"error": "internal_error", "message": "Error interno del gateway"}), HTTPStatus.INTERNAL_SERVER_ERROR


@bp.route("/", methods=["GET"])
def service_info() -> Response:
	return _proxy_user("/")


@bp.route("/users/me", methods=["GET", "PATCH"])
def users_me() -> Response:
	return _proxy_user("/users/me")


@bp.route("/users/me/org-memberships", methods=["GET"])
def users_memberships() -> Response:
	return _proxy_user("/users/me/org-memberships")


@bp.route("/users/me/invitations", methods=["GET"])
def users_invitations() -> Response:
	return _proxy_user("/users/me/invitations")


@bp.route("/users/me/invitations/<string:invitation_id>/accept", methods=["POST"])
def users_invitation_accept(invitation_id: str) -> Response:
	return _proxy_user(f"/users/me/invitations/{invitation_id}/accept")


@bp.route("/users/me/invitations/<string:invitation_id>/reject", methods=["POST"])
def users_invitation_reject(invitation_id: str) -> Response:
	return _proxy_user(f"/users/me/invitations/{invitation_id}/reject")


@bp.route("/users/me/push-devices", methods=["GET", "POST"])
def users_push_devices() -> Response:
	return _proxy_user("/users/me/push-devices")


@bp.route("/users/me/push-devices/<string:device_id>", methods=["PATCH", "DELETE"])
def users_push_device_detail(device_id: str) -> Response:
	return _proxy_user(f"/users/me/push-devices/{device_id}")


@bp.route("/orgs/<string:org_id>/members/<string:user_id>", methods=["GET"])
def org_membership_detail(org_id: str, user_id: str) -> Response:
	return _proxy_user(f"/orgs/{org_id}/members/{user_id}")


@bp.route("/orgs/<string:org_id>/dashboard", methods=["GET"])
def org_dashboard(org_id: str) -> Response:
	return _proxy_user(f"/orgs/{org_id}/dashboard")


@bp.route("/orgs/<string:org_id>/care-teams", methods=["GET"])
def org_care_teams(org_id: str) -> Response:
	return _proxy_user(f"/orgs/{org_id}/care-teams")


@bp.route("/orgs/<string:org_id>/care-team-patients", methods=["GET"])
def org_care_team_patients(org_id: str) -> Response:
	return _proxy_user(f"/orgs/{org_id}/care-team-patients")


@bp.route("/orgs/<string:org_id>/care-team-patients/locations", methods=["GET"])
def org_care_team_patients_locations(org_id: str) -> Response:
	return _proxy_user(f"/orgs/{org_id}/care-team-patients/locations")


@bp.route("/orgs/<string:org_id>/care-teams/<string:team_id>/devices", methods=["GET"])
def org_care_team_devices(org_id: str, team_id: str) -> Response:
	return _proxy_user(f"/orgs/{org_id}/care-teams/{team_id}/devices")


@bp.route("/orgs/<string:org_id>/care-teams/<string:team_id>/devices/disconnected", methods=["GET"])
def org_care_team_disconnected_devices(org_id: str, team_id: str) -> Response:
	return _proxy_user(f"/orgs/{org_id}/care-teams/{team_id}/devices/disconnected")


@bp.route("/orgs/<string:org_id>/care-teams/<string:team_id>/devices/<string:device_id>", methods=["GET"])
def org_care_team_device_detail(org_id: str, team_id: str, device_id: str) -> Response:
	return _proxy_user(f"/orgs/{org_id}/care-teams/{team_id}/devices/{device_id}")


@bp.route("/orgs/<string:org_id>/care-teams/<string:team_id>/devices/<string:device_id>/streams", methods=["GET"])
def org_care_team_device_streams(org_id: str, team_id: str, device_id: str) -> Response:
	return _proxy_user(f"/orgs/{org_id}/care-teams/{team_id}/devices/{device_id}/streams")


@bp.route("/orgs/<string:org_id>/patients/<string:patient_id>", methods=["GET"])
def org_patient_detail(org_id: str, patient_id: str) -> Response:
	return _proxy_user(f"/orgs/{org_id}/patients/{patient_id}")


@bp.route("/orgs/<string:org_id>/patients/<string:patient_id>/alerts", methods=["GET"])
def org_patient_alerts(org_id: str, patient_id: str) -> Response:
	return _proxy_user(f"/orgs/{org_id}/patients/{patient_id}/alerts")


@bp.route("/orgs/<string:org_id>/patients/<string:patient_id>/notes", methods=["GET"])
def org_patient_notes(org_id: str, patient_id: str) -> Response:
	return _proxy_user(f"/orgs/{org_id}/patients/{patient_id}/notes")


@bp.route("/orgs/<string:org_id>/metrics", methods=["GET"])
def org_metrics(org_id: str) -> Response:
	return _proxy_user(f"/orgs/{org_id}/metrics")


@bp.route("/care-team/locations", methods=["GET"])
def care_team_locations() -> Response:
	return _proxy_user("/care-team/locations")


@bp.route("/caregiver/patients", methods=["GET"])
def caregiver_patients() -> Response:
	return _proxy_user("/caregiver/patients")


@bp.route("/caregiver/patients/locations", methods=["GET"])
def caregiver_patient_locations() -> Response:
	return _proxy_user("/caregiver/patients/locations")


@bp.route("/caregiver/patients/<string:patient_id>", methods=["GET"])
def caregiver_patient_detail(patient_id: str) -> Response:
	return _proxy_user(f"/caregiver/patients/{patient_id}")


@bp.route("/caregiver/patients/<string:patient_id>/alerts", methods=["GET"])
def caregiver_patient_alerts(patient_id: str) -> Response:
	return _proxy_user(f"/caregiver/patients/{patient_id}/alerts")


@bp.route("/caregiver/patients/<string:patient_id>/notes", methods=["GET", "POST"])
def caregiver_patient_notes(patient_id: str) -> Response:
	return _proxy_user(f"/caregiver/patients/{patient_id}/notes")


@bp.route("/caregiver/metrics", methods=["GET"])
def caregiver_metrics() -> Response:
	return _proxy_user("/caregiver/metrics")


@bp.route("/event-types", methods=["GET"])
def event_types() -> Response:
	return _proxy_user("/event-types")
