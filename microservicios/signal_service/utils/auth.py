"""Authentication helpers for signal_service."""

from functools import wraps
from typing import Any, Callable, Dict

import jwt
from flask import g, request

from config import settings
from repository.memberships import resolve_org_for_user, user_belongs_to_org
from responses import err


class AuthError(Exception):
    """Custom error for authentication/authorization failures."""


def _extract_bearer_token() -> str:
    header_value = request.headers.get("Authorization", "").strip()
    if not header_value:
        raise AuthError("Token es requerido")

    parts = header_value.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthError("Formato de token inválido")
    return parts[1]


def _decode_token(raw_token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(
            raw_token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Token expirado") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Token inválido") from exc


def _resolve_org_id(identity: Dict[str, Any]) -> str:
    org_id = identity.get("org_id") or request.headers.get("X-Org-ID")
    user_id = identity.get("user_id")
    if not org_id and user_id:
        org_id = resolve_org_for_user(user_id)
    if not org_id:
        raise AuthError("Organización no especificada")
    return str(org_id)


def token_required(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            token = _extract_bearer_token()
            decoded = _decode_token(token)
        except AuthError as exc:
            return err(str(exc), code="auth_error", status=401)

        identity = decoded.get("identity") if isinstance(decoded.get("identity"), dict) else {}
        user_id = identity.get("user_id")
        if not user_id:
            return err("Token sin usuario", code="auth_invalid", status=401)

        try:
            org_id = _resolve_org_id(identity)
        except AuthError as exc:
            return err(str(exc), code="org_missing", status=401)

        if not user_belongs_to_org(user_id, org_id):
            return err("No autorizado para esta organización", code="forbidden", status=403)

        g.token_claims = decoded
        g.user_id = str(user_id)
        g.org_id = str(org_id)
        return fn(*args, **kwargs)

    return wrapper
