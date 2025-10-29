from datetime import datetime
from typing import Any, Dict

from flask import abort, g, request
from sqlalchemy.exc import NoResultFound

from ..repository import (
    AlertRepository,
    serialize_alert,
    serialize_delivery,
    serialize_label,
)
from ..utils import (
    AuthError,
    auto_response,
    send_analytics_event,
    send_audit_event,
    token_required,
)
from . import alerts_bp


repository = AlertRepository()


def _parse_iso_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Invalid datetime format. Use ISO 8601.") from exc


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


@alerts_bp.errorhandler(AuthError)
def handle_auth_error(error: AuthError):
    return auto_response({"error": str(error)}, 401)


@alerts_bp.errorhandler(NoResultFound)
def handle_not_found(error: NoResultFound):
    return auto_response({"error": str(error)}, 404)


@alerts_bp.errorhandler(ValueError)
def handle_value_error(error: ValueError):
    return auto_response({"error": str(error)}, 400)


@alerts_bp.route("/alerts", methods=["GET"])
@token_required
def list_alerts():
    filters = {}
    for key in ("patient_id", "status_id", "type_id", "level_id"):
        value = request.args.get(key)
        if value:
            filters[key] = value

    alerts = repository.get_alerts(g.org_id, filters)
    send_analytics_event("alerts.list", {"filters": filters})
    return auto_response({"alerts": [serialize_alert(alert) for alert in alerts]})


@alerts_bp.route("/alerts", methods=["POST"])
@token_required
def create_alert():
    payload = request.get_json() or {}
    required_fields = [
        "patient_id",
        "alert_type_id",
        "alert_level_id",
        "alert_status_id",
        "message",
    ]
    missing = [field for field in required_fields if field not in payload]
    if missing:
        abort(400, description=f"Missing fields: {', '.join(missing)}")

    data: Dict[str, Any] = {
        "patient_id": payload["patient_id"],
        "alert_type_id": payload["alert_type_id"],
        "alert_level_id": payload["alert_level_id"],
        "alert_status_id": payload["alert_status_id"],
        "message": payload["message"],
    }
    if "payload" in payload:
        data["payload"] = payload["payload"]
    if "is_active" in payload:
        data["is_active"] = _parse_bool(payload["is_active"])

    alert = repository.create_alert(g.org_id, data)
    send_audit_event("CREATE_ALERT", {"alert_id": str(alert.id)})
    send_analytics_event("alerts.created", {"alert_id": str(alert.id)})
    return auto_response({"alert": serialize_alert(alert)}, 201)


@alerts_bp.route("/alerts/<alert_id>", methods=["PATCH"])
@token_required
def update_alert(alert_id: str):
    payload = request.get_json() or {}
    allowed = {
        "alert_type_id",
        "alert_level_id",
        "alert_status_id",
        "message",
        "payload",
        "is_active",
    }

    update_data: Dict[str, Any] = {}
    for key in allowed:
        if key in payload:
            update_data[key] = (
                _parse_bool(payload[key]) if key == "is_active" else payload[key]
            )

    if not update_data:
        abort(400, description="No valid fields to update")

    alert = repository.update_alert(alert_id, g.org_id, update_data)
    send_audit_event("UPDATE_ALERT", {"alert_id": str(alert.id)})
    send_analytics_event("alerts.updated", {"alert_id": str(alert.id)})
    return auto_response({"alert": serialize_alert(alert)})


@alerts_bp.route("/alerts/<alert_id>", methods=["DELETE"])
@token_required
def delete_alert(alert_id: str):
    repository.delete_alert(alert_id, g.org_id)
    send_audit_event("DELETE_ALERT", {"alert_id": alert_id})
    send_analytics_event("alerts.deleted", {"alert_id": alert_id})
    return auto_response({"deleted": True})


@alerts_bp.route("/alerts/active-by-patient", methods=["GET"])
@token_required
def active_alerts_by_patient():
    patient_id = request.args.get("patient_id")
    if not patient_id:
        abort(400, description="patient_id query parameter is required")

    alerts = repository.get_active_alerts_by_patient(g.org_id, patient_id)
    send_analytics_event(
        "alerts.active_by_patient", {"patient_id": patient_id, "count": len(alerts)}
    )
    return auto_response({"alerts": [serialize_alert(alert) for alert in alerts]})


@alerts_bp.route("/alerts/<alert_id>/deliveries", methods=["POST"])
@token_required
def create_delivery(alert_id: str):
    payload = request.get_json() or {}
    required_fields = ["delivery_status_id", "channel", "recipient"]
    missing = [field for field in required_fields if field not in payload]
    if missing:
        abort(400, description=f"Missing fields: {', '.join(missing)}")

    data: Dict[str, Any] = {
        "delivery_status_id": payload["delivery_status_id"],
        "channel": payload["channel"],
        "recipient": payload["recipient"],
    }
    if "delivered_at" in payload and payload["delivered_at"]:
        data["delivered_at"] = _parse_iso_datetime(payload["delivered_at"])
    if "payload" in payload:
        data["payload"] = payload["payload"]

    delivery = repository.create_delivery(alert_id, g.org_id, data)
    send_audit_event(
        "CREATE_ALERT_DELIVERY", {"alert_id": alert_id, "delivery_id": str(delivery.id)}
    )
    send_analytics_event(
        "alerts.delivery_created", {"alert_id": alert_id, "delivery_id": str(delivery.id)}
    )
    return auto_response({"delivery": serialize_delivery(delivery)}, 201)


@alerts_bp.route("/labels", methods=["POST"])
@token_required
def create_label():
    payload = request.get_json() or {}
    required_fields = ["alert_id", "label"]
    missing = [field for field in required_fields if field not in payload]
    if missing:
        abort(400, description=f"Missing fields: {', '.join(missing)}")

    data: Dict[str, Any] = {"label": payload["label"]}
    if "notes" in payload:
        data["notes"] = payload["notes"]

    label = repository.create_ground_truth_label(payload["alert_id"], g.org_id, data)
    send_audit_event(
        "CREATE_GROUND_TRUTH_LABEL",
        {"alert_id": payload["alert_id"], "label_id": str(label.id)},
    )
    send_analytics_event(
        "alerts.label_created",
        {"alert_id": payload["alert_id"], "label_id": str(label.id)},
    )
    return auto_response({"label": serialize_label(label)}, 201)
