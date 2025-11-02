"""Blueprint principal de autenticación."""
from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, current_app, request

from ..errors import ForbiddenError, ValidationError
from ..services.auth_service import AuthService

bp = Blueprint("auth", __name__, url_prefix="/auth")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _service() -> AuthService:
    return AuthService(current_app.config)


def _json() -> dict:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Se esperaba un cuerpo JSON")
    return payload


def _bearer_token() -> str:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise ValidationError("Se requiere Authorization Bearer")
    return header.split(" ", 1)[1]


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------


@bp.post("/register/user")
def register_user():
    payload = _json()
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""

    if not name or not email or not password:
        raise ValidationError("Nombre, email y contraseña son obligatorios")

    result = _service().register_user(name=name, email=email, password=password)
    return result, HTTPStatus.CREATED


@bp.post("/register/patient")
def register_patient():
    payload = _json()
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    org_id = (payload.get("org_id") or "").strip()

    if not name or not email or not password or not org_id:
        raise ValidationError("Nombre, email, contraseña y org_id son obligatorios")

    result = _service().register_patient(
        name=name,
        email=email,
        password=password,
        org_id=org_id,
        birthdate=payload.get("birthdate"),
        sex_code=payload.get("sex_code"),
        risk_level_code=payload.get("risk_level_code"),
    )
    return result, HTTPStatus.CREATED


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@bp.post("/login/user")
def login_user():
    payload = _json()
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    if not email or not password:
        raise ValidationError("Email y contraseña son obligatorios")
    return _service().login_user(email=email, password=password), HTTPStatus.OK


@bp.post("/login/patient")
def login_patient():
    payload = _json()
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    if not email or not password:
        raise ValidationError("Email y contraseña son obligatorios")
    return _service().login_patient(email=email, password=password), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Invitaciones
# ---------------------------------------------------------------------------


@bp.post("/accept-invitation/<string:token>")
def accept_invitation(token: str):
    access_token = _bearer_token()
    verification = _service().verify(access_token=access_token)
    payload = verification["payload"]
    if payload.get("account_type") != "user":
        raise ForbiddenError("Solo usuarios del staff pueden aceptar invitaciones")

    result = _service().accept_invitation(
        token=token,
        user_id=payload["user_id"],
        user_email=payload.get("email", ""),
    )
    return result, HTTPStatus.OK


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------


@bp.post("/refresh")
def refresh():
    payload = _json()
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise ValidationError("refresh_token es requerido")
    return _service().refresh(refresh_token=refresh_token), HTTPStatus.OK


@bp.get("/verify")
def verify():
    access_token = _bearer_token()
    return _service().verify(access_token=access_token), HTTPStatus.OK


@bp.get("/me")
def me():
    access_token = _bearer_token()
    return _service().account_details(access_token=access_token), HTTPStatus.OK