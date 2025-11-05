"""Factory para respuestas JSON consistentes"""
from __future__ import annotations

import uuid
from typing import Any

from flask import Response, jsonify, g


def _ensure_trace_id() -> str:
    trace_id = getattr(g, 'trace_id', None)
    if not trace_id:
        trace_id = uuid.uuid4().hex
        g.trace_id = trace_id
    return trace_id


def build_response(*, status: str, message: str | None, data: Any, error: Any, status_code: int) -> tuple[Response, int]:
    """Construye una respuesta JSON con la forma estándar."""
    trace_id = _ensure_trace_id()
    payload = {
        'status': status,
        'message': message,
        'error': error,
        'data': data,
        'trace_id': trace_id,
    }
    return jsonify(payload), status_code


def success_response(*, data: Any = None, message: str | None = 'OK', status_code: int = 200) -> tuple[Response, int]:
    """Respuesta de éxito."""
    return build_response(status='success', message=message, data=data, error=None, status_code=status_code)


def fail_response(*, message: str, error_code: str = 'validation_error', data: Any = None, status_code: int = 400) -> tuple[Response, int]:
    """Respuesta para errores de validación o negocio controlados."""
    error_payload = {'code': error_code}
    return build_response(status='fail', message=message, data=data, error=error_payload, status_code=status_code)


def error_response(*, message: str, error_code: str = 'internal_error', data: Any = None, status_code: int = 500) -> tuple[Response, int]:
    """Respuesta para errores inesperados."""
    error_payload = {'code': error_code}
    return build_response(status='error', message=message, data=data, error=error_payload, status_code=status_code)
