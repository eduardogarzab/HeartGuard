"""Device service managing hardware assets and stream bindings."""
from __future__ import annotations

import datetime as dt
from typing import Dict, List

from flask import Blueprint, request

from common.auth import require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("devices", __name__)

DEVICE_TYPES = {
    "dev-type-1": {"id": "dev-type-1", "name": "HeartGuard Watch", "manufacturer": "HeartGuard"},
}

DEVICES: Dict[str, Dict] = {
    "dev-1": {
        "id": "dev-1",
        "device_type_id": "dev-type-1",
        "serial_number": "HGW-0001",
        "assigned_patient_id": "pat-1",
        "status": "active",
    }
}

SIGNAL_STREAMS: Dict[str, Dict] = {
    "stream-1": {
        "id": "stream-1",
        "device_id": "dev-1",
        "signal_type": "heart_rate",
        "sampling_rate": 1,
    }
}

TIMESERIES_BINDINGS: List[Dict] = [
    {
        "id": "binding-1",
        "stream_id": "stream-1",
        "influx_measurement": "heart_rate",
        "bucket": "heartguard-timeseries",
        "org": "heartguard",
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
]


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "device", "status": "healthy", "devices": len(DEVICES)})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_devices() -> "Response":
    return render_response({"devices": list(DEVICES.values())}, meta={"total": len(DEVICES)})


@bp.route("", methods=["POST"])
@require_auth(required_roles=["admin", "clinician"])
def register_device() -> "Response":
    payload, _ = parse_request_data(request)
    serial = payload.get("serial_number")
    if not serial:
        raise APIError("serial_number is required", status_code=400, error_id="HG-DEVICE-VALIDATION")
    device_id = f"dev-{len(DEVICES) + 1}"
    device = {
        "id": device_id,
        "device_type_id": payload.get("device_type_id", "dev-type-1"),
        "serial_number": serial,
        "assigned_patient_id": payload.get("assigned_patient_id"),
        "status": payload.get("status", "inventory"),
    }
    DEVICES[device_id] = device
    return render_response({"device": device}, status_code=201)


@bp.route("/<device_id>/streams", methods=["GET"])
@require_auth(optional=True)
def list_streams(device_id: str) -> "Response":
    streams = [stream for stream in SIGNAL_STREAMS.values() if stream["device_id"] == device_id]
    bindings = [binding for binding in TIMESERIES_BINDINGS if binding["stream_id"] in {s["id"] for s in streams}]
    return render_response({"streams": streams, "bindings": bindings}, meta={"streams": len(streams)})


@bp.route("/streams/bind", methods=["POST"])
@require_auth(required_roles=["admin", "clinician"])
def create_binding() -> "Response":
    payload, _ = parse_request_data(request)
    stream_id = payload.get("stream_id")
    measurement = payload.get("influx_measurement")
    if not stream_id or not measurement:
        raise APIError("stream_id and influx_measurement are required", status_code=400, error_id="HG-DEVICE-BINDING")
    binding = {
        "id": f"binding-{len(TIMESERIES_BINDINGS) + 1}",
        "stream_id": stream_id,
        "influx_measurement": measurement,
        "bucket": payload.get("bucket", "heartguard-timeseries"),
        "org": payload.get("org", "heartguard"),
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    TIMESERIES_BINDINGS.append(binding)
    return render_response({"binding": binding}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/devices")
