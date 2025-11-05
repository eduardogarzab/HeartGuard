"""
Utilidades para trabajar con JWT del User Service
"""
from __future__ import annotations

from typing import Any, Dict

import jwt

from ..config import get_config

config = get_config()


def decode_token(token: str) -> Dict[str, Any]:
    """Decodifica y valida un JWT genérico."""
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:  # pragma: no cover - dependiente de tiempo
        raise ValueError("Token expirado") from exc
    except jwt.InvalidTokenError as exc:  # pragma: no cover - dependiente del token
        raise ValueError("Token inválido") from exc


def verify_user_token(token: str) -> Dict[str, Any]:
    """Verifica que el token corresponda a un usuario válido."""
    payload = decode_token(token)

    if payload.get('account_type') != 'user':
        raise ValueError("Token no pertenece a un usuario")

    if 'user_id' not in payload:
        raise ValueError("Token no contiene user_id")

    return payload


def extract_token_from_header(authorization_header: str | None) -> str:
    """Extrae el token del encabezado Authorization."""
    if not authorization_header:
        raise ValueError("Header Authorization no proporcionado")

    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise ValueError("Header Authorization debe ser 'Bearer <token>'")

    return parts[1]
