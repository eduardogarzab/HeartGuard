"""Audit service ingesting audit log events."""
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
    return render_response({"service": "audit", "status": "healthy", "events": AuditLog.query.count()})


@bp.route("/logs", methods=["GET"])
@require_auth(optional=True)
def list_logs() -> "Response":
    limit = int(request.args.get("limit", 20))
    logs = [
        _serialize_log(log)
        for log in AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    ]
    return render_response({"logs": logs}, meta={"returned": len(logs)})


@bp.route("/logs", methods=["POST"])
@require_auth(optional=True)
def create_log() -> "Response":
    payload, _ = parse_request_data(request)
    actor = payload.get("actor_id")
    action = payload.get("action")
    if not actor or not action:
        raise APIError("actor_id and action are required", status_code=400, error_id="HG-AUDIT-VALIDATION")
    entry = AuditLog(
        id=f"audit-{uuid.uuid4()}",
        actor_id=actor,
        action=action,
        resource=payload.get("resource"),
        metadata=payload.get("metadata", {}),
        created_at=dt.datetime.utcnow(),
    )
    db.session.add(entry)
    db.session.commit()
    return render_response({"log": _serialize_log(entry)}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/audit")
    with app.app_context():
        _seed_default_log()


def _serialize_log(log: AuditLog) -> dict:
    return {
        "id": log.id,
        "actor_id": log.actor_id,
        "action": log.action,
        "resource": log.resource,
        "metadata": log.metadata or {},
        "created_at": (log.created_at or dt.datetime.utcnow()).isoformat() + "Z",
    }


def _seed_default_log() -> None:
    if AuditLog.query.count() == 0:
        entry = AuditLog(
            id="audit-1",
            actor_id="system",
            action="bootstrap",
            resource="startup",
            metadata={"status": "initialized"},
        )
        db.session.add(entry)
        db.session.commit()
