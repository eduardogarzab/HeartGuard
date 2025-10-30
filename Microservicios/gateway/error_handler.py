from werkzeug.exceptions import HTTPException
from flask import Flask

from .utils_format import error_response


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        return error_response(exc.code or 500, exc.description)

    @app.errorhandler(Exception)
    def handle_exception(exc: Exception):  # pragma: no cover - generic safeguard
        app.logger.exception("Unhandled exception")
        return error_response(500, "Internal server error")
