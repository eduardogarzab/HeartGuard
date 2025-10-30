"""Audit service ingesting audit log events."""
from __future__ import annotations

import datetime as dt
from typing import List

from flask import Blueprint, request

from common.auth import require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("audit", __name__)

AUDIT_LOGS: List[dict] = []


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "audit", "status": "healthy", "events": len(AUDIT_LOGS)})


@bp.route("/logs", methods=["GET"])
@require_auth(optional=True)
def list_logs() -> "Response":
    limit = int(request.args.get("limit", 20))
    return render_response({"logs": AUDIT_LOGS[-limit:]}, meta={"returned": min(limit, len(AUDIT_LOGS))})


@bp.route("/logs", methods=["POST"])
@require_auth(optional=True)
def create_log() -> "Response":
    payload, _ = parse_request_data(request)
    actor = payload.get("actor_id")
    action = payload.get("action")
    if not actor or not action:
        raise APIError("actor_id and action are required", status_code=400, error_id="HG-AUDIT-VALIDATION")
    entry = {
        "id": f"audit-{len(AUDIT_LOGS) + 1}",
        "actor_id": actor,
        "action": action,
        "resource": payload.get("resource"),
        "metadata": payload.get("metadata", {}),
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    AUDIT_LOGS.append(entry)
    return render_response({"log": entry}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/audit")
