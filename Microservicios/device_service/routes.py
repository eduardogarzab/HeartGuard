"""models.Device service managing hardware assets and stream bindings."""
from __future__ import annotations

import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response
import models
# Models accessed via models. models.Device

bp = Blueprint("devices", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "device", "status": "healthy"})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_devices() -> "Response":
    devices = [d.to_dict() for d in models.Device.query.all()]
    return render_response({"devices": devices}, meta={"total": len(devices)})


@bp.route("", methods=["POST"])
@require_auth(required_roles=["admin", "clinician"])
def register_device() -> "Response":
    payload, _ = parse_request_data(request)
    serial = payload.get("serial")
    device_type_id = payload.get("device_type_id")
    if not serial or not device_type_id:
        raise APIError("serial and device_type_id are required", status_code=400, error_id="HG-DEVICE-VALIDATION")

    new_device = models.Device(serial=serial, device_type_id=device_type_id, org_id=payload.get("org_id"))

    db.session.add(new_device)
    db.session.commit()

    return render_response({"device": new_device.to_dict()}, status_code=201)


@bp.route("/<device_id>", methods=["GET"])
@require_auth(optional=True)
def get_device(device_id: str) -> "Response":
    device = models.Device.query.get(device_id)
    if not device:
        raise APIError("models.Device not found", status_code=404, error_id="HG-DEVICE-NOT-FOUND")
    return render_response({"device": device.to_dict()})


@bp.route("/<device_id>/streams", methods=["GET"])
@require_auth(optional=True)
def list_streams(device_id: str) -> "Response":
    # This would query the 'signal_streams' table in a real application.
    return render_response({"streams": [], "bindings": []}, meta={"streams": 0})


@bp.route("/streams/bind", methods=["POST"])
@require_auth(required_roles=["admin", "clinician"])
def create_binding() -> "Response":
    # This would create a new entry in the 'timeseries_binding' table.
    payload, _ = parse_request_data(request)
    stream_id = payload.get("stream_id")
    if not stream_id:
        raise APIError("stream_id is required", status_code=400, error_id="HG-DEVICE-BINDING")

    # Placeholder for the new binding
    new_binding = {"id": str(uuid.uuid4()), "stream_id": stream_id}

    return render_response({"binding": new_binding}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/devices")
