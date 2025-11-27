"""Utilidades para generación y validación de JWT."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt


def encode_token(
    payload: dict[str, Any],
    *,
    secret: str,
    algorithm: str,
    expires_minutes: int,
    token_type: str,
) -> str:
    now = datetime.now(timezone.utc)
    scoped_payload = {
        **payload,
        "token_type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(scoped_payload, secret, algorithm=algorithm)


def decode_token(token: str, *, secret: str, algorithms: list[str] | tuple[str, ...]) -> dict[str, Any]:
    return jwt.decode(token, secret, algorithms=algorithms)


def ensure_token_type(payload: dict[str, Any], expected: str) -> None:
    token_type = payload.get("token_type")
    if token_type != expected:
        raise ValueError(f"Se esperaba token de tipo {expected}, recibido {token_type}")
