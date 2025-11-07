"""Cliente HTTP en Python equivalente al ``ApiClient`` de la app Java."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from .config import API_SETTINGS
from .models import auth as auth_models
from .utils.async_utils import run_in_executor


class ApiError(RuntimeError):
    """Error lanzado cuando el backend responde con un código diferente de 2xx."""

    def __init__(self, message: str, status_code: Optional[int] = None, error_code: str = "unknown_error", payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.payload = payload


@dataclass
class _RequestContext:
    method: str
    path: str
    requires_token: bool = True
    params: Optional[Dict[str, Any]] = None
    json_body: Optional[Dict[str, Any]] = None
    token_override: Optional[str] = None


class ApiClient:
    """Cliente HTTP que encapsula todas las llamadas usadas por la app de escritorio."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or API_SETTINGS.base_url).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.access_token: Optional[str] = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def set_access_token(self, token: Optional[str]) -> None:
        self.access_token = token or None

    # Internal request helper
    def _send(self, ctx: _RequestContext) -> Dict[str, Any]:
        url = f"{self.base_url}{ctx.path}"
        headers: Dict[str, str] = {}
        token = ctx.token_override or self.access_token
        if ctx.requires_token:
            if not token:
                raise ApiError("Token de acceso no proporcionado", status_code=401, error_code="unauthorized")
            headers["Authorization"] = f"Bearer {token}"

        timeout = (API_SETTINGS.connect_timeout, API_SETTINGS.read_timeout)
        try:
            response = self.session.request(
                ctx.method,
                url,
                params=ctx.params,
                json=ctx.json_body,
                headers=headers or None,
                timeout=timeout,
            )
        except requests.RequestException as exc:  # pragma: no cover - errores de red
            raise ApiError(f"Error de conexión: {exc}") from exc

        if response.status_code == 204 or not response.content:
            payload: Dict[str, Any] = {}
        else:
            try:
                payload = response.json()
            except json.JSONDecodeError:
                payload = {"raw": response.text}

        if not response.ok:
            error_code = "unknown_error"
            message = payload.get("message") if isinstance(payload, dict) else None
            if isinstance(payload, dict):
                raw_error = payload.get("error")
                if isinstance(raw_error, str):
                    error_code = raw_error
                elif isinstance(raw_error, dict) and "code" in raw_error:
                    error_code = raw_error["code"]
            if not message:
                message = "Sesión expirada. Por favor, vuelve a iniciar sesión." if response.status_code == 401 else "Error en la petición"
            raise ApiError(message, status_code=response.status_code, error_code=error_code, payload=payload)

        return payload if isinstance(payload, dict) else {"data": payload}

    # Convenience wrappers ------------------------------------------------
    def _get(self, path: str, *, params: Optional[Dict[str, Any]] = None, token: Optional[str] = None, requires_token: bool = True) -> Dict[str, Any]:
        return self._send(_RequestContext("GET", path, requires_token=requires_token, params=params, token_override=token))

    def _post(self, path: str, *, body: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None,
              token: Optional[str] = None, requires_token: bool = True) -> Dict[str, Any]:
        return self._send(_RequestContext("POST", path, requires_token=requires_token, params=params, json_body=body, token_override=token))

    def _patch(self, path: str, *, body: Optional[Dict[str, Any]] = None, token: Optional[str] = None) -> Dict[str, Any]:
        return self._send(_RequestContext("PATCH", path, json_body=body, token_override=token))

    # Autenticación -------------------------------------------------------
    def login_user(self, email: str, password: str) -> auth_models.LoginResponse:
        payload = self._post("/auth/login/user", body={"email": email, "password": password}, requires_token=False)
        response = auth_models.LoginResponse.from_api(payload)
        if response.access_token:
            self.set_access_token(response.access_token)
        return response

    def login_patient(self, email: str, password: str) -> auth_models.LoginResponse:
        payload = self._post("/auth/login/patient", body={"email": email, "password": password}, requires_token=False)
        response = auth_models.LoginResponse.from_api(payload)
        if response.access_token:
            self.set_access_token(response.access_token)
        return response

    def register_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        return self._post(
            "/auth/register/user",
            body={"email": email, "password": password, "name": name},
            requires_token=False,
        )

    def register_patient(self, email: str, password: str, name: str, org_id_or_code: str, birthdate: str,
                         sex_code: str, risk_level_code: Optional[str]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "email": email,
            "password": password,
            "name": name,
            "birthdate": birthdate,
            "sex_code": sex_code,
        }
        if org_id_or_code and len(org_id_or_code) == 36 and org_id_or_code.count("-") == 4:
            payload["org_id"] = org_id_or_code
        else:
            payload["org_code"] = org_id_or_code
        if risk_level_code:
            payload["risk_level_code"] = risk_level_code
        return self._post("/auth/register/patient", body=payload, requires_token=False)

    def verify_token(self) -> bool:
        try:
            self._get("/auth/verify")
            return True
        except ApiError:
            return False

    def get_me(self) -> auth_models.LoginResponse:
        payload = self._get("/auth/me")
        return auth_models.LoginResponse.from_api(payload)

    # Perfil del usuario ---------------------------------------------------
    def get_current_user_profile(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get("/users/me", token=token)

    def get_current_user_memberships(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get("/users/me/org-memberships", token=token)

    def get_pending_invitations(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get("/users/me/invitations", token=token)

    def accept_invitation(self, invitation_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._post(f"/users/me/invitations/{invitation_id}/accept", body={}, token=token)

    def reject_invitation(self, invitation_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._post(f"/users/me/invitations/{invitation_id}/reject", body={}, token=token)

    def update_current_user_profile(self, updates: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        body = {key: value for key, value in updates.items()}
        return self._patch("/users/me", body=body, token=token)

    # Dashboard organizacional --------------------------------------------
    def get_organization_dashboard(self, org_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get(f"/orgs/{org_id}/dashboard", token=token)

    def get_organization_metrics(self, org_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get(f"/orgs/{org_id}/metrics", token=token)

    def get_organization_care_teams(self, org_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get(f"/orgs/{org_id}/care-teams", token=token)

    def get_organization_care_team_patients(self, org_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get(f"/orgs/{org_id}/care-team-patients", token=token)

    def get_organization_patient_detail(self, org_id: str, patient_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get(f"/orgs/{org_id}/patients/{patient_id}", token=token)

    def get_organization_patient_alerts(self, org_id: str, patient_id: str, limit: int = 20,
                                        token: Optional[str] = None) -> Dict[str, Any]:
        params = {"limit": max(1, limit)}
        return self._get(f"/orgs/{org_id}/patients/{patient_id}/alerts", params=params, token=token)

    def get_organization_patient_notes(self, org_id: str, patient_id: str, limit: int = 20,
                                       token: Optional[str] = None) -> Dict[str, Any]:
        params = {"limit": max(1, limit)}
        return self._get(f"/orgs/{org_id}/patients/{patient_id}/notes", params=params, token=token)

    # Pacientes asignados --------------------------------------------------
    def get_caregiver_patients(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get("/caregiver/patients", token=token)

    def get_caregiver_patient_locations(self, params: Optional[Dict[str, Any]] = None,
                                        token: Optional[str] = None) -> Dict[str, Any]:
        return self._get("/caregiver/patients/locations", params=params, token=token)

    def get_care_team_locations(self, params: Optional[Dict[str, Any]] = None, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get("/care-team/locations", params=params, token=token)

    # Dispositivos ---------------------------------------------------------
    def get_care_team_devices(self, org_id: str, team_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get(f"/orgs/{org_id}/care-teams/{team_id}/devices", token=token)

    def get_care_team_disconnected_devices(self, org_id: str, team_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get(f"/orgs/{org_id}/care-teams/{team_id}/devices/disconnected", token=token)

    def get_care_team_device_streams(self, org_id: str, team_id: str, device_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get(f"/orgs/{org_id}/care-teams/{team_id}/devices/{device_id}/streams", token=token)

    # Dashboard del paciente -----------------------------------------------
    def get_patient_dashboard(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get("/patient/dashboard", token=token)

    def get_patient_alerts(self, limit: int = 100, offset: int = 0, status: Optional[str] = None,
                           token: Optional[str] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": max(1, limit), "offset": max(0, offset)}
        if status:
            params["status"] = status
        return self._get("/patient/alerts", params=params, token=token)

    def get_patient_devices(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get("/patient/devices", token=token)

    def get_patient_locations(self, limit: int = 6, offset: int = 0, token: Optional[str] = None) -> Dict[str, Any]:
        params = {"limit": max(1, limit), "offset": max(0, offset)}
        return self._get("/patient/locations", params=params, token=token)

    def get_patient_caregivers(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get("/patient/caregivers", token=token)

    def get_patient_care_team(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self._get("/patient/care-team", token=token)

    # Métodos asíncronos ---------------------------------------------------
    def async_call(self, func_name: str, *args: Any, **kwargs: Any):
        func = getattr(self, func_name)
        return run_in_executor(func, *args, **kwargs)

    def close(self) -> None:  # pragma: no cover - limpieza opcional
        self.session.close()
