"""Notification service to manage push devices and alert deliveries."""
from __future__ import annotations

import datetime as dt
import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import AlertDelivery, PushDevice

bp = Blueprint("notifications", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "notification", "status": "healthy", "devices": PushDevice.query.count()})


@bp.route("/push-devices", methods=["GET"])
@require_auth(optional=True)
def list_devices() -> "Response":
    devices = [
        _serialize_device(device)
        for device in PushDevice.query.order_by(PushDevice.created_at.desc()).all()
    ]
    return render_response({"push_devices": devices}, meta={"total": len(devices)})


@bp.route("/push-devices", methods=["POST"])
@require_auth(optional=True)
def register_device() -> "Response":
    payload, _ = parse_request_data(request)
    user_id = payload.get("user_id")
    token = payload.get("token")
    if not user_id or not token:
        raise APIError("user_id and token are required", status_code=400, error_id="HG-NOTIFY-VALIDATION")
    device = PushDevice(
        id=f"pd-{uuid.uuid4()}",
        user_id=user_id,
        platform=payload.get("platform", "ios"),
        token=token,
        created_at=dt.datetime.utcnow(),
    )
    db.session.add(device)
    db.session.commit()
    return render_response({"push_device": _serialize_device(device)}, status_code=201)


@bp.route("/deliveries", methods=["POST"])
@require_auth(optional=True)
def create_delivery() -> "Response":
    payload, _ = parse_request_data(request)
    alert_id = payload.get("alert_id")
    device_id = payload.get("device_id")
    if not alert_id or not device_id:
        raise APIError("alert_id and device_id are required", status_code=400, error_id="HG-NOTIFY-DELIVERY")
    device = PushDevice.query.get(device_id)
    if not device:
        raise APIError("Device not found", status_code=404, error_id="HG-NOTIFY-DEVICE-NOT-FOUND")
    delivery = AlertDelivery(
        id=f"delivery-{uuid.uuid4()}",
        alert_id=alert_id,
        device=device,
        status="sent",
        sent_at=dt.datetime.utcnow(),
    )
    db.session.add(delivery)
    db.session.commit()
    return render_response({"delivery": _serialize_delivery(delivery)}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/notifications")
    with app.app_context():
        _seed_defaults()


def _serialize_device(device: PushDevice) -> dict:
    return {
        "id": device.id,
        "user_id": device.user_id,
        "platform": device.platform,
        "token": device.token,
        "created_at": (device.created_at or dt.datetime.utcnow()).isoformat() + "Z",
    }


def _serialize_delivery(delivery: AlertDelivery) -> dict:
    return {
        "id": delivery.id,
        "alert_id": delivery.alert_id,
        "device_id": delivery.device_id,
        "status": delivery.status,
        "sent_at": delivery.sent_at.isoformat() + "Z",
    }


def _seed_defaults() -> None:
    if PushDevice.query.count() == 0:
        device = PushDevice(
            id="pd-1",
            user_id="usr-2",
            platform="ios",
            token="ios-token-123",
        )
        db.session.add(device)
        db.session.commit()
