"""Cliente HTTP para el Media Service."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import requests


class MediaClient:
    """Invocaciones al microservicio de media."""

    def __init__(self, base_url: str, *, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def proxy_request(
        self,
        method: str,
        path: str,
        *,
        headers: Mapping[str, str] | None = None,
        data: bytes | None = None,
        json: Any = None,
        files: Mapping[str, Any] | None = None,
        params: Sequence[tuple[str, str]] | None = None,
    ) -> requests.Response:
        url = f"{self.base_url}{path}"
        try:
            # If files are provided, don't include Content-Type header (let requests set it)
            request_headers = dict(headers) if headers else {}
            if files and "Content-Type" in request_headers:
                del request_headers["Content-Type"]
            
            response = requests.request(
                method=method,
                url=url,
                headers=request_headers or None,
                data=data,
                json=json,
                files=files,
                params=params,
                timeout=self.timeout,
            )
            return response
        except requests.Timeout as exc:
            raise MediaClientError(504, "timeout", "El media-service no respondió a tiempo") from exc
        except requests.ConnectionError as exc:
            raise MediaClientError(503, "service_unavailable", "El media-service no está disponible") from exc
        except Exception as exc:  # pragma: no cover - defensivo
            raise MediaClientError(500, "internal_error", "Error al invocar Media Service") from exc


class MediaClientError(Exception):
    def __init__(self, status_code: int, error: str, message: str) -> None:
        self.status_code = status_code
        self.error = error
        self.message = message
        super().__init__(f"[{status_code}] {error}: {message}")
