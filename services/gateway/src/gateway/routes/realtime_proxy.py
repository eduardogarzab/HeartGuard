"""Proxy para rutas del Realtime Data Generator Service."""
from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, Response, current_app, jsonify, request

from ..services.realtime_client import RealtimeClient, RealtimeClientError

bp = Blueprint("realtime", __name__, url_prefix="/realtime")


def _get_realtime_client() -> RealtimeClient:
    """Construye una instancia del cliente que reutiliza la configuración del gateway."""
    return RealtimeClient(
        base_url=current_app.config["REALTIME_SERVICE_URL"],
        timeout=current_app.config["GATEWAY_SERVICE_TIMEOUT"],
    )


def _proxy_request(path: str, method: str = "GET") -> Response:
    """Reenvía la petición actual al Realtime Service y replica su respuesta."""
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
        client = _get_realtime_client()
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

    except RealtimeClientError as exc:
        return jsonify({"error": exc.error, "message": exc.message}), exc.status_code
    except Exception as exc:  # pragma: no cover - log inesperado
        current_app.logger.error(f"Error en proxy realtime: {exc}")
        return (
            jsonify({
                "error": "proxy_error",
                "message": "Error interno del gateway al comunicarse con Realtime Service",
            }),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


# ---------------------------------------------------------------------------
# Endpoints del Realtime Data Generator Service
# ---------------------------------------------------------------------------


@bp.route("/health", methods=["GET"])
def health_check() -> Response:
    """Proxy: Health check del Realtime Service."""
    return _proxy_request("/health", "GET")


@bp.route("/status", methods=["GET"])
def get_status() -> Response:
    """Proxy: Obtiene el estado detallado del servicio de generación."""
    return _proxy_request("/status", "GET")


@bp.route("/patients", methods=["GET"])
def get_patients() -> Response:
    """Proxy: Obtiene la lista de pacientes siendo monitoreados."""
    return _proxy_request("/patients", "GET")
