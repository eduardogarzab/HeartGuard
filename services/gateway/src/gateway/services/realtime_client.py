"""Cliente HTTP para el Realtime Data Generator Service."""
from __future__ import annotations

from http import HTTPStatus
from typing import Any

import requests


class RealtimeClientError(Exception):
    """Excepción específica para errores del Realtime Service."""

    def __init__(self, message: str, status_code: int, error: str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error = error or "realtime_service_error"


class RealtimeClient:
    """Cliente para comunicarse con el Realtime Data Generator Service."""

    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def proxy_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        data: bytes | None = None,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        """
        Reenvía la petición HTTP al Realtime Service.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            path: Ruta del endpoint (ej: '/health')
            headers: Encabezados HTTP opcionales
            json: Cuerpo JSON opcional
            data: Cuerpo raw opcional
            params: Query parameters opcionales
            
        Returns:
            Response directo de requests
            
        Raises:
            RealtimeClientError: Si hay error de conexión o el servicio responde con error
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
            response.raise_for_status()
            return response

        except requests.HTTPError as exc:
            try:
                error_data = exc.response.json()
                error_msg = error_data.get("message", str(exc))
                error_code = error_data.get("error", "http_error")
            except Exception:
                error_msg = str(exc)
                error_code = "http_error"

            raise RealtimeClientError(
                message=error_msg,
                status_code=exc.response.status_code,
                error=error_code,
            ) from exc

        except requests.RequestException as exc:
            raise RealtimeClientError(
                message=f"Error de conexión con Realtime Service: {str(exc)}",
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                error="connection_error",
            ) from exc
