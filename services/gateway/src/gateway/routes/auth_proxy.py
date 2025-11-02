"""Proxy para rutas de autenticación hacia Auth Service."""
from __future__ import annotations

from http import HTTPStatus
from flask import Blueprint, current_app, jsonify, request

from ..services.auth_client import AuthClient, AuthClientError

bp = Blueprint("auth", __name__, url_prefix="/auth")


def _get_auth_client() -> AuthClient:
    """Obtiene instancia del cliente de autenticación."""
    return AuthClient(
        base_url=current_app.config["AUTH_SERVICE_URL"],
        timeout=current_app.config["GATEWAY_SERVICE_TIMEOUT"],
    )


def _json_or_400():
    """Extrae JSON del request o retorna error 400."""
    if not request.is_json:
        return jsonify({"error": "invalid_request", "message": "Content-Type debe ser application/json"}), HTTPStatus.BAD_REQUEST
    return request.get_json()


def _bearer_token():
    """Extrae el token Bearer del header Authorization."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthClientError(HTTPStatus.UNAUTHORIZED, "missing_token", "Token de autorización requerido")
    return auth_header[7:].strip()


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------

@bp.post("/register/user")
def register_user():
    """Proxy: Registro de usuario (staff)."""
    payload = _json_or_400()
    if isinstance(payload, tuple):  # Error response
        return payload
    
    try:
        client = _get_auth_client()
        result = client.register_user(payload)
        return jsonify(result), HTTPStatus.CREATED
    except AuthClientError as e:
        return jsonify({"error": e.error, "message": e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en register_user: {e}")
        return jsonify({"error": "internal_error", "message": "Error interno del servidor"}), HTTPStatus.INTERNAL_SERVER_ERROR


@bp.post("/register/patient")
def register_patient():
    """Proxy: Registro de paciente."""
    payload = _json_or_400()
    if isinstance(payload, tuple):  # Error response
        return payload
    
    try:
        client = _get_auth_client()
        result = client.register_patient(payload)
        return jsonify(result), HTTPStatus.CREATED
    except AuthClientError as e:
        return jsonify({"error": e.error, "message": e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en register_patient: {e}")
        return jsonify({"error": "internal_error", "message": "Error interno del servidor"}), HTTPStatus.INTERNAL_SERVER_ERROR


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@bp.post("/login/user")
def login_user():
    """Proxy: Login de usuario (staff)."""
    payload = _json_or_400()
    if isinstance(payload, tuple):  # Error response
        return payload
    
    try:
        client = _get_auth_client()
        result = client.login_user(
            email=payload.get("email", "").strip(),
            password=payload.get("password", "")
        )
        return jsonify(result), HTTPStatus.OK
    except AuthClientError as e:
        return jsonify({"error": e.error, "message": e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en login_user: {e}")
        return jsonify({"error": "internal_error", "message": "Error interno del servidor"}), HTTPStatus.INTERNAL_SERVER_ERROR


@bp.post("/login/patient")
def login_patient():
    """Proxy: Login de paciente."""
    payload = _json_or_400()
    if isinstance(payload, tuple):  # Error response
        return payload
    
    try:
        client = _get_auth_client()
        result = client.login_patient(
            email=payload.get("email", "").strip(),
            password=payload.get("password", "")
        )
        return jsonify(result), HTTPStatus.OK
    except AuthClientError as e:
        return jsonify({"error": e.error, "message": e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en login_patient: {e}")
        return jsonify({"error": "internal_error", "message": "Error interno del servidor"}), HTTPStatus.INTERNAL_SERVER_ERROR


# ---------------------------------------------------------------------------
# Token Management
# ---------------------------------------------------------------------------

@bp.post("/refresh")
def refresh():
    """Proxy: Renovar access token con refresh token."""
    payload = _json_or_400()
    if isinstance(payload, tuple):  # Error response
        return payload
    
    try:
        client = _get_auth_client()
        result = client.refresh(refresh_token=payload.get("refresh_token", ""))
        return jsonify(result), HTTPStatus.OK
    except AuthClientError as e:
        return jsonify({"error": e.error, "message": e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en refresh: {e}")
        return jsonify({"error": "internal_error", "message": "Error interno del servidor"}), HTTPStatus.INTERNAL_SERVER_ERROR


@bp.get("/verify")
def verify():
    """Proxy: Verificar validez de access token."""
    try:
        token = _bearer_token()
        client = _get_auth_client()
        result = client.verify(access_token=token)
        return jsonify(result), HTTPStatus.OK
    except AuthClientError as e:
        return jsonify({"error": e.error, "message": e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en verify: {e}")
        return jsonify({"error": "internal_error", "message": "Error interno del servidor"}), HTTPStatus.INTERNAL_SERVER_ERROR


@bp.get("/me")
def me():
    """Proxy: Obtener información de la cuenta autenticada."""
    try:
        token = _bearer_token()
        client = _get_auth_client()
        result = client.me(access_token=token)
        return jsonify(result), HTTPStatus.OK
    except AuthClientError as e:
        return jsonify({"error": e.error, "message": e.message}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en me: {e}")
        return jsonify({"error": "internal_error", "message": "Error interno del servidor"}), HTTPStatus.INTERNAL_SERVER_ERROR
