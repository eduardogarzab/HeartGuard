"""Shared error classes and registration helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from flask import Flask


@dataclass
class APIError(Exception):
    """Uniform API error that integrates with the response envelope."""

    message: str
    status_code: int = 400
    error_id: str = "HG-GENERIC-ERROR"
    details: Any | None = None
    meta: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "status_code": self.status_code,
            "error_id": self.error_id,
            "details": self.details,
            "meta": self.meta,
        }


def register_error_handlers(app: Flask) -> None:
    from .serialization import render_error

    @app.errorhandler(APIError)
    def _handle_api_error(error: APIError):
        app.logger.warning("api_error error_id=%s status_code=%s", error.error_id, error.status_code)
        return render_error(error)

    @app.errorhandler(404)
    def _handle_not_found(_):
        return render_error(APIError("Resource not found", status_code=404, error_id="HG-NOT-FOUND"))

    @app.errorhandler(405)
    def _handle_method_not_allowed(_):
        return render_error(
            APIError("Method not allowed", status_code=405, error_id="HG-METHOD-NOT-ALLOWED")
        )

    @app.errorhandler(Exception)
    def _handle_unexpected(error: Exception):
        app.logger.exception("unexpected_error", exc_info=error)
        return render_error(
            APIError("Internal server error", status_code=500, error_id="HG-INTERNAL-ERROR")
        )
