"""JWT helpers and decorators for microservices."""
from __future__ import annotations

import datetime as dt
import os
from functools import wraps
from typing import Any, Callable, Dict

import jwt
from flask import g, request

from .errors import APIError

DEFAULT_ALGORITHM = "HS256"


class JWTManager:
    """Simple JWT manager based on shared secrets."""

    def __init__(self, secret: str | None = None, algorithm: str = DEFAULT_ALGORITHM):
        self.secret = secret or os.getenv("JWT_SECRET")
        self.algorithm = algorithm

    def encode(self, payload: Dict[str, Any], expires_in: int = 900) -> str:
        claims = payload.copy()
        now = dt.datetime.utcnow()
        claims.setdefault("iat", now)
        claims.setdefault("exp", now + dt.timedelta(seconds=expires_in))
        return jwt.encode(claims, self.secret, algorithm=self.algorithm)

    def decode(self, token: str) -> Dict[str, Any]:
        return jwt.decode(token, self.secret, algorithms=[self.algorithm])


_jwt_manager: JWTManager | None = None


def get_jwt_manager() -> JWTManager:
    global _jwt_manager
    if _jwt_manager is None:
        if os.getenv("JWT_SECRET") is None:
            raise ValueError("JWT_SECRET no está configurado")
        _jwt_manager = JWTManager()
    return _jwt_manager


def require_auth(optional: bool = False, required_roles: list[str] | None = None):
    required_roles = required_roles or []

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header:
                if optional:
                    return func(*args, **kwargs)
                raise APIError("Missing Authorization header", status_code=401, error_id="HG-AUTH-MISSING")
            try:
                scheme, token = auth_header.split(" ", 1)
            except ValueError as exc:
                raise APIError("Invalid Authorization header", status_code=401, error_id="HG-AUTH-BAD") from exc
            if scheme.lower() != "bearer":
                raise APIError("Invalid auth scheme", status_code=401, error_id="HG-AUTH-SCHEME")
            try:
                payload = get_jwt_manager().decode(token)
            except jwt.ExpiredSignatureError as exc:
                raise APIError("Token expired", status_code=401, error_id="HG-AUTH-EXPIRED") from exc
            except jwt.InvalidTokenError as exc:
                raise APIError("Invalid token", status_code=401, error_id="HG-AUTH-INVALID") from exc

            roles = payload.get("roles", [])
            if required_roles and not any(role in roles for role in required_roles):
                raise APIError("Insufficient permissions", status_code=403, error_id="HG-AUTH-FORBIDDEN")

            g.current_user = payload
            return func(*args, **kwargs)

        return wrapper

    return decorator


def issue_tokens(
    user_id: str,
    roles: list[str] | None = None,
    expires_in: int = 900,
    org_id: str | None = None,
) -> Dict[str, Any]:
    roles = roles or ["user"]
    manager = get_jwt_manager()
    access_payload: Dict[str, Any] = {"sub": user_id, "roles": roles}
    if org_id:
        access_payload["org_id"] = str(org_id)
    access_token = manager.encode(access_payload, expires_in=expires_in)
    refresh_ttl = int(os.getenv("REFRESH_TOKEN_TTL", "604800"))
    refresh_payload: Dict[str, Any] = {"sub": user_id, "type": "refresh"}
    if org_id:
        refresh_payload["org_id"] = str(org_id)
    refresh_token = manager.encode(refresh_payload, expires_in=refresh_ttl)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "token_type": "Bearer",
        "roles": roles,
    }
