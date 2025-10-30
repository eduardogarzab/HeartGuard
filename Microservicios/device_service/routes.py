"""Device service managing hardware assets and stream bindings."""
from __future__ import annotations

import datetime as dt
import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import Device, DeviceType, SignalStream, TimeseriesBinding

bp = Blueprint("devices", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "device", "status": "healthy", "devices": Device.query.count()})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_devices() -> "Response":
    devices = [
        _serialize_device(device)
        for device in Device.query.order_by(Device.created_at.desc()).all()
    ]
    return render_response({"devices": devices}, meta={"total": len(devices)})


@bp.route("", methods=["POST"])
@require_auth(required_roles=["admin", "clinician"])
def register_device() -> "Response":
    payload, _ = parse_request_data(request)
    serial = payload.get("serial_number")
    if not serial:
        raise APIError("serial_number is required", status_code=400, error_id="HG-DEVICE-VALIDATION")
    device_type_id = payload.get("device_type_id") or _get_default_device_type().id
    device = Device(
        id=f"dev-{uuid.uuid4()}",
        device_type_id=device_type_id,
        serial_number=serial,
        assigned_patient_id=payload.get("assigned_patient_id"),
        status=payload.get("status", "inventory"),
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
    bindings = [_serialize_binding(binding) for stream in device.streams for binding in stream.bindings]
    return render_response({"streams": streams, "bindings": bindings}, meta={"streams": len(streams)})


@bp.route("/streams/bind", methods=["POST"])
@require_auth(required_roles=["admin", "clinician"])
def create_binding() -> "Response":
    payload, _ = parse_request_data(request)
    stream_id = payload.get("stream_id")
    measurement = payload.get("influx_measurement")
    if not stream_id or not measurement:
        raise APIError("stream_id and influx_measurement are required", status_code=400, error_id="HG-DEVICE-BINDING")
    stream = SignalStream.query.get(stream_id)
    if not stream:
        raise APIError("Stream not found", status_code=404, error_id="HG-DEVICE-STREAM-NOT-FOUND")
    binding = TimeseriesBinding(
        id=f"binding-{uuid.uuid4()}",
        stream=stream,
        influx_measurement=measurement,
        bucket=payload.get("bucket", "heartguard-timeseries"),
        org=payload.get("org", "heartguard"),
        created_at=dt.datetime.utcnow(),
    )
    db.session.add(binding)
    db.session.commit()
    return render_response({"binding": _serialize_binding(binding)}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/devices")
    with app.app_context():
        _seed_defaults()


def _get_default_device_type() -> DeviceType:
    device_type = DeviceType.query.first()
    if not device_type:
        device_type = DeviceType(id="dev-type-1", name="HeartGuard Watch", manufacturer="HeartGuard")
        db.session.add(device_type)
        db.session.commit()
    return device_type


def _serialize_device(device: Device) -> dict:
    return {
        "id": device.id,
        "device_type_id": device.device_type_id,
        "serial_number": device.serial_number,
        "assigned_patient_id": device.assigned_patient_id,
        "status": device.status,
        "created_at": (device.created_at or dt.datetime.utcnow()).isoformat() + "Z",
        "updated_at": (device.updated_at or dt.datetime.utcnow()).isoformat() + "Z",
    }


def _serialize_stream(stream: SignalStream) -> dict:
    return {
        "id": stream.id,
        "device_id": stream.device_id,
        "signal_type": stream.signal_type,
        "sampling_rate": stream.sampling_rate,
    }


def _serialize_binding(binding: TimeseriesBinding) -> dict:
    return {
        "id": binding.id,
        "stream_id": binding.stream_id,
        "influx_measurement": binding.influx_measurement,
        "bucket": binding.bucket,
        "org": binding.org,
        "created_at": (binding.created_at or dt.datetime.utcnow()).isoformat() + "Z",
    }


def _seed_defaults() -> None:
    if Device.query.count() > 0:
        return
    device_type = _get_default_device_type()
    device = Device(
        id="dev-1",
        device_type=device_type,
        serial_number="HGW-0001",
        assigned_patient_id="pat-1",
        status="active",
    )
    db.session.add(device)
    stream = SignalStream(id="stream-1", device=device, signal_type="heart_rate", sampling_rate=1)
    db.session.add(stream)
    db.session.add(
        TimeseriesBinding(
            id="binding-1",
            stream=stream,
            influx_measurement="heart_rate",
            bucket="heartguard-timeseries",
            org="heartguard",
            created_at=dt.datetime.utcnow(),
        )
    )
    db.session.commit()
