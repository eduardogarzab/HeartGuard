"""HTTP helpers and decorators shared across the analytics service."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict, Optional

from flask import Response, g, jsonify, request

from config import settings


def create_response(
    data: Optional[Dict[str, Any]] = None,
    *,
    message: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
    errors: Optional[Dict[str, Any]] = None,
) -> tuple[Response, int]:
    """Return a standardized JSON response."""

    payload: Dict[str, Any] = {"status": "ok" if status_code < 400 else "error"}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    if meta is not None:
        payload["meta"] = meta
    if errors:
        payload["errors"] = errors
    return jsonify(payload), status_code


def require_auth(fn: Callable) -> Callable:
    """Decorator ensuring the request carries the user context headers."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = request.headers.get("X-User-Id")
        role = (request.headers.get("X-User-Role") or "").strip().lower()
        org_id = request.headers.get("X-Org-Id")

        if not user_id:
            return create_response(message="Missing authentication context", status_code=401)
        if not org_id and role != "superadmin":
            return create_response(message="Organization context required", status_code=400)

        g.user_id = user_id
        g.role = role
        g.org_id = org_id
        return fn(*args, **kwargs)

    return wrapper


def require_internal_api_key(fn: Callable) -> Callable:
    """Protect endpoints with the configured internal API key."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        expected_key = settings.INTERNAL_API_KEY
        provided_key = request.headers.get("X-Internal-API-Key")

        if not expected_key:
            return create_response(message="Internal API key is not configured", status_code=500)
        if not provided_key or provided_key != expected_key:
            return create_response(message="Forbidden", status_code=403)

        return fn(*args, **kwargs)

    return wrapper

