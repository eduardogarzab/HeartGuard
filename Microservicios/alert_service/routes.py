"""Alert service handling alert lifecycle operations."""
from __future__ import annotations

import datetime as dt
from typing import Dict, List

from flask import Blueprint, request

from common.auth import require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("alerts", __name__)

ALERTS: Dict[str, Dict] = {
    "alert-1": {
        "id": "alert-1",
        "patient_id": "pat-1",
        "status": "new",
        "severity": "high",
        "event_type": "tachycardia",
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
}

ALERT_ASSIGNMENTS: List[Dict] = []
ALERT_ACKS: List[Dict] = []
ALERT_RESOLUTIONS: List[Dict] = []


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "alerts", "status": "healthy", "alerts": len(ALERTS)})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_alerts() -> "Response":
    return render_response({"alerts": list(ALERTS.values())}, meta={"total": len(ALERTS)})


@bp.route("", methods=["POST"])
@require_auth(optional=True)
def create_alert() -> "Response":
    payload, _ = parse_request_data(request)
    patient_id = payload.get("patient_id")
    if not patient_id:
        raise APIError("patient_id is required", status_code=400, error_id="HG-ALERT-VALIDATION")
    alert_id = f"alert-{len(ALERTS) + 1}"
    alert = {
        "id": alert_id,
        "patient_id": patient_id,
        "status": "new",
        "severity": payload.get("severity", "medium"),
        "event_type": payload.get("event_type"),
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    ALERTS[alert_id] = alert
    return render_response({"alert": alert}, status_code=201)


@bp.route("/<alert_id>/assign", methods=["POST"])
@require_auth(required_roles=["clinician", "admin"])
def assign_alert(alert_id: str) -> "Response":
    payload, _ = parse_request_data(request)
    assignee = payload.get("assignee_id")
    if alert_id not in ALERTS:
        raise APIError("Alert not found", status_code=404, error_id="HG-ALERT-NOT-FOUND")
    if not assignee:
        raise APIError("assignee_id is required", status_code=400, error_id="HG-ALERT-ASSIGN")
    assignment = {
        "alert_id": alert_id,
        "assignee_id": assignee,
        "assigned_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    ALERT_ASSIGNMENTS.append(assignment)
    ALERTS[alert_id]["status"] = "assigned"
    return render_response({"assignment": assignment, "alert": ALERTS[alert_id]})


@bp.route("/<alert_id>/ack", methods=["POST"])
@require_auth(optional=True)
def acknowledge_alert(alert_id: str) -> "Response":
    if alert_id not in ALERTS:
        raise APIError("Alert not found", status_code=404, error_id="HG-ALERT-NOT-FOUND")
    payload, _ = parse_request_data(request)
    ack = {
        "alert_id": alert_id,
        "acknowledged_by": payload.get("acknowledged_by"),
        "acknowledged_at": dt.datetime.utcnow().isoformat() + "Z",
        "notes": payload.get("notes"),
    }
    ALERT_ACKS.append(ack)
    ALERTS[alert_id]["status"] = "acknowledged"
    return render_response({"ack": ack, "alert": ALERTS[alert_id]})


@bp.route("/<alert_id>/resolve", methods=["POST"])
@require_auth(optional=True)
def resolve_alert(alert_id: str) -> "Response":
    if alert_id not in ALERTS:
        raise APIError("Alert not found", status_code=404, error_id="HG-ALERT-NOT-FOUND")
    payload, _ = parse_request_data(request)
    resolution = {
        "alert_id": alert_id,
        "resolved_by": payload.get("resolved_by"),
        "resolution_reason": payload.get("reason", "resolved"),
        "resolved_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    ALERT_RESOLUTIONS.append(resolution)
    ALERTS[alert_id]["status"] = "resolved"
    return render_response({"resolution": resolution, "alert": ALERTS[alert_id]})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/alerts")
