"""Proxy para rutas del Patient Service."""
from __future__ import annotations

from http import HTTPStatus
from flask import Blueprint, current_app, jsonify, request
import requests

bp = Blueprint("patient", __name__, url_prefix="/patient")


def _get_patient_service_url() -> str:
    """Obtiene la URL base del Patient Service."""
    return current_app.config["PATIENT_SERVICE_URL"]


def _get_timeout() -> float:
    """Obtiene el timeout configurado para las peticiones."""
    return current_app.config["GATEWAY_SERVICE_TIMEOUT"]


def _get_auth_headers() -> dict:
    """Extrae y retorna los headers de autenticación del request actual."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {}
    return {"Authorization": auth_header}


def _proxy_get(path: str):
    """
    Proxy genérico para peticiones GET al Patient Service.
    Incluye query params y headers de autenticación.
    """
    try:
        url = f"{_get_patient_service_url()}{path}"
        headers = _get_auth_headers()
        
        response = requests.get(
            url,
            params=request.args,
            headers=headers,
            timeout=_get_timeout()
        )
        
        return jsonify(response.json()), response.status_code
    
    except requests.Timeout:
        return jsonify({
            "error": "service_timeout",
            "message": "El servicio de pacientes no respondió a tiempo"
        }), HTTPStatus.GATEWAY_TIMEOUT
    
    except requests.ConnectionError:
        return jsonify({
            "error": "service_unavailable",
            "message": "El servicio de pacientes no está disponible"
        }), HTTPStatus.SERVICE_UNAVAILABLE
    
    except Exception as e:
        current_app.logger.error(f"Error en proxy patient: {e}")
        return jsonify({
            "error": "proxy_error",
            "message": "Error al comunicarse con el servicio de pacientes"
        }), HTTPStatus.INTERNAL_SERVER_ERROR


# ---------------------------------------------------------------------------
# Endpoints del Patient Service
# ---------------------------------------------------------------------------

@bp.get("/dashboard")
def get_dashboard():
    """Proxy: Obtiene el dashboard completo del paciente."""
    return _proxy_get("/patient/dashboard")


@bp.get("/profile")
def get_profile():
    """Proxy: Obtiene el perfil del paciente."""
    return _proxy_get("/patient/profile")


@bp.get("/alerts")
def get_alerts():
    """
    Proxy: Obtiene alertas del paciente.
    Query params: status, limit, offset
    """
    return _proxy_get("/patient/alerts")


@bp.get("/devices")
def get_devices():
    """Proxy: Obtiene dispositivos asignados al paciente."""
    return _proxy_get("/patient/devices")


@bp.get("/readings")
def get_readings():
    """
    Proxy: Obtiene historial de lecturas del paciente.
    Query params: limit, offset
    """
    return _proxy_get("/patient/readings")


@bp.get("/care-team")
def get_care_team():
    """Proxy: Obtiene el equipo de cuidado del paciente."""
    return _proxy_get("/patient/care-team")


@bp.get("/location/latest")
def get_latest_location():
    """Proxy: Obtiene la última ubicación del paciente."""
    return _proxy_get("/patient/location/latest")


@bp.get("/health")
def health_check():
    """Proxy: Health check del Patient Service."""
    return _proxy_get("/patient/health")
