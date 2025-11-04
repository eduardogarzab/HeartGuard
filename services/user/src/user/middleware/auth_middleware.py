"""Middleware de autenticación JWT para usuarios"""
from __future__ import annotations

from functools import wraps

from flask import current_app, g, request

from ..utils.jwt_utils import extract_token_from_header, verify_user_token
from ..utils.response_builder import error_response, fail_response


def require_user_token(func):
    """Decorator que exige un JWT válido de tipo usuario."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            token = extract_token_from_header(auth_header)
            payload = verify_user_token(token)
            g.current_user_payload = payload
            return func(current_user_id=payload['user_id'], *args, **kwargs)
        except ValueError as exc:
            return fail_response(message=str(exc), error_code='unauthorized', status_code=401)
        except Exception:  # pragma: no cover - defensivo
            current_app.logger.exception('Error al validar token')
            return error_response(message='Error al validar token', error_code='unauthorized', status_code=401)

    return wrapper
