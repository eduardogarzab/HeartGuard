"""Health endpoint."""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint

from ..xml import xml_response

bp = Blueprint("health", __name__, url_prefix="/health")


@bp.get("/")
def healthcheck():
    payload = {
        "status": "ok",
        "service": "heartguard-admin",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return xml_response(payload, root="health")
