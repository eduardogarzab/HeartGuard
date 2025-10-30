"""Notification service to manage push devices and alert deliveries."""
from __future__ import annotations

import datetime as dt
from typing import Dict, List

from flask import Blueprint, request

from common.auth import require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("notifications", __name__)

PUSH_DEVICES: Dict[str, Dict] = {
    "pd-1": {
        "id": "pd-1",
        "user_id": "usr-2",
        "platform": "ios",
        "token": "ios-token-123",
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
}

ALERT_DELIVERIES: List[Dict] = []


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "notification", "status": "healthy", "devices": len(PUSH_DEVICES)})


@bp.route("/push-devices", methods=["GET"])
@require_auth(optional=True)
def list_devices() -> "Response":
    return render_response({"push_devices": list(PUSH_DEVICES.values())}, meta={"total": len(PUSH_DEVICES)})


@bp.route("/push-devices", methods=["POST"])
@require_auth(optional=True)
def register_device() -> "Response":
    payload, _ = parse_request_data(request)
    user_id = payload.get("user_id")
    token = payload.get("token")
    if not user_id or not token:
        raise APIError("user_id and token are required", status_code=400, error_id="HG-NOTIFY-VALIDATION")
    device_id = f"pd-{len(PUSH_DEVICES) + 1}"
    device = {
        "id": device_id,
        "user_id": user_id,
        "platform": payload.get("platform", "ios"),
        "token": token,
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    PUSH_DEVICES[device_id] = device
    return render_response({"push_device": device}, status_code=201)


@bp.route("/deliveries", methods=["POST"])
@require_auth(optional=True)
def create_delivery() -> "Response":
    payload, _ = parse_request_data(request)
    alert_id = payload.get("alert_id")
    device_id = payload.get("device_id")
    if not alert_id or not device_id:
        raise APIError("alert_id and device_id are required", status_code=400, error_id="HG-NOTIFY-DELIVERY")
    delivery = {
        "id": f"delivery-{len(ALERT_DELIVERIES) + 1}",
        "alert_id": alert_id,
        "device_id": device_id,
        "status": "sent",
        "sent_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    ALERT_DELIVERIES.append(delivery)
    return render_response({"delivery": delivery}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/notifications")
