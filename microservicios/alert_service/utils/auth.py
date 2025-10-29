import os
from functools import wraps
from typing import Any, Callable

import jwt
from flask import abort, current_app, g, request


class AuthError(Exception):
    """Custom exception for authentication failures."""


def _get_jwt_secret() -> str:
    secret = current_app.config.get("JWT_SECRET") if current_app else None
    return secret or os.getenv("JWT_SECRET", "")


def token_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that ensures the requester presents a valid JWT token."""

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            abort(401, description="Missing or invalid authorization header")

        token = auth_header.split(" ", 1)[1].strip()
        secret = _get_jwt_secret()
        if not secret:
            abort(500, description="JWT secret is not configured")

        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError as exc:
            raise AuthError("Token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthError("Invalid token") from exc

        user_id = payload.get("user_id")
        org_id = payload.get("org_id")

        if not org_id:
            org_id = request.headers.get("x-org-id") or request.headers.get("X-Org-ID")

        if not org_id:
            abort(403, description="Organization context is required")

        g.user_id = user_id
        g.org_id = org_id

        return f(*args, **kwargs)

    return decorated


__all__ = ["token_required", "AuthError"]
