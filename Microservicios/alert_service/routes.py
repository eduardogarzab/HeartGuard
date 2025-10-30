"""Alert service wired to the backend PostgreSQL schema."""
from __future__ import annotations

import datetime as dt
import uuid

from flask import Blueprint, g, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import Alert, AlertAck, AlertAssignment, AlertLevel, AlertResolution, AlertStatus, AlertType

bp = Blueprint("alerts", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response(
        {
            "service": "alerts",
            "status": "healthy",
            "alerts": Alert.query.count(),
        }
    )


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_alerts() -> "Response":
    alerts = [
        _serialize_alert(alert)
        for alert in Alert.query.order_by(Alert.created_at.desc()).limit(200).all()
    ]
    return render_response({"alerts": alerts}, meta={"total": len(alerts)})


@bp.route("", methods=["POST"])
@require_auth(required_roles=["clinician", "superadmin"])
def create_alert() -> "Response":
    payload, _ = parse_request_data(request)
    patient_id = payload.get("patient_id")
    if not patient_id:
        raise APIError("patient_id is required", status_code=400, error_id="HG-ALERT-PATIENT")

    type_code = payload.get("alert_type_code")
    level_code = payload.get("level_code")
    status_code = payload.get("status_code", "created")

    alert_type = AlertType.query.filter_by(code=type_code).first()
    if not alert_type:
        raise APIError("alert_type_code is invalid", status_code=400, error_id="HG-ALERT-TYPE")

    level = AlertLevel.query.filter_by(code=level_code).first()
    if not level:
        raise APIError("level_code is invalid", status_code=400, error_id="HG-ALERT-LEVEL")

    status = AlertStatus.query.filter_by(code=status_code).first()
    if not status:
        raise APIError("status_code is invalid", status_code=400, error_id="HG-ALERT-STATUS")

    alert = Alert(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        type_id=alert_type.id,
        alert_level_id=level.id,
        status_id=status.id,
        description=payload.get("description"),
        created_at=dt.datetime.utcnow(),
    )
    db.session.add(alert)
    db.session.commit()
    return render_response({"alert": _serialize_alert(alert)}, status_code=201)


@bp.route("/<alert_id>/assign", methods=["POST"])
@require_auth(required_roles=["clinician", "superadmin"])
def assign_alert(alert_id: str) -> "Response":
    payload, _ = parse_request_data(request)
    assignee = payload.get("assignee_id")
    if not assignee:
        raise APIError("assignee_id is required", status_code=400, error_id="HG-ALERT-ASSIGNEE")
    alert = Alert.query.get(alert_id)
    if not alert:
        raise APIError("Alert not found", status_code=404, error_id="HG-ALERT-NOT-FOUND")

    assignment = AlertAssignment(
        alert_id=alert.id,
        assignee_user_id=assignee,
        assigned_by_user_id=g.current_user.get("sub") if getattr(g, "current_user", None) else None,
        assigned_at=dt.datetime.utcnow(),
    )
    db.session.add(assignment)
    db.session.commit()
    return render_response({"assignment": _serialize_assignment(assignment)})


@bp.route("/<alert_id>/ack", methods=["POST"])
@require_auth(optional=True)
def acknowledge_alert(alert_id: str) -> "Response":
    alert = Alert.query.get(alert_id)
    if not alert:
        raise APIError("Alert not found", status_code=404, error_id="HG-ALERT-NOT-FOUND")
    payload, _ = parse_request_data(request)
    status = AlertStatus.query.filter_by(code="ack").first()
    if status:
        alert.status_id = status.id
    acknowledgement = AlertAck(
        id=str(uuid.uuid4()),
        alert_id=alert.id,
        ack_by_user_id=payload.get("acknowledged_by") or g.current_user.get("sub") if getattr(g, "current_user", None) else None,
        ack_at=dt.datetime.utcnow(),
        note=payload.get("notes"),
    )
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
    status = AlertStatus.query.filter_by(code="resolved").first()
    if status:
        alert.status_id = status.id
    resolution = AlertResolution(
        id=str(uuid.uuid4()),
        alert_id=alert.id,
        resolved_by_user_id=payload.get("resolved_by") or g.current_user.get("sub") if getattr(g, "current_user", None) else None,
        resolved_at=dt.datetime.utcnow(),
        outcome=payload.get("outcome"),
        note=payload.get("note"),
    )
    db.session.add(resolution)
    db.session.commit()
    return render_response({"resolution": _serialize_resolution(resolution), "alert": _serialize_alert(alert)})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/alerts")


def _serialize_alert(alert: Alert) -> dict:
    level = alert.level.code if alert.level else None
    status = alert.status.code if alert.status else None
    alert_type = alert.alert_type.code if alert.alert_type else None
    return {
        "id": alert.id,
        "patient_id": alert.patient_id,
        "alert_type_code": alert_type,
        "level_code": level,
        "status_code": status,
        "description": alert.description,
        "created_at": alert.created_at.isoformat() + "Z" if alert.created_at else None,
    }


def _serialize_assignment(assignment: AlertAssignment) -> dict:
    return {
        "alert_id": assignment.alert_id,
        "assignee_user_id": assignment.assignee_user_id,
        "assigned_by_user_id": assignment.assigned_by_user_id,
        "assigned_at": assignment.assigned_at.isoformat() + "Z",
    }


def _serialize_ack(ack: AlertAck) -> dict:
    return {
        "id": ack.id,
        "alert_id": ack.alert_id,
        "ack_by_user_id": ack.ack_by_user_id,
        "ack_at": ack.ack_at.isoformat() + "Z",
        "note": ack.note,
    }


def _serialize_resolution(resolution: AlertResolution) -> dict:
    return {
        "id": resolution.id,
        "alert_id": resolution.alert_id,
        "resolved_by_user_id": resolution.resolved_by_user_id,
        "resolved_at": resolution.resolved_at.isoformat() + "Z",
        "outcome": resolution.outcome,
        "note": resolution.note,
    }
