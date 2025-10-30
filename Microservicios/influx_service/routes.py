"""InfluxDB wrapper service providing write/query endpoints."""
from __future__ import annotations

import datetime as dt
import os
from typing import Dict, List

from flask import Blueprint, request

from common.auth import require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("influx", __name__)

WRITTEN_POINTS: List[Dict] = []
BUCKETS: Dict[str, Dict] = {
    os.getenv("INFLUX_BUCKET", "heartguard-timeseries"): {
        "name": os.getenv("INFLUX_BUCKET", "heartguard-timeseries"),
        "retention_days": 30,
        "org": os.getenv("INFLUX_ORG", "heartguard"),
    }
}


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "influx", "status": "healthy", "points_cached": len(WRITTEN_POINTS)})


@bp.route("/ready", methods=["GET"])
def ready() -> "Response":
    token_available = bool(os.getenv("INFLUX_TOKEN"))
    status = "ready" if token_available else "degraded"
    return render_response({"status": status, "token": token_available})


@bp.route("/write", methods=["POST"])
@require_auth(optional=True)
def write_points() -> "Response":
    payload, _ = parse_request_data(request)
    points = payload.get("points") or []
    if not isinstance(points, list) or not points:
        raise APIError("points must be a non-empty list", status_code=400, error_id="HG-INFLUX-VALIDATION")
    for point in points:
        point.setdefault("received_at", dt.datetime.utcnow().isoformat() + "Z")
        WRITTEN_POINTS.append(point)
    return render_response({"ingested": len(points)})


@bp.route("/query", methods=["POST"])
@require_auth(optional=True)
def query_points() -> "Response":
    payload, _ = parse_request_data(request)
    measurement = payload.get("measurement")
    limit = int(payload.get("limit", 100))
    filtered = [p for p in WRITTEN_POINTS if measurement is None or p.get("measurement") == measurement]
    return render_response({"results": filtered[:limit]}, meta={"returned": min(limit, len(filtered))})


@bp.route("/buckets", methods=["GET"])
@require_auth(optional=True)
def list_buckets() -> "Response":
    return render_response({"buckets": list(BUCKETS.values())}, meta={"total": len(BUCKETS)})


@bp.route("/buckets", methods=["POST"])
@require_auth(required_roles=["admin"])
def create_bucket() -> "Response":
    payload, _ = parse_request_data(request)
    name = payload.get("name")
    if not name:
        raise APIError("name is required", status_code=400, error_id="HG-INFLUX-BUCKET")
    bucket = {
        "name": name,
        "retention_days": payload.get("retention_days", 30),
        "org": payload.get("org", os.getenv("INFLUX_ORG", "heartguard")),
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    BUCKETS[name] = bucket
    return render_response({"bucket": bucket}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/influx")
