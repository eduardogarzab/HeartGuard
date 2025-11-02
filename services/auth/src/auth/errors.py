"""Definición de errores controlados para Auth Service."""
from __future__ import annotations

from http import HTTPStatus
from typing import Any, Mapping


class AuthServiceError(Exception):
    """Base para excepciones controladas."""

    status_code = HTTPStatus.BAD_REQUEST
    error_code = "auth_error"

    def __init__(self, message: str, *, extra: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.extra = dict(extra or {})

    def to_response(self) -> dict[str, Any]:
        payload = {"error": self.error_code, "message": self.message}
        if self.extra:
            payload["details"] = self.extra
        return payload


class ConflictError(AuthServiceError):
    status_code = HTTPStatus.CONFLICT
    error_code = "conflict"


class UnauthorizedError(AuthServiceError):
    status_code = HTTPStatus.UNAUTHORIZED
    error_code = "unauthorized"


class NotFoundError(AuthServiceError):
    status_code = HTTPStatus.NOT_FOUND
    error_code = "not_found"


class ForbiddenError(AuthServiceError):
    status_code = HTTPStatus.FORBIDDEN
    error_code = "forbidden"


class ValidationError(AuthServiceError):
    status_code = HTTPStatus.BAD_REQUEST
    error_code = "validation_error"


def register_error_handlers(app) -> None:
    """Registra manejadores globales de errores."""

    @app.errorhandler(AuthServiceError)
    def handle_auth_error(exc: AuthServiceError):  # type: ignore[override]
        return exc.to_response(), exc.status_code

    @app.errorhandler(Exception)
    def handle_unknown_error(exc: Exception):  # type: ignore[override]
        app.logger.exception("Error inesperado", exc_info=exc)
        return {"error": "internal_error", "message": "Ha ocurrido un error inesperado"}, HTTPStatus.INTERNAL_SERVER_ERROR
