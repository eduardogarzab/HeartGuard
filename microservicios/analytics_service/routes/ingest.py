"""Endpoints de ingesta para el servicio de analytics."""
from __future__ import annotations

from functools import wraps
from typing import Any, Dict, Optional

from flask import Blueprint, current_app, request

from config import settings
import repository
from repository import RepositoryError

try:  # pragma: no cover - dependencia compartida
    from shared_lib.flask.responses import create_response  # type: ignore
except Exception:  # pragma: no cover
    try:
        from shared_lib.responses import create_response  # type: ignore
    except Exception:  # pragma: no cover
        from flask import jsonify

        def create_response(
            payload: Dict[str, Any],
            status_code: int = 200,
            headers: Optional[Dict[str, Any]] = None,
        ):
            response = jsonify(payload)
            response.status_code = status_code
            if headers:
                for key, value in headers.items():
                    response.headers[key] = value
            return response


def _require_internal_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        expected = settings.INGEST_API_KEY
        provided = request.headers.get("X-Internal-Key") or request.headers.get("X-Api-Key")
        if not expected:
            current_app.logger.warning("INGEST_API_KEY no configurada; rechazando petición")
            return create_response(
                {"status": "error", "message": "Servicio no configurado"}, status_code=503
            )
        if not provided or provided != expected:
            return create_response({"status": "error", "message": "Unauthorized"}, status_code=401)
        return func(*args, **kwargs)

    return wrapper


ingest_bp = Blueprint("ingest", __name__, url_prefix="/v1/metrics")


@ingest_bp.post("/heartbeat")
@_require_internal_key
def ingest_heartbeat():
    """Recibe ``heartbeats`` internos de otros servicios."""

    payload = request.get_json(silent=True) or {}
    service_name = (payload.get("service_name") or "").strip()
    status = (payload.get("status") or "").strip().lower()
    details = payload.get("details") or payload.get("metadata") or {}

    if not service_name:
        return create_response({"status": "error", "message": "service_name requerido"}, status_code=400)

    if status not in {"ok", "degraded", "error"}:
        return create_response({"status": "error", "message": "status inválido"}, status_code=400)

    if not isinstance(details, dict):
        return create_response({"status": "error", "message": "details debe ser un objeto"}, status_code=400)

    try:
        repository.log_heartbeat(service_name, status, details=details)
    except RepositoryError as exc:
        return create_response(
            {
                "status": "error",
                "message": "No se pudo registrar el heartbeat",
                "details": {"reason": str(exc)},
            },
            status_code=500,
        )

    return create_response({"status": "ok", "message": "heartbeat registrado"}, status_code=200)


__all__ = ["ingest_bp", "ingest_heartbeat"]
