"""Proxy para rutas del Patient Service."""
from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, Response, current_app, jsonify, request

from ..services.patient_client import PatientClient, PatientClientError

bp = Blueprint("patient", __name__, url_prefix="/patient")


def _get_patient_client() -> PatientClient:
    """Construye una instancia de paciente que reutiliza la configuración del gateway."""
    return PatientClient(
        base_url=current_app.config["PATIENT_SERVICE_URL"],
        timeout=current_app.config["GATEWAY_SERVICE_TIMEOUT"],
    )


def _proxy_request(path: str, method: str = "GET") -> Response:
    """Reenvía la petición actual al Patient Service y replica su respuesta."""
    headers: dict[str, str] = {}
    if "Authorization" in request.headers:
        headers["Authorization"] = request.headers["Authorization"]
    if "Content-Type" in request.headers:
        headers["Content-Type"] = request.headers["Content-Type"]

    json_payload = None
    raw_payload = None
    if method in {"POST", "PATCH", "PUT"}:
        if request.is_json:
            json_payload = request.get_json(silent=True)
        if json_payload is None and request.data:
            raw_payload = request.get_data()

    params = request.args.to_dict(flat=False) if request.args else None

    try:
        client = _get_patient_client()
        upstream_response = client.proxy_request(
            method=method,
            path=path,
            headers=headers or None,
            json=json_payload,
            data=raw_payload,
            params=params,
        )

        excluded = {"content-length", "transfer-encoding", "connection"}
        response_headers = [
            (name, value)
            for name, value in upstream_response.headers.items()
            if name.lower() not in excluded
        ]

        return Response(
            response=upstream_response.content,
            status=upstream_response.status_code,
            headers=response_headers,
        )

    except PatientClientError as exc:
        return jsonify({"error": exc.error, "message": exc.message}), exc.status_code
    except Exception as exc:  # pragma: no cover - log inesperado
        current_app.logger.error(f"Error en proxy patient: {exc}")
        return (
            jsonify({
                "error": "proxy_error",
                "message": "Error interno del gateway al comunicarse con Patient Service",
            }),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


# ---------------------------------------------------------------------------
# Endpoints del Patient Service
# ---------------------------------------------------------------------------


@bp.route("/dashboard", methods=["GET"])
def get_dashboard() -> Response:
    """Proxy: Obtiene el dashboard completo del paciente."""
    return _proxy_request("/patient/dashboard", "GET")


@bp.route("/profile", methods=["GET"])
def get_profile() -> Response:
    """Proxy: Obtiene el perfil del paciente."""
    return _proxy_request("/patient/profile", "GET")


@bp.route("/alerts", methods=["GET"])
def get_alerts() -> Response:
    """Proxy: Obtiene alertas del paciente (status, limit, offset)."""
    return _proxy_request("/patient/alerts", "GET")


@bp.route("/devices", methods=["GET"])
def get_devices() -> Response:
    """Proxy: Obtiene dispositivos asignados al paciente."""
    return _proxy_request("/patient/devices", "GET")


@bp.route("/caregivers", methods=["GET"])
def get_caregivers() -> Response:
    """Proxy: Obtiene cuidadores del paciente."""
    return _proxy_request("/patient/caregivers", "GET")


@bp.route("/readings", methods=["GET"])
def get_readings() -> Response:
    """Proxy: Obtiene historial de lecturas (limit, offset)."""
    return _proxy_request("/patient/readings", "GET")


@bp.route("/care-team", methods=["GET"])
def get_care_team() -> Response:
    """Proxy: Obtiene el equipo de cuidado del paciente."""
    return _proxy_request("/patient/care-team", "GET")


@bp.route("/location/latest", methods=["GET"])
def get_latest_location() -> Response:
    """Proxy: Obtiene la última ubicación registrada del paciente."""
    return _proxy_request("/patient/location/latest", "GET")


@bp.route("/locations", methods=["GET"])
def get_locations() -> Response:
    """Proxy: Obtiene el historial de ubicaciones del paciente."""
    return _proxy_request("/patient/locations", "GET")


@bp.route("/health", methods=["GET"])
def health_check() -> Response:
    """Proxy: Health check del Patient Service."""
    return _proxy_request("/patient/health", "GET")
