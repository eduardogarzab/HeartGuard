"""models.Alert service handling alert lifecycle operations."""
from __future__ import annotations

import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response
import models
# Models accessed via models. models.Alert

bp = Blueprint("alerts", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "alerts", "status": "healthy"})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_alerts() -> "Response":
    alerts = [a.to_dict() for a in models.Alert.query.all()]
    return render_response({"alerts": alerts}, meta={"total": len(alerts)})


@bp.route("", methods=["POST"])
@require_auth(optional=True)
def create_alert() -> "Response":
    payload, _ = parse_request_data(request)
    patient_id = payload.get("patient_id")
    type_id = payload.get("type_id")
    alert_level_id = payload.get("alert_level_id")
    status_id = payload.get("status_id")

    if not all([patient_id, type_id, alert_level_id, status_id]):
        raise APIError("patient_id, type_id, alert_level_id, and status_id are required",
                         status_code=400, error_id="HG-ALERT-VALIDATION")

    new_alert = models.Alert(patient_id=patient_id, type_id=type_id,
                      alert_level_id=alert_level_id, status_id=status_id,
                      description=payload.get("description"))

    db.session.add(new_alert)
    db.session.commit()

    return render_response({"alert": new_alert.to_dict()}, status_code=201)


@bp.route("/<alert_id>", methods=["GET"])
@require_auth(optional=True)
def get_alert(alert_id: str) -> "Response":
    alert = models.Alert.query.get(alert_id)
    if not alert:
        raise APIError("models.Alert not found", status_code=404, error_id="HG-ALERT-NOT-FOUND")
    return render_response({"alert": alert.to_dict()})


@bp.route("/<alert_id>/assign", methods=["POST"])
@require_auth(required_roles=["clinician", "admin"])
def assign_alert(alert_id: str) -> "Response":
    alert = models.Alert.query.get(alert_id)
    if not alert:
        raise APIError("models.Alert not found", status_code=404, error_id="HG-ALERT-NOT-FOUND")

    # This is a placeholder for the 'assigned' status_id
    alert.status_id = "f4e5a6b0-1e89-4c22-9b2a-1e6b9a7a8d8e"
    db.session.commit()
    return render_response({"alert": alert.to_dict()})


@bp.route("/<alert_id>/ack", methods=["POST"])
@require_auth(optional=True)
def acknowledge_alert(alert_id: str) -> "Response":
    alert = models.Alert.query.get(alert_id)
    if not alert:
        raise APIError("models.Alert not found", status_code=404, error_id="HG-ALERT-NOT-FOUND")

    # This is a placeholder for the 'acknowledged' status_id
    alert.status_id = "a2e5a6b0-1e89-4c22-9b2a-1e6b9a7a8d8e"
    db.session.commit()
    return render_response({"alert": alert.to_dict()})


@bp.route("/<alert_id>/resolve", methods=["POST"])
@require_auth(optional=True)
def resolve_alert(alert_id: str) -> "Response":
    alert = models.Alert.query.get(alert_id)
    if not alert:
        raise APIError("models.Alert not found", status_code=404, error_id="HG-ALERT-NOT-FOUND")

    # This is a placeholder for the 'resolved' status_id
    alert.status_id = "b8e5a6b0-1e89-4c22-9b2a-1e6b9a7a8d8e"
    db.session.commit()
    return render_response({"alert": alert.to_dict()})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/alerts")
