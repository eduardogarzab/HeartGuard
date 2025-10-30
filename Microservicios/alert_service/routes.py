"""Alert service handling alert lifecycle operations."""
from __future__ import annotations

import datetime as dt
import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import Alert, AlertAcknowledgement, AlertAssignment, AlertResolution

bp = Blueprint("alerts", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "alerts", "status": "healthy", "alerts": Alert.query.count()})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_alerts() -> "Response":
    alerts = [
        _serialize_alert(alert)
        for alert in Alert.query.order_by(Alert.created_at.desc()).all()
    ]
    return render_response({"alerts": alerts}, meta={"total": len(alerts)})


@bp.route("", methods=["POST"])
@require_auth(optional=True)
def create_alert() -> "Response":
    payload, _ = parse_request_data(request)
    patient_id = payload.get("patient_id")
    if not patient_id:
        raise APIError("patient_id is required", status_code=400, error_id="HG-ALERT-VALIDATION")
    alert = Alert(
        id=f"alert-{uuid.uuid4()}",
        patient_id=patient_id,
        status="new",
        severity=payload.get("severity", "medium"),
        event_type=payload.get("event_type"),
        created_at=dt.datetime.utcnow(),
    )
    db.session.add(alert)
    db.session.commit()
    return render_response({"alert": _serialize_alert(alert)}, status_code=201)


@bp.route("/<alert_id>/assign", methods=["POST"])
@require_auth(required_roles=["clinician", "admin"])
def assign_alert(alert_id: str) -> "Response":
    payload, _ = parse_request_data(request)
    assignee = payload.get("assignee_id")
    alert = Alert.query.get(alert_id)
    if not alert:
        raise APIError("Alert not found", status_code=404, error_id="HG-ALERT-NOT-FOUND")
    if not assignee:
        raise APIError("assignee_id is required", status_code=400, error_id="HG-ALERT-ASSIGN")
    assignment = AlertAssignment(
        id=f"assign-{uuid.uuid4()}",
        alert=alert,
        assignee_id=assignee,
        assigned_at=dt.datetime.utcnow(),
    )
    alert.status = "assigned"
    db.session.add(assignment)
    db.session.commit()
    return render_response({"assignment": _serialize_assignment(assignment), "alert": _serialize_alert(alert)})


@bp.route("/<alert_id>/ack", methods=["POST"])
@require_auth(optional=True)
def acknowledge_alert(alert_id: str) -> "Response":
    alert = Alert.query.get(alert_id)
    if not alert:
        raise APIError("Alert not found", status_code=404, error_id="HG-ALERT-NOT-FOUND")
    payload, _ = parse_request_data(request)
    acknowledgement = AlertAcknowledgement(
        id=f"ack-{uuid.uuid4()}",
        alert=alert,
        acknowledged_by=payload.get("acknowledged_by"),
        acknowledged_at=dt.datetime.utcnow(),
        notes=payload.get("notes"),
    )
    alert.status = "acknowledged"
    db.session.add(acknowledgement)
    db.session.commit()
    return render_response({"ack": _serialize_ack(acknowledgement), "alert": _serialize_alert(alert)})


@bp.route("/<alert_id>/resolve", methods=["POST"])
@require_auth(optional=True)
def resolve_alert(alert_id: str) -> "Response":
    alert = Alert.query.get(alert_id)
    if not alert:
        raise APIError("Alert not found", status_code=404, error_id="HG-ALERT-NOT-FOUND")
    payload, _ = parse_request_data(request)
    resolution = AlertResolution(
        id=f"res-{uuid.uuid4()}",
        alert=alert,
        resolved_by=payload.get("resolved_by"),
        resolution_reason=payload.get("reason", "resolved"),
        resolved_at=dt.datetime.utcnow(),
    )
    alert.status = "resolved"
    db.session.add(resolution)
    db.session.commit()
    return render_response({"resolution": _serialize_resolution(resolution), "alert": _serialize_alert(alert)})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/alerts")
    with app.app_context():
        _seed_defaults()


def _serialize_alert(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "patient_id": alert.patient_id,
        "status": alert.status,
        "severity": alert.severity,
        "event_type": alert.event_type,
        "created_at": (alert.created_at or dt.datetime.utcnow()).isoformat() + "Z",
        "updated_at": (alert.updated_at or dt.datetime.utcnow()).isoformat() + "Z",
    }


def _serialize_assignment(assignment: AlertAssignment) -> dict:
    return {
        "id": assignment.id,
        "alert_id": assignment.alert_id,
        "assignee_id": assignment.assignee_id,
        "assigned_at": assignment.assigned_at.isoformat() + "Z",
    }


def _serialize_ack(ack: AlertAcknowledgement) -> dict:
    return {
        "id": ack.id,
        "alert_id": ack.alert_id,
        "acknowledged_by": ack.acknowledged_by,
        "acknowledged_at": ack.acknowledged_at.isoformat() + "Z",
        "notes": ack.notes,
    }


def _serialize_resolution(resolution: AlertResolution) -> dict:
    return {
        "id": resolution.id,
        "alert_id": resolution.alert_id,
        "resolved_by": resolution.resolved_by,
        "resolution_reason": resolution.resolution_reason,
        "resolved_at": resolution.resolved_at.isoformat() + "Z",
    }


def _seed_defaults() -> None:
    if Alert.query.count() == 0:
        alert = Alert(
            id="alert-1",
            patient_id="pat-1",
            status="new",
            severity="high",
            event_type="tachycardia",
        )
        db.session.add(alert)
        db.session.commit()
