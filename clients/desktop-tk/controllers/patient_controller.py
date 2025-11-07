"""Controller for patient flows."""
from __future__ import annotations

from typing import Any

from ..api.gateway_client import GatewayApiClient


class PatientController:
    def __init__(self, api_client: GatewayApiClient) -> None:
        self.api_client = api_client

    def get_dashboard(self) -> dict[str, Any]:
        return self.api_client.get_patient_dashboard()

    def get_profile(self) -> dict[str, Any]:
        return self.api_client.get_patient_profile()

    def get_alerts(self, limit: int = 20, offset: int = 0, status: str | None = None) -> dict[str, Any]:
        return self.api_client.get_patient_alerts(limit=limit, offset=offset, status=status)

    def get_devices(self) -> dict[str, Any]:
        return self.api_client.get_patient_devices()

    def get_caregivers(self) -> dict[str, Any]:
        return self.api_client.get_patient_caregivers()

    def get_readings(self, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        return self.api_client.get_patient_readings(limit=limit, offset=offset)

    def get_care_team(self) -> dict[str, Any]:
        return self.api_client.get_patient_care_team()

    def get_locations(self, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        return self.api_client.get_patient_locations(limit=limit, offset=offset)

    def get_latest_location(self) -> dict[str, Any]:
        return self.api_client.get_patient_latest_location()
