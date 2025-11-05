"""Push device endpoints for organization administrators."""
from __future__ import annotations

from flask import Blueprint, Request, request

from ..auth import AuthContext, require_org_admin
from .. import db
from ..repositories.push_devices import PushDevicesRepository
from ..request_utils import parse_payload
from ..xml import xml_error_response, xml_response

bp = Blueprint("push_devices", __name__, url_prefix="/admin/organizations/<org_id>/push-devices")
_repo = PushDevicesRepository()


def _auth_context(req: Request) -> AuthContext:
    ctx = getattr(req, "auth_context", None)
    if ctx is None:
        raise RuntimeError("auth context missing")
    return ctx


def _coerce_int(value: str | None, *, default: int, minimum: int, maximum: int | None = None) -> int:
    if value is None or value.strip() == "":
        result = default
    else:
        try:
            result = int(value)
        except ValueError:
            result = default
    if result < minimum:
        result = minimum
    if maximum is not None and result > maximum:
        result = maximum
    return result


def _coerce_bool(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "t", "yes", "y"}:
        return True
    if lowered in {"0", "false", "f", "no", "n"}:
        return False
    return default


def _trim(value: object) -> str | None:
    if value is None:
        return None
    return str(value).strip() or None


def _ensure_member(org_id: str, user_id: str | None):
    if not user_id:
        return None
    query = """
        SELECT 1
        FROM user_org_membership
        WHERE org_id = %(org_id)s AND user_id = %(user_id)s
        LIMIT 1
    """
    result = db.fetch_one(query, {"org_id": org_id, "user_id": user_id})
    if result is None:
        return xml_error_response("forbidden", "User does not belong to this organization", status=403)
    return None


@bp.get("/")
@require_org_admin
def list_push_devices(org_id: str):
    limit = _coerce_int(request.args.get("limit"), default=100, minimum=1, maximum=200)
    offset = _coerce_int(request.args.get("offset"), default=0, minimum=0)
    active_param = request.args.get("active")
    active = None
    if active_param is not None and active_param.strip() != "":
        active = _coerce_bool(active_param, default=True)
    user_id = _trim(request.args.get("user_id"))
    error = _ensure_member(org_id, user_id)
    if error:
        return error
    devices = _repo.list_for_org(org_id, limit=limit, offset=offset, active=active)
    if user_id:
        devices = [item for item in devices if str(item.get("user_id")) == user_id]
    return xml_response({"push_devices": devices})


@bp.patch("/<device_id>")
@require_org_admin
def update_push_device(org_id: str, device_id: str):
    _auth_context(request)
    existing = _repo.get(org_id, device_id)
    if not existing:
        return xml_error_response("not_found", "Push device not found", status=404)
    payload = parse_payload(request)
    raw_active = payload.get("active")
    if raw_active is None and "is_active" in payload:
        raw_active = payload.get("is_active")
    active = _coerce_bool(raw_active, default=bool(existing.get("active")))
    updated = _repo.update_active(device_id, active)
    if not updated:
        return xml_error_response("update_failed", "Push device could not be updated", status=500)
    refreshed = _repo.get(org_id, device_id)
    return xml_response({"push_device": refreshed or updated})


@bp.delete("/<device_id>")
@require_org_admin
def delete_push_device(org_id: str, device_id: str):
    _auth_context(request)
    existing = _repo.get(org_id, device_id)
    if not existing:
        return xml_error_response("not_found", "Push device not found", status=404)
    deleted = _repo.delete(device_id)
    if not deleted:
        return xml_error_response("delete_failed", "Push device could not be deleted", status=500)
    return xml_response({"deleted": True})


@bp.get("/platforms")
@require_org_admin
def list_push_platforms(org_id: str):
    """Return the catalog of push notification platforms."""
    platforms = _repo.list_platforms()
    return xml_response({"platforms": platforms})
