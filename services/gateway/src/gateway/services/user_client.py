"""Cliente HTTP para interactuar con User Service."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import requests


class UserClient:
	"""Invocaciones al microservicio de usuarios."""

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
		params: Sequence[tuple[str, str]] | None = None,
	) -> requests.Response:
		"""Realiza una petición HTTP transparente hacia el user-service."""
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
			raise UserClientError(504, "timeout", "El servicio de usuario no respondió a tiempo") from exc
		except requests.ConnectionError as exc:
			raise UserClientError(503, "service_unavailable", "El servicio de usuario no está disponible") from exc
		except Exception as exc:  # pragma: no cover - defensivo
			raise UserClientError(500, "internal_error", "Error al invocar User Service") from exc


class UserClientError(Exception):
	"""Errores provenientes del servicio User."""

	def __init__(self, status_code: int, error: str | None, message: str | None) -> None:
		self.status_code = status_code
		self.error = error or "user_client_error"
		self.message = message or "Error al invocar User Service"
		super().__init__(f"[{status_code}] {self.error}: {self.message}")
