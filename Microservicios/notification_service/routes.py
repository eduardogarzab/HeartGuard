"""Notification service integrating with push device and alert delivery tables."""
from __future__ import annotations

import datetime as dt
import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import AlertChannel, AlertDelivery, DeliveryStatus, Platform, PushDevice

bp = Blueprint("notifications", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response(
        {
            "service": "notification",
            "status": "healthy",
            "push_devices": PushDevice.query.count(),
            "deliveries": AlertDelivery.query.count(),
        }
    )


@bp.route("/push-devices", methods=["GET"])
@require_auth(optional=True)
def list_devices() -> "Response":
    devices = [
        _serialize_device(device)
        for device in PushDevice.query.order_by(PushDevice.last_seen_at.desc()).limit(200).all()
    ]
    return render_response({"push_devices": devices}, meta={"total": len(devices)})


@bp.route("/push-devices", methods=["POST"])
@require_auth(optional=True)
def register_device() -> "Response":
    payload, _ = parse_request_data(request)
    user_id = payload.get("user_id")
    platform_code = payload.get("platform_code") or payload.get("platform")
    push_token = payload.get("push_token") or payload.get("token")
    if not user_id or not platform_code or not push_token:
        raise APIError(
            "user_id, platform_code y push_token son requeridos",
            status_code=400,
            error_id="HG-NOTIFY-VALIDATION",
        )
    platform = Platform.query.filter_by(code=platform_code).first()
    if not platform:
        raise APIError("platform_code inválido", status_code=400, error_id="HG-NOTIFY-PLATFORM")

    device = PushDevice(
        id=str(uuid.uuid4()),
        user_id=user_id,
        platform_id=platform.id,
        push_token=push_token,
        last_seen_at=dt.datetime.utcnow(),
        active=True,
    )
    db.session.add(device)
    db.session.commit()
    return render_response({"push_device": _serialize_device(device)}, status_code=201)


@bp.route("/deliveries", methods=["POST"])
@require_auth(optional=True)
def create_delivery() -> "Response":
    payload, _ = parse_request_data(request)
    alert_id = payload.get("alert_id")
    channel_code = payload.get("channel_code", "PUSH")
    target = payload.get("target")
    status_code = payload.get("status_code", "SENT")
    if not alert_id or not target:
        raise APIError("alert_id y target son requeridos", status_code=400, error_id="HG-NOTIFY-DELIVERY")

    channel = AlertChannel.query.filter_by(code=channel_code).first()
    if not channel:
        raise APIError("channel_code inválido", status_code=400, error_id="HG-NOTIFY-CHANNEL")

    status = DeliveryStatus.query.filter_by(code=status_code).first()
    if not status:
        raise APIError("status_code inválido", status_code=400, error_id="HG-NOTIFY-STATUS")

    delivery = AlertDelivery(
        id=str(uuid.uuid4()),
        alert_id=alert_id,
        channel_id=channel.id,
        target=target,
        sent_at=dt.datetime.utcnow(),
        delivery_status_id=status.id,
        response_payload=payload.get("response_payload"),
    )
    db.session.add(delivery)
    db.session.commit()
    return render_response({"delivery": _serialize_delivery(delivery)}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/notifications")


def _serialize_device(device: PushDevice) -> dict:
    platform = Platform.query.get(device.platform_id)
    return {
        "id": device.id,
        "user_id": device.user_id,
        "platform_code": platform.code if platform else None,
        "push_token": device.push_token,
        "last_seen_at": device.last_seen_at.isoformat() + "Z",
        "active": device.active,
    }


def _serialize_delivery(delivery: AlertDelivery) -> dict:
    channel = AlertChannel.query.get(delivery.channel_id)
    status = DeliveryStatus.query.get(delivery.delivery_status_id)
    return {
        "id": delivery.id,
        "alert_id": delivery.alert_id,
        "channel_code": channel.code if channel else None,
        "target": delivery.target,
        "status_code": status.code if status else None,
        "sent_at": delivery.sent_at.isoformat() + "Z",
        "response_payload": delivery.response_payload,
    }
