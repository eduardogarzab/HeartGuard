"""Gateway API client for the HeartGuard Tkinter desktop application."""
from __future__ import annotations

import logging
from typing import Any, Callable, Mapping

import requests

from ..utils.config import APP_CONFIG

LOGGER = logging.getLogger(__name__)


class ApiError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None,
                 payload: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


class GatewayApiClient:
    """Wrapper around ``requests`` that handles JWT authentication."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or APP_CONFIG.gateway_url).rstrip("/")
        self.session = requests.Session()
        self.access_token: str | None = None
        self.refresh_token: str | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            raise ValueError("Path must start with '/'")
        return f"{self.base_url}{path}"

    def _prepare_headers(self, headers: Mapping[str, str] | None, require_auth: bool) -> dict[str, str]:
        merged = {"Content-Type": "application/json", "Accept": "application/json"}
        if headers:
            merged.update(headers)
        if require_auth and self.access_token:
            merged.setdefault("Authorization", f"Bearer {self.access_token}")
        return merged

    def _request(self, method: str, path: str, *, require_auth: bool = True,
                 retry: bool = True, **kwargs: Any) -> Any:
        url = self._url(path)
        headers = self._prepare_headers(kwargs.pop("headers", None), require_auth)
        LOGGER.debug("%s %s", method, url)
        response = self.session.request(method, url, headers=headers, timeout=20, **kwargs)
        if response.status_code == 401 and retry and self.refresh_token:
            LOGGER.info("Access token expired, attempting refresh")
            if self.refresh_tokens():
                headers = self._prepare_headers(kwargs.pop("headers", None), require_auth)
                response = self.session.request(method, url, headers=headers, timeout=20, **kwargs)
        if response.status_code >= 400:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
            raise ApiError(str(payload), status_code=response.status_code, payload=payload)
        if response.status_code == 204:
            return None
        if response.headers.get("Content-Type", "").startswith("application/json"):
            return response.json()
        return response.text

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------
    def set_tokens(self, access_token: str | None, refresh_token: str | None) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token

    def clear_tokens(self) -> None:
        self.access_token = None
        self.refresh_token = None

    def refresh_tokens(self) -> bool:
        if not self.refresh_token:
            return False
        try:
            payload = {"refresh_token": self.refresh_token}
            response = self.session.post(
                self._url("/auth/refresh"), json=payload, timeout=20
            )
            if response.status_code >= 400:
                LOGGER.warning("Token refresh failed: %s", response.text)
                self.clear_tokens()
                return False
            data = response.json()
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token", self.refresh_token)
            LOGGER.info("Token refresh succeeded")
            return True
        except requests.RequestException as exc:
            LOGGER.error("Error refreshing token: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Authentication endpoints
    # ------------------------------------------------------------------
    def login_user(self, email: str, password: str) -> dict[str, Any]:
        data = {"email": email, "password": password}
        response = self._request("POST", "/auth/login/user", json=data, require_auth=False)
        self._update_tokens_from_login(response)
        return response

    def login_patient(self, email: str, password: str) -> dict[str, Any]:
        data = {"email": email, "password": password}
        response = self._request("POST", "/auth/login/patient", json=data, require_auth=False)
        self._update_tokens_from_login(response)
        return response

    def register_user(self, name: str, email: str, password: str) -> dict[str, Any]:
        data = {"name": name, "email": email, "password": password}
        return self._request("POST", "/auth/register/user", json=data, require_auth=False)

    def register_patient(
        self,
        name: str,
        email: str,
        password: str,
        org_id_or_code: str,
        birthdate: str,
        sex_code: str,
        risk_level_code: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": name,
            "email": email,
            "password": password,
            "birthdate": birthdate,
            "sex_code": sex_code,
        }
        if org_id_or_code.count("-") == 4 and len(org_id_or_code) == 36:
            payload["org_id"] = org_id_or_code
        else:
            payload["org_code"] = org_id_or_code
        if risk_level_code:
            payload["risk_level_code"] = risk_level_code
        return self._request("POST", "/auth/register/patient", json=payload, require_auth=False)

    def verify_token(self) -> bool:
        try:
            self._request("GET", "/auth/verify")
            return True
        except ApiError as exc:
            LOGGER.info("Token verification failed: %s", exc)
            return False

    def get_me(self) -> dict[str, Any]:
        return self._request("GET", "/auth/me")

    def _update_tokens_from_login(self, response: Mapping[str, Any]) -> None:
        access_token = response.get("access_token")
        refresh_token = response.get("refresh_token")
        if access_token:
            self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token

    # ------------------------------------------------------------------
    # User scoped endpoints
    # ------------------------------------------------------------------
    def get_current_user_profile(self) -> dict[str, Any]:
        return self._request("GET", "/users/me")

    def get_current_user_memberships(self) -> list[dict[str, Any]]:
        data = self._request("GET", "/users/me/org-memberships")
        if isinstance(data, dict):
            payload = data.get("data")
            if isinstance(payload, dict):
                memberships = payload.get("memberships", [])
                return list(memberships)
            if isinstance(payload, list):
                return list(payload)
        return []

    def get_pending_invitations(self) -> list[dict[str, Any]]:
        data = self._request("GET", "/users/me/invitations")
        invitations = data.get("data", {}).get("invitations", []) if isinstance(data, dict) else []
        return list(invitations)

    def accept_invitation(self, invitation_id: str) -> Any:
        return self._request("POST", f"/users/me/invitations/{invitation_id}/accept")

    def reject_invitation(self, invitation_id: str) -> Any:
        return self._request("POST", f"/users/me/invitations/{invitation_id}/reject")

    def update_user_profile(self, updates: Mapping[str, Any]) -> Any:
        return self._request("PATCH", "/users/me", json=dict(updates))

    # Organization dashboard
    def get_organization_dashboard(self, org_id: str) -> dict[str, Any]:
        return self._request("GET", f"/orgs/{org_id}/dashboard")

    def get_organization_metrics(self, org_id: str) -> dict[str, Any]:
        return self._request("GET", f"/orgs/{org_id}/metrics")

    def get_caregiver_patients(self) -> dict[str, Any]:
        return self._request("GET", "/caregiver/patients")

    def get_caregiver_patients_locations(self, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return self._request("GET", "/caregiver/patients/locations", params=params or {})

    def get_caregiver_patient(self, patient_id: str) -> dict[str, Any]:
        return self._request("GET", f"/caregiver/patients/{patient_id}")

    def get_caregiver_patient_locations(self, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return self._request("GET", "/caregiver/patients/locations", params=params or {})

    def get_care_team_locations(self, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return self._request("GET", "/care-team/locations", params=params or {})

    def get_care_team_patients(self, org_id: str) -> dict[str, Any]:
        return self._request("GET", f"/orgs/{org_id}/care-team-patients")

    def get_care_team_devices(self, org_id: str, team_id: str) -> dict[str, Any]:
        return self._request("GET", f"/orgs/{org_id}/care-teams/{team_id}/devices")

    def get_care_team_disconnected_devices(self, org_id: str, team_id: str) -> dict[str, Any]:
        return self._request("GET", f"/orgs/{org_id}/care-teams/{team_id}/devices/disconnected")

    def get_care_team_device_streams(self, org_id: str, team_id: str, device_id: str) -> dict[str, Any]:
        return self._request("GET", f"/orgs/{org_id}/care-teams/{team_id}/devices/{device_id}/streams")

    def get_caregiver_patient_alerts(self, patient_id: str, limit: int = 10) -> dict[str, Any]:
        params = {"limit": limit}
        return self._request("GET", f"/caregiver/patients/{patient_id}/alerts", params=params)

    def get_caregiver_patient_notes(self, patient_id: str) -> dict[str, Any]:
        return self._request("GET", f"/caregiver/patients/{patient_id}/notes")

    # ------------------------------------------------------------------
    # Patient scoped endpoints
    # ------------------------------------------------------------------
    def get_patient_dashboard(self) -> dict[str, Any]:
        return self._request("GET", "/patient/dashboard")

    def get_patient_profile(self) -> dict[str, Any]:
        return self._request("GET", "/patient/profile")

    def get_patient_alerts(self, limit: int = 10, offset: int = 0, status: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return self._request("GET", "/patient/alerts", params=params)

    def get_patient_devices(self) -> dict[str, Any]:
        return self._request("GET", "/patient/devices")

    def get_patient_caregivers(self) -> dict[str, Any]:
        return self._request("GET", "/patient/caregivers")

    def get_patient_readings(self, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        params = {"limit": limit, "offset": offset}
        return self._request("GET", "/patient/readings", params=params)

    def get_patient_care_team(self) -> dict[str, Any]:
        return self._request("GET", "/patient/care-team")

    def get_patient_locations(self, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        params = {"limit": limit, "offset": offset}
        return self._request("GET", "/patient/locations", params=params)

    def get_patient_latest_location(self) -> dict[str, Any]:
        return self._request("GET", "/patient/location/latest")


def with_error_handling(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for controller methods to catch :class:`ApiError`."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except ApiError as exc:
            LOGGER.error("API error: %s", exc)
            raise

    return wrapper
