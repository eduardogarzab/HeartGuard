"""HTTP client that mirrors the Java ApiClient but using `requests`."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

from ..models import LoginResponse
from .errors import ApiError

DEFAULT_GATEWAY_URL = os.getenv("HEARTGUARD_GATEWAY_URL", "http://136.115.53.140:8080")


class ApiClient:
    """Simplified wrapper around the HeartGuard gateway endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        timeout: float = 15.0,
    ) -> None:
        self.base_url = (base_url or DEFAULT_GATEWAY_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.access_token: Optional[str] = None

    # ------------------------------------------------------------------
    # General helpers
    # ------------------------------------------------------------------
    def set_access_token(self, token: Optional[str]) -> None:
        self.access_token = token

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        json_payload: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None,
        require_auth: bool = False,
        error_message: str = "Error al comunicarse con el gateway",
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers: Dict[str, str] = {"Accept": "application/json"}
        if json_payload is not None:
            headers["Content-Type"] = "application/json"

        auth_token = token or self.access_token
        if require_auth:
            if not auth_token:
                raise ApiError("Token de acceso no disponible")
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            response = self.session.request(
                method,
                url,
                json=json_payload,
                params=query,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise ApiError(f"Error de conexión: {exc}") from exc

        if response.status_code == 204 or not response.content:
            if response.ok:
                return {}
            self._raise_api_error(response, error_message)

        if not response.ok:
            self._raise_api_error(response, error_message)

        try:
            return response.json()
        except ValueError as exc:
            raise ApiError(
                "Respuesta inválida del servidor",
                status_code=response.status_code,
                payload=response.text,
            ) from exc

    def _raise_api_error(self, response: requests.Response, fallback_message: str) -> None:
        message = fallback_message
        error_code: Optional[str] = None
        payload: Any = None

        try:
            payload = response.json()
            if isinstance(payload, dict):
                error_code = self._extract_error_code(payload)
                message = self._extract_error_message(payload) or message
        except ValueError:
            payload = response.text

        raise ApiError(message, status_code=response.status_code, error_code=error_code, payload=payload)

    @staticmethod
    def _extract_error_code(payload: Dict[str, Any]) -> Optional[str]:
        error_value = payload.get("error")
        if isinstance(error_value, dict):
            raw = error_value.get("code")
            return str(raw) if raw is not None else None
        if error_value is not None:
            return str(error_value)
        return None

    @staticmethod
    def _extract_error_message(payload: Dict[str, Any]) -> Optional[str]:
        message = payload.get("message")
        if isinstance(message, (dict, list)):
            return str(message)
        if message:
            return str(message)
        return None

    # ------------------------------------------------------------------
    # Auth flows
    # ------------------------------------------------------------------
    def login_user(self, email: str, password: str) -> LoginResponse:
        data = self._request_json(
            "post",
            "/auth/login/user",
            json_payload={"email": email, "password": password},
            error_message="No se pudo iniciar sesión (usuario)",
        )
        login = LoginResponse.from_dict(data)
        if login.access_token:
            self.set_access_token(login.access_token)
        return login

    def login_patient(self, email: str, password: str) -> LoginResponse:
        data = self._request_json(
            "post",
            "/auth/login/patient",
            json_payload={"email": email, "password": password},
            error_message="No se pudo iniciar sesión (paciente)",
        )
        login = LoginResponse.from_dict(data)
        if login.access_token:
            self.set_access_token(login.access_token)
        return login

    def register_user(self, email: str, password: str, name: str) -> LoginResponse:
        data = self._request_json(
            "post",
            "/auth/register/user",
            json_payload={"email": email, "password": password, "name": name},
            error_message="No se pudo registrar al usuario",
        )
        return LoginResponse.from_dict(data or {"account_type": "user"})

    def register_patient(
        self,
        email: str,
        password: str,
        name: str,
        org_id_or_code: str,
        birthdate: str,
        sex_code: str,
        risk_level_code: Optional[str] = None,
    ) -> LoginResponse:
        payload: Dict[str, Any] = {
            "email": email,
            "password": password,
            "name": name,
            "birthdate": birthdate,
            "sex_code": sex_code,
        }
        if "-" in org_id_or_code and len(org_id_or_code) >= 36:
            payload["org_id"] = org_id_or_code
        else:
            payload["org_code"] = org_id_or_code
        if risk_level_code:
            payload["risk_level_code"] = risk_level_code

        data = self._request_json(
            "post",
            "/auth/register/patient",
            json_payload=payload,
            error_message="No se pudo registrar al paciente",
        )
        return LoginResponse.from_dict(data or {"account_type": "patient"})

    # ------------------------------------------------------------------
    # Patient endpoints
    # ------------------------------------------------------------------
    def get_patient_dashboard(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._request_json(
            "get",
            "/patient/dashboard",
            token=token,
            require_auth=True,
            error_message="No se pudo cargar el dashboard del paciente",
        )

    def get_patient_alerts(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {"limit": max(1, limit), "offset": max(0, offset)}
        if status:
            query["status"] = status
        return self._request_json(
            "get",
            "/patient/alerts",
            query=query,
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener las alertas",
        )

    def get_patient_devices(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._request_json(
            "get",
            "/patient/devices",
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener los dispositivos",
        )

    def get_patient_locations(self, *, limit: int = 10, token: Optional[str] = None) -> Dict[str, Any]:
        query = {"limit": max(1, limit)}
        return self._request_json(
            "get",
            "/patient/locations",
            query=query,
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener las ubicaciones",
        )

    def get_patient_caregivers(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._request_json(
            "get",
            "/patient/caregivers",
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener los cuidadores",
        )

    def get_patient_care_team(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._request_json(
            "get",
            "/patient/care-team",
            token=token,
            require_auth=True,
            error_message="No se pudo obtener el equipo de cuidado",
        )

    # ------------------------------------------------------------------
    # User (staff) endpoints
    # ------------------------------------------------------------------
    def get_current_user_profile(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._request_json(
            "get",
            "/users/me",
            token=token,
            require_auth=True,
            error_message="No se pudo obtener el perfil",
        )

    def get_current_user_memberships(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._request_json(
            "get",
            "/users/me/org-memberships",
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener las organizaciones",
        )

    def get_pending_invitations(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._request_json(
            "get",
            "/users/me/invitations",
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener las invitaciones",
        )

    def get_organization_dashboard(self, org_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._request_json(
            "get",
            f"/orgs/{org_id}/dashboard",
            token=token,
            require_auth=True,
            error_message="No se pudo obtener el dashboard de la organización",
        )

    def get_organization_metrics(self, org_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._request_json(
            "get",
            f"/orgs/{org_id}/metrics",
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener las métricas",
        )

    def get_organization_care_teams(self, org_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._request_json(
            "get",
            f"/orgs/{org_id}/care-teams",
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener los equipos",
        )

    def get_organization_care_team_patients(self, org_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._request_json(
            "get",
            f"/orgs/{org_id}/care-team-patients",
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener los pacientes por equipo",
        )

    def get_caregiver_patients(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._request_json(
            "get",
            "/caregiver/patients",
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener los pacientes asignados",
        )

    def get_caregiver_patient_alerts(
        self, 
        patient_id: str, 
        *, 
        limit: int = 10,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtiene las alertas de un paciente específico (como caregiver)."""
        return self._request_json(
            "get",
            f"/caregiver/patients/{patient_id}/alerts",
            query={"limit": limit},
            token=token,
            require_auth=True,
            error_message=f"No se pudieron obtener las alertas del paciente {patient_id}",
        )

    def get_organization_patient_alerts(
        self,
        org_id: str,
        patient_id: str,
        *,
        limit: int = 10,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtiene las alertas de un paciente específico (como admin de org)."""
        return self._request_json(
            "get",
            f"/orgs/{org_id}/patients/{patient_id}/alerts",
            query={"limit": limit},
            token=token,
            require_auth=True,
            error_message=f"No se pudieron obtener las alertas del paciente {patient_id}",
        )

    # ------------------------------------------------------------------
    # Map & locations
    # ------------------------------------------------------------------
    def get_care_team_locations(
        self,
        *,
        org_id: Optional[str] = None,
        token: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = dict(extra_params or {})
        if org_id:
            query.setdefault("org_id", org_id)
        return self._request_json(
            "get",
            "/care-team/locations",
            query=query or None,
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener las ubicaciones de equipos",
        )

    def get_caregiver_patient_locations(
        self,
        *,
        org_id: Optional[str] = None,
        token: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = dict(extra_params or {})
        if org_id:
            query.setdefault("org_id", org_id)
        return self._request_json(
            "get",
            "/caregiver/patients/locations",
            query=query or None,
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener las ubicaciones de pacientes",
        )

    # ------------------------------------------------------------------
    # Devices
    # ------------------------------------------------------------------
    def get_care_team_devices(
        self,
        org_id: str,
        team_id: str,
        *,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._request_json(
            "get",
            f"/orgs/{org_id}/care-teams/{team_id}/devices",
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener los dispositivos del equipo",
        )

    def get_care_team_disconnected_devices(
        self,
        org_id: str,
        team_id: str,
        *,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._request_json(
            "get",
            f"/orgs/{org_id}/care-teams/{team_id}/devices/disconnected",
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener los dispositivos desconectados",
        )

    def get_care_team_device_streams(
        self,
        org_id: str,
        team_id: str,
        device_id: str,
        *,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._request_json(
            "get",
            f"/orgs/{org_id}/care-teams/{team_id}/devices/{device_id}/streams",
            token=token,
            require_auth=True,
            error_message="No se pudieron obtener los streams del dispositivo",
        )
