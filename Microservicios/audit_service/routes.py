"""Audit service exposing records stored in the shared audit_logs table."""
from __future__ import annotations

import datetime as dt
import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import AuditLog

bp = Blueprint("audit", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response(
        {
            "service": "audit",
            "status": "healthy",
            "events": AuditLog.query.count(),
        }
    )


@bp.route("/logs", methods=["GET"])
@require_auth(optional=True)
def list_logs() -> "Response":
    limit = min(int(request.args.get("limit", 50)), 200)
    logs = [
        _serialize_log(log)
        for log in AuditLog.query.order_by(AuditLog.ts.desc()).limit(limit).all()
    ]
    return render_response({"logs": logs}, meta={"returned": len(logs)})


@bp.route("/logs", methods=["POST"])
@require_auth(optional=True)
def create_log() -> "Response":
    payload, _ = parse_request_data(request)
    user_id = payload.get("user_id")
    action = payload.get("action")
    if not action:
        raise APIError("action es requerido", status_code=400, error_id="HG-AUDIT-ACTION")

    entry = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action=action,
        entity=payload.get("entity"),
        entity_id=payload.get("entity_id"),
        ts=payload.get("timestamp") or dt.datetime.utcnow(),
        ip=payload.get("ip"),
        details=payload.get("details"),
    )
    db.session.add(entry)
    db.session.commit()
    return render_response({"log": _serialize_log(entry)}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/audit")


def _serialize_log(log: AuditLog) -> dict:
    return {
        "id": log.id,
        "user_id": log.user_id,
        "action": log.action,
        "entity": log.entity,
        "entity_id": log.entity_id,
        "timestamp": log.ts.isoformat() + "Z" if log.ts else None,
        "ip": log.ip,
        "details": log.details,
    }
