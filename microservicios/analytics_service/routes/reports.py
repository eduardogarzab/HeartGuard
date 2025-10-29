"""Rutas de reportes para el servicio de analytics."""
from __future__ import annotations

from functools import wraps
from typing import Any, Dict, Optional

from flask import Blueprint, g

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

try:  # pragma: no cover
    from shared_lib.flask.auth import require_auth  # type: ignore
except Exception:  # pragma: no cover
    try:
        from shared_lib.auth import require_auth  # type: ignore
    except Exception:  # pragma: no cover
        def require_auth(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper


reports_bp = Blueprint("reports", __name__, url_prefix="/v1/metrics")


@reports_bp.get("/overview")
@require_auth
def overview_metrics():
    """Devuelve métricas consolidadas para paneles administrativos."""

    role = (getattr(g, "role", "") or "").lower()
    if role not in {"admin", "superadmin"}:
        return create_response({"status": "error", "message": "Forbidden"}, status_code=403)

    org_id = getattr(g, "org_id", None)
    include_all = role == "superadmin"

    if not include_all and org_id is None:
        return create_response({"status": "error", "message": "Organización requerida"}, status_code=400)

    try:
        metrics = repository.get_overview_metrics(org_id=org_id, include_all=include_all)
    except RepositoryError as exc:
        return create_response(
            {
                "status": "error",
                "message": "No fue posible obtener las métricas",
                "details": {"reason": str(exc)},
            },
            status_code=500,
        )

    payload = {
        "status": "ok",
        "data": {
            "metrics": metrics,
            "context": {
                "org_id": org_id,
                "role": role,
                "source": "audit_logs",
            },
        },
    }
    return create_response(payload)


__all__ = ["reports_bp", "overview_metrics"]
