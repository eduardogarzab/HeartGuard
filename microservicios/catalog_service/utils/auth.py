"""Authentication helpers for catalog service."""
from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict

import jwt
from flask import current_app, g, request


class AuthenticationError(Exception):
    """Raised when token validation fails."""


def _extract_token() -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1]
    return auth_header


def token_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to validate JWT tokens and expose user/org identifiers."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        token = _extract_token()
        if not token:
            raise AuthenticationError("Authorization token missing")

        try:
            payload: Dict[str, Any] = jwt.decode(
                token,
                current_app.config.get("JWT_SECRET", ""),
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        except jwt.PyJWTError as exc:  # pragma: no cover - runtime safety
            raise AuthenticationError("Invalid token") from exc

        user_id = payload.get("sub") or payload.get("user_id")
        org_id = payload.get("org_id")
        if not user_id:
            raise AuthenticationError("User identifier missing in token")
        if org_id is None:
            raise AuthenticationError("Organization identifier missing in token")

        g.user_id = user_id
        g.org_id = org_id
        g.token_payload = payload

        return func(*args, **kwargs)

    return wrapper
