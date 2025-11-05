"""Cliente HTTP para interactuar con Patient Service."""
from __future__ import annotations

from typing import Any, Mapping

import requests


class PatientClient:
    """Invocaciones al microservicio de pacientes."""

    def __init__(self, base_url: str, *, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def proxy_request(
        self,
        method: str,
        path: str,
        *,
        headers: Mapping[str, str] | None = None,
        json: Any = None,
        data: bytes | None = None,
        params: Mapping[str, str] | None = None,
    ) -> requests.Response:
        """Realiza una petición HTTP al patient-service y retorna la respuesta cruda."""
        url = f"{self.base_url}{path}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=json,
                data=data,
                params=params,
                timeout=self.timeout,
            )
            return response
        except requests.Timeout as exc:
            raise PatientClientError(504, "timeout", "El servicio de pacientes no respondió a tiempo") from exc
        except requests.ConnectionError as exc:
            raise PatientClientError(503, "service_unavailable", "El servicio de pacientes no está disponible") from exc
        except Exception as exc:
            raise PatientClientError(500, "internal_error", "Error al invocar Patient Service") from exc


class PatientClientError(Exception):
    """Errores provenientes del servicio Patient."""

    def __init__(self, status_code: int, error: str | None, message: str | None) -> None:
        self.status_code = status_code
        self.error = error or "patient_client_error"
        self.message = message or "Error al invocar Patient Service"
        super().__init__(f"[{status_code}] {self.error}: {self.message}")
