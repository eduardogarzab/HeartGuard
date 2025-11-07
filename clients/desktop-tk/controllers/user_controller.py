"""Controller for staff (caregiver) workflows."""
from __future__ import annotations

from typing import Any

from ..api.gateway_client import GatewayApiClient


class UserController:
    def __init__(self, api_client: GatewayApiClient) -> None:
        self.api_client = api_client

    def get_profile(self) -> dict[str, Any]:
        return self.api_client.get_current_user_profile()

    def get_memberships(self) -> list[dict[str, Any]]:
        return self.api_client.get_current_user_memberships()

    def get_dashboard(self, org_id: str) -> dict[str, Any]:
        return self.api_client.get_organization_dashboard(org_id)

    def get_metrics(self, org_id: str) -> dict[str, Any]:
        return self.api_client.get_organization_metrics(org_id)

    def get_patients(self) -> dict[str, Any]:
        return self.api_client.get_caregiver_patients()

    def get_patient_detail(self, patient_id: str) -> dict[str, Any]:
        return self.api_client.get_caregiver_patient(patient_id)

    def get_patient_alerts(self, patient_id: str, limit: int = 10) -> dict[str, Any]:
        return self.api_client.get_caregiver_patient_alerts(patient_id, limit)

    def get_patient_notes(self, patient_id: str) -> dict[str, Any]:
        return self.api_client.get_caregiver_patient_notes(patient_id)

    def get_invitations(self) -> list[dict[str, Any]]:
        return self.api_client.get_pending_invitations()

    def accept_invitation(self, invitation_id: str) -> Any:
        return self.api_client.accept_invitation(invitation_id)

    def reject_invitation(self, invitation_id: str) -> Any:
        return self.api_client.reject_invitation(invitation_id)

    def get_care_team_locations(self) -> dict[str, Any]:
        return self.api_client.get_care_team_locations({})

    def get_patient_locations(self) -> dict[str, Any]:
        return self.api_client.get_caregiver_patients_locations({})

    def get_care_team_devices(self, org_id: str, team_id: str) -> dict[str, Any]:
        return self.api_client.get_care_team_devices(org_id, team_id)

    def get_disconnected_devices(self, org_id: str, team_id: str) -> dict[str, Any]:
        return self.api_client.get_care_team_disconnected_devices(org_id, team_id)

    def get_device_streams(self, org_id: str, team_id: str, device_id: str) -> dict[str, Any]:
        return self.api_client.get_care_team_device_streams(org_id, team_id, device_id)
