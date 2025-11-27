"""Endpoint de salud básico."""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify

bp = Blueprint("auth_health", __name__, url_prefix="/health")


@bp.get("/")
def healthcheck():
    return jsonify(
        {
            "status": "ok",
            "service": "heartguard-auth",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "debug": bool(current_app.config.get("DEBUG", False)),
        }
    )
