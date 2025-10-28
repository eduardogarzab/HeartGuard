"""Helpers related to authentication for the gateway service."""

from functools import wraps

import jwt
from flask import g, jsonify, request

from config import Config


def _extract_bearer_token() -> str | None:
    """Return the bearer token sent in the Authorization header, if any."""

    header_value = request.headers.get("Authorization", "").strip()
    if not header_value:
        return None

    parts = header_value.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("Formato de token inválido")
    return parts[1]


def token_required(fn):
    """Ensure the request includes a valid JWT before proxying it."""

    @wraps(fn)
    def decorated(*args, **kwargs):
        try:
            token = _extract_bearer_token()
        except ValueError as exc:
            return jsonify({"message": str(exc)}), 401

        if not token:
            return jsonify({"message": "Token es requerido"}), 401

        try:
            claims = jwt.decode(
                token,
                Config.JWT_SECRET_KEY,
                algorithms=[Config.JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token ha expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token inválido"}), 401
        except Exception as exc:  # pragma: no cover - caso inesperado
            return (
                jsonify({"message": "Error al procesar el token", "error": str(exc)}),
                401,
            )

        identity = claims.get("identity") or {}
        if not isinstance(identity, dict):
            identity = {}

        g.token_claims = claims
        g.user_id = identity.get("user_id")

        org_id = identity.get("org_id") or request.headers.get("X-Org-ID")
        g.org_id = org_id

        return fn(*args, **kwargs)

    return decorated

