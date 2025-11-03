"""Application error handlers."""

from __future__ import annotations

from typing import Any, Dict

from flask import Flask, jsonify


class APIError(Exception):
    """Base API error."""

    status_code = 400

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {"error": self.message}


def register_error_handlers(app: Flask) -> None:
    """Register error handlers on the Flask app."""

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):  # type: ignore[override]
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_not_found(error):  # type: ignore[override]
        response = jsonify({"error": "Resource not found"})
        response.status_code = 404
        return response

    @app.errorhandler(500)
    def handle_internal_error(error):  # type: ignore[override]
        response = jsonify({"error": "Internal server error"})
        response.status_code = 500
        return response


__all__ = ["APIError", "register_error_handlers"]
