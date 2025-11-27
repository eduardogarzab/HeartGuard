"""Endpoints de salud y metadatos básicos."""
from __future__ import annotations

from datetime import datetime, timezone
from flask import Blueprint, current_app, jsonify

bp = Blueprint("health", __name__, url_prefix="/health")


@bp.get("/")
def healthcheck():
    """Retorna el estado básico del gateway."""
    return jsonify(
        {
            "status": "ok",
            "service": "heartguard-gateway",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "debug": bool(current_app.config.get("DEBUG", False)),
        }
    )
