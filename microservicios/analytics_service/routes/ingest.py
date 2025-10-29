"""Endpoints for ingesting analytics signals."""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, request

from repository import log_heartbeat
from utils import create_response, require_internal_api_key

bp = Blueprint("analytics_ingest", __name__, url_prefix="/v1/metrics")


def _validate_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    service_name = (payload.get("service_name") or "").strip()
    if not service_name:
        raise ValueError("'service_name' is required")

    status = (payload.get("status") or "ok").strip() or "ok"
    metadata = payload.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("'metadata' must be an object if provided")

    return {
        "service_name": service_name,
        "status": status,
        "metadata": metadata or {},
    }


@bp.post("/heartbeat")
@require_internal_api_key
def heartbeat():
    """Register a heartbeat event emitted by an internal service."""

    payload = request.get_json(silent=True) or {}
    try:
        data = _validate_payload(payload)
    except ValueError as exc:
        return create_response(message=str(exc), status_code=400)

    record = log_heartbeat(**data)
    return create_response(data=record, status_code=202)

