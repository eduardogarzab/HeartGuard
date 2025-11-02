"""Cliente HTTP para interactuar con Auth Service."""
from __future__ import annotations

from typing import Any, Mapping

import requests


class AuthClient:
    """Invocaciones al microservicio de autenticación."""

    def __init__(self, base_url: str, *, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Usuarios / pacientes
    # ------------------------------------------------------------------
    def login_user(self, email: str, password: str) -> dict[str, Any]:
        payload = {"email": email, "password": password}
        return self._post("/auth/login/user", json=payload)

    def login_patient(self, email: str, password: str) -> dict[str, Any]:
        payload = {"email": email, "password": password}
        return self._post("/auth/login/patient", json=payload)

    def register_user(self, data: Mapping[str, Any]) -> dict[str, Any]:
        return self._post("/auth/register/user", json=dict(data))

    def register_patient(self, data: Mapping[str, Any]) -> dict[str, Any]:
        return self._post("/auth/register/patient", json=dict(data))

    # ------------------------------------------------------------------
    # Tokens
    # ------------------------------------------------------------------
    def refresh(self, refresh_token: str) -> dict[str, Any]:
        return self._post("/auth/refresh", json={"refresh_token": refresh_token})

    def verify(self, access_token: str) -> dict[str, Any]:
        return self._get("/auth/verify", headers={"Authorization": f"Bearer {access_token}"})

    def me(self, access_token: str) -> dict[str, Any]:
        return self._get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})

    # ------------------------------------------------------------------
    # Helpers HTTP
    # ------------------------------------------------------------------
    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _post(self, path: str, *, json: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None) -> dict[str, Any]:
        response = requests.post(
            self._url(path),
            json=json,
            headers=headers,
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def _get(self, path: str, *, headers: Mapping[str, str] | None = None) -> dict[str, Any]:
        response = requests.get(
            self._url(path),
            headers=headers,
            timeout=self.timeout,
        )
        return self._handle_response(response)

    @staticmethod
    def _handle_response(response: requests.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:  # pragma: no cover
            response.raise_for_status()
            raise exc
        if response.ok:
            return payload
        detail = payload if isinstance(payload, dict) else {"error": payload}
        raise AuthClientError(response.status_code, detail.get("error"), detail.get("message"))


class AuthClientError(Exception):
    """Errores provenientes del servicio Auth."""

    def __init__(self, status_code: int, error: str | None, message: str | None) -> None:
        self.status_code = status_code
        self.error = error or "auth_client_error"
        self.message = message or "Error al invocar Auth Service"
        super().__init__(f"[{status_code}] {self.error}: {self.message}")
