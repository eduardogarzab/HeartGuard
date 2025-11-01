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


def get_user_roles_from_jwt():
    """Extract user_id and roles from JWT in request context."""
    from flask import g
    user_id = getattr(g, 'user_id', None)
    roles = getattr(g, 'roles', [])
    return user_id, roles


def get_user_organizations(user_id):
    """Get all organization IDs where user is a member."""
    memberships = models.UserOrgMembership.query.filter_by(
        user_id=user_id
    ).filter(
        models.UserOrgMembership.left_at.is_(None)
    ).all()
    return [str(m.org_id) for m in memberships]


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_devices() -> "Response":
    """
    List devices based on user role:
    - superadmin: all devices
    - admin/clinician: devices in their organization(s)
    """
    user_id, roles = get_user_roles_from_jwt()
    
    # Log para debug
    print(f"[DEVICE LIST] user_id={user_id}, roles={roles}")
    
    query = models.Device.query
    
    # Si no hay autenticación, devolver todos (para testing)
    if not user_id:
        print("[DEVICE LIST] No user_id - returning all devices")
        devices = [d.to_dict() for d in query.all()]
        return render_response({"devices": devices}, meta={"total": len(devices)})
    
    # SUPERADMIN: ver todos
    if 'superadmin' in roles:
        print("[DEVICE LIST] User is SUPERADMIN - returning all devices")
        devices = [d.to_dict() for d in query.all()]
        return render_response({"devices": devices}, meta={"total": len(devices)})
    
    # ADMIN/CLINICIAN/CAREGIVER: ver dispositivos de su(s) organización(es)
    if 'admin' in roles or 'clinician' in roles or 'caregiver' in roles:
        org_ids = get_user_organizations(user_id)
        print(f"[DEVICE LIST] User has roles {roles} - org_ids={org_ids}")
        if org_ids:
            # Convertir strings a UUID objects
            org_uuid_list = [uuid.UUID(oid) for oid in org_ids]
            query = query.filter(models.Device.org_id.in_(org_uuid_list))
        else:
            # No pertenece a ninguna org - sin dispositivos
            print("[DEVICE LIST] User has no organization memberships")
            return render_response({"devices": []}, meta={"total": 0})
    
    # Otros roles: sin acceso a dispositivos
    else:
        print(f"[DEVICE LIST] User has no device access role: {roles}")
        return render_response({"devices": []}, meta={"total": 0})
    
    devices = [d.to_dict() for d in query.all()]
    print(f"[DEVICE LIST] Returning {len(devices)} devices")
    return render_response({"devices": devices}, meta={"total": len(devices)})


@bp.route("/count", methods=["POST"])
@require_auth(optional=True)
def count_devices() -> "Response":
    """Count devices with the same role-based filtering as list."""
    user_id, roles = get_user_roles_from_jwt()
    
    query = models.Device.query
    
    # Si no hay autenticación, contar todos
    if not user_id:
        count = query.count()
        return render_response({"count": count})
    
    # SUPERADMIN: contar todos
    if 'superadmin' in roles:
        count = query.count()
        return render_response({"count": count})
    
    # ADMIN/CLINICIAN/CAREGIVER: contar dispositivos de su(s) organización(es)
    if 'admin' in roles or 'clinician' in roles or 'caregiver' in roles:
        org_ids = get_user_organizations(user_id)
        if org_ids:
            org_uuid_list = [uuid.UUID(oid) for oid in org_ids]
            query = query.filter(models.Device.org_id.in_(org_uuid_list))
            count = query.count()
        else:
            count = 0
        return render_response({"count": count})
    
    # Otros roles: sin acceso
    else:
        return render_response({"count": 0})


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
