from werkzeug.exceptions import HTTPException
from flask import Flask

from .utils_format import error_response


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http(exc: HTTPException):
        return error_response(exc.code or 500, exc.description)

    @app.errorhandler(Exception)
    def handle_generic(exc: Exception):  # pragma: no cover
        app.logger.exception("Unhandled error")
        return error_response(500, "Internal server error")
