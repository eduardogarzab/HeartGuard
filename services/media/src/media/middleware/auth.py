"""Middleware de autenticación para Media Service."""
from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import Callable, Iterable

from flask import Response, current_app, g, request

from ..utils.jwt_utils import decode_token, extract_token_from_header
from ..utils.responses import error_response, fail_response


@dataclass(frozen=True, slots=True)
class AuthSubject:
    """Representa el sujeto autenticado a partir del JWT."""

    account_type: str
    user_id: str | None = None
    patient_id: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> "AuthSubject":
        account_type = str(payload.get("account_type", ""))
        if account_type not in {"user", "patient"}:
            raise ValueError("Token no pertenece a un sujeto soportado")
        user_id = payload.get("user_id")
        patient_id = payload.get("patient_id")
        if account_type == "user" and not user_id:
            raise ValueError("Token de usuario sin user_id")
        if account_type == "patient" and not patient_id:
            raise ValueError("Token de paciente sin patient_id")
        return cls(account_type=account_type, user_id=str(user_id) if user_id else None, patient_id=str(patient_id) if patient_id else None)

    def is_user(self) -> bool:
        return self.account_type == "user"

    def is_patient(self) -> bool:
        return self.account_type == "patient"

    @property
    def subject_id(self) -> str:
        if self.is_user() and self.user_id:
            return self.user_id
        if self.is_patient() and self.patient_id:
            return self.patient_id
        raise ValueError("Subject sin identificador válido")


def require_token(*, allow: Iterable[str] | None = None) -> Callable:
    """Decorador que valida el JWT y pasa el sujeto autenticado.

    Args:
        allow: Iterable con los tipos de cuenta permitidos (`user`, `patient`).
    """

    allowed_types = {typ.lower() for typ in allow} if allow else {"user", "patient"}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                token = extract_token_from_header(request.headers.get("Authorization"))
                payload = decode_token(token)
                subject = AuthSubject.from_payload(payload)
                if subject.account_type not in allowed_types:
                    return fail_response(message="Token no autorizado para esta operación", error_code="forbidden", status_code=403)
                g.current_subject = subject
                kwargs["auth_subject"] = subject
                return func(*args, **kwargs)
            except ValueError as exc:
                return fail_response(message=str(exc), error_code="unauthorized", status_code=401)
            except Exception:  # pragma: no cover - defensivo
                current_app.logger.exception("Error al validar token", extra={"trace_id": getattr(g, "trace_id", None)})
                return error_response(message="Error al validar token", error_code="unauthorized", status_code=401)

        return wrapper

    return decorator
