"""Device service aligned with the backend device schema."""
from __future__ import annotations

import datetime as dt
import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import Device, DeviceType, SignalStream, SignalType, TimeseriesBinding

bp = Blueprint("devices", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response(
        {
            "service": "device",
            "status": "healthy",
            "devices": Device.query.count(),
        }
    )


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_devices() -> "Response":
    devices = [
        _serialize_device(device)
        for device in Device.query.order_by(Device.registered_at.desc()).limit(200).all()
    ]
    return render_response({"devices": devices}, meta={"total": len(devices)})


@bp.route("", methods=["POST"])
@require_auth(required_roles=["clinician", "superadmin"])
def register_device() -> "Response":
    payload, _ = parse_request_data(request)
    serial = payload.get("serial") or payload.get("serial_number")
    device_type_code = payload.get("device_type_code")
    if not serial or not device_type_code:
        raise APIError("serial y device_type_code son requeridos", status_code=400, error_id="HG-DEVICE-VALIDATION")
    if Device.query.filter_by(serial=serial).first():
        raise APIError("serial ya existe", status_code=409, error_id="HG-DEVICE-DUPLICATE")

    device_type = DeviceType.query.filter_by(code=device_type_code).first()
    if not device_type:
        raise APIError("device_type_code inválido", status_code=400, error_id="HG-DEVICE-TYPE")

    device = Device(
        id=str(uuid.uuid4()),
        serial=serial,
        device_type_id=device_type.id,
        org_id=payload.get("org_id"),
        owner_patient_id=payload.get("owner_patient_id"),
        brand=payload.get("brand"),
        model=payload.get("model"),
        registered_at=dt.datetime.utcnow(),
        active=payload.get("active", True),
    )
    db.session.add(device)
    db.session.commit()
    return render_response({"device": _serialize_device(device)}, status_code=201)


@bp.route("/<device_id>/streams", methods=["GET"])
@require_auth(optional=True)
def list_streams(device_id: str) -> "Response":
    device = Device.query.get(device_id)
    if not device:
        raise APIError("Device not found", status_code=404, error_id="HG-DEVICE-NOT-FOUND")
    streams = [_serialize_stream(stream) for stream in device.streams]
    bindings = [
        _serialize_binding(binding)
        for stream in device.streams
        for binding in stream.bindings
    ]
    return render_response({"streams": streams, "bindings": bindings}, meta={"streams": len(streams)})


@bp.route("/streams/bind", methods=["POST"])
@require_auth(required_roles=["clinician", "superadmin"])
def create_binding() -> "Response":
    payload, _ = parse_request_data(request)
    stream_id = payload.get("stream_id")
    measurement = payload.get("measurement") or payload.get("influx_measurement")
    bucket = payload.get("bucket") or payload.get("influx_bucket")
    if not stream_id or not measurement or not bucket:
        raise APIError("stream_id, measurement y bucket son requeridos", status_code=400, error_id="HG-DEVICE-BINDING")
    stream = SignalStream.query.get(stream_id)
    if not stream:
        raise APIError("Stream not found", status_code=404, error_id="HG-DEVICE-STREAM-NOT-FOUND")

    binding = TimeseriesBinding(
        id=str(uuid.uuid4()),
        stream_id=stream.id,
        influx_org=payload.get("org", "heartguard"),
        influx_bucket=bucket,
        measurement=measurement,
        retention_hint=payload.get("retention_hint"),
        created_at=dt.datetime.utcnow(),
    )
    db.session.add(binding)
    db.session.commit()
    return render_response({"binding": _serialize_binding(binding)}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/devices")


def _serialize_device(device: Device) -> dict:
    device_type = DeviceType.query.get(device.device_type_id)
    return {
        "id": device.id,
        "serial": device.serial,
        "device_type_code": device_type.code if device_type else None,
        "org_id": device.org_id,
        "owner_patient_id": device.owner_patient_id,
        "brand": device.brand,
        "model": device.model,
        "registered_at": device.registered_at.isoformat() + "Z" if device.registered_at else None,
        "active": device.active,
    }


def _serialize_stream(stream: SignalStream) -> dict:
    signal_type = SignalType.query.get(stream.signal_type_id)
    return {
        "id": stream.id,
        "device_id": stream.device_id,
        "patient_id": stream.patient_id,
        "signal_type_code": signal_type.code if signal_type else None,
        "sample_rate_hz": float(stream.sample_rate_hz) if stream.sample_rate_hz is not None else None,
        "started_at": stream.started_at.isoformat() + "Z" if stream.started_at else None,
        "ended_at": stream.ended_at.isoformat() + "Z" if stream.ended_at else None,
    }


def _serialize_binding(binding: TimeseriesBinding) -> dict:
    return {
        "id": binding.id,
        "stream_id": binding.stream_id,
        "influx_org": binding.influx_org,
        "influx_bucket": binding.influx_bucket,
        "measurement": binding.measurement,
        "created_at": binding.created_at.isoformat() + "Z" if binding.created_at else None,
    }
