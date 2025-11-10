"""Utilidades para verificar JWT en el Media Service."""
from __future__ import annotations

from typing import Any, Dict

import jwt
from flask import current_app


def decode_token(token: str) -> Dict[str, Any]:
    """Decodifica un JWT utilizando la configuración de la aplicación."""
    if not token:
        raise ValueError("Token no proporcionado")

    secret = current_app.config.get("JWT_SECRET")
    algorithm = current_app.config.get("JWT_ALGORITHM", "HS256")
    if not secret:
        raise ValueError("Configuración JWT incompleta")

    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.ExpiredSignatureError as exc:  # pragma: no cover - dependiente de tiempo
        raise ValueError("Token expirado") from exc
    except jwt.InvalidTokenError as exc:  # pragma: no cover - librería
        raise ValueError("Token inválido") from exc


def extract_token_from_header(header_value: str | None) -> str:
    """Obtiene el token del encabezado Authorization."""
    if not header_value:
        raise ValueError("Encabezado Authorization ausente")

    parts = header_value.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("Authorization debe ser 'Bearer <token>'")

    return parts[1]
