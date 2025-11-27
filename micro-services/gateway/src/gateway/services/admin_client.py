"""Cliente HTTP para interactuar con Admin Service."""
from __future__ import annotations

from typing import Any, Mapping

import requests


class AdminClient:
    """Invocaciones al microservicio de administración."""

    def __init__(self, base_url: str, *, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Método genérico para proxy transparente
    # ------------------------------------------------------------------
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
        """
        Realiza una petición HTTP al admin-service y retorna la respuesta cruda.
        
        Args:
            method: GET, POST, PATCH, DELETE, etc.
            path: Ruta relativa (ej: /organizations/)
            headers: Headers HTTP a reenviar
            json: Payload JSON (opcional)
            data: Payload raw bytes (opcional)
            params: Query parameters (opcional)
        
        Returns:
            Response object de requests
        """
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
            raise AdminClientError(504, "timeout", "El servicio de administración no respondió a tiempo") from exc
        except requests.ConnectionError as exc:
            raise AdminClientError(503, "service_unavailable", "El servicio de administración no está disponible") from exc
        except Exception as exc:
            raise AdminClientError(500, "internal_error", "Error al invocar Admin Service") from exc


class AdminClientError(Exception):
    """Errores provenientes del servicio Admin."""

    def __init__(self, status_code: int, error: str | None, message: str | None) -> None:
        self.status_code = status_code
        self.error = error or "admin_client_error"
        self.message = message or "Error al invocar Admin Service"
        super().__init__(f"[{status_code}] {self.error}: {self.message}")
