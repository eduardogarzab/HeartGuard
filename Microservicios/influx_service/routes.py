"""InfluxDB wrapper service providing write/query endpoints."""
from __future__ import annotations

import datetime as dt
import os
import datetime as dt
import os

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import InfluxBucket, TimeseriesPoint

bp = Blueprint("influx", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "influx", "status": "healthy", "points_cached": TimeseriesPoint.query.count()})


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
    for raw_point in points:
        measurement = raw_point.get("measurement")
        bucket_name = raw_point.get("bucket") or os.getenv("INFLUX_BUCKET", "heartguard-timeseries")
        if not measurement:
            raise APIError("measurement is required", status_code=400, error_id="HG-INFLUX-MEASUREMENT")
        bucket = InfluxBucket.query.get(bucket_name)
        if not bucket:
            bucket = InfluxBucket(
                name=bucket_name,
                retention_days=raw_point.get("retention_days", 30),
                org=raw_point.get("org", os.getenv("INFLUX_ORG", "heartguard")),
                created_at=dt.datetime.utcnow(),
            )
            db.session.add(bucket)
        point = TimeseriesPoint(
            bucket=bucket.name,
            measurement=measurement,
            tags=raw_point.get("tags", {}),
            fields=raw_point.get("fields", {}),
            received_at=dt.datetime.utcnow(),
        )
        db.session.add(point)
    db.session.commit()
    return render_response({"ingested": len(points)})


@bp.route("/query", methods=["POST"])
@require_auth(optional=True)
def query_points() -> "Response":
    payload, _ = parse_request_data(request)
    measurement = payload.get("measurement")
    limit = int(payload.get("limit", 100))
    query = TimeseriesPoint.query
    if measurement:
        query = query.filter_by(measurement=measurement)
    results = [
        {
            "id": point.id,
            "bucket": point.bucket,
            "measurement": point.measurement,
            "tags": point.tags,
            "fields": point.fields,
            "received_at": point.received_at.isoformat() + "Z",
        }
        for point in query.order_by(TimeseriesPoint.received_at.desc()).limit(limit).all()
    ]
    return render_response({"results": results}, meta={"returned": len(results)})


@bp.route("/buckets", methods=["GET"])
@require_auth(optional=True)
def list_buckets() -> "Response":
    buckets = [
        {
            "name": bucket.name,
            "retention_days": bucket.retention_days,
            "org": bucket.org,
            "created_at": (bucket.created_at or dt.datetime.utcnow()).isoformat() + "Z",
        }
        for bucket in InfluxBucket.query.all()
    ]
    return render_response({"buckets": buckets}, meta={"total": len(buckets)})


@bp.route("/buckets", methods=["POST"])
@require_auth(required_roles=["admin"])
def create_bucket() -> "Response":
    payload, _ = parse_request_data(request)
    name = payload.get("name")
    if not name:
        raise APIError("name is required", status_code=400, error_id="HG-INFLUX-BUCKET")
    bucket = InfluxBucket(
        name=name,
        retention_days=int(payload.get("retention_days", 30)),
        org=payload.get("org", os.getenv("INFLUX_ORG", "heartguard")),
        created_at=dt.datetime.utcnow(),
    )
    db.session.add(bucket)
    db.session.commit()
    return render_response({
        "bucket": {
            "name": bucket.name,
            "retention_days": bucket.retention_days,
            "org": bucket.org,
            "created_at": bucket.created_at.isoformat() + "Z",
        }
    }, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/influx")
    with app.app_context():
        _seed_default_bucket()


def _seed_default_bucket() -> None:
    if InfluxBucket.query.count() == 0:
        bucket = InfluxBucket(
            name=os.getenv("INFLUX_BUCKET", "heartguard-timeseries"),
            retention_days=30,
            org=os.getenv("INFLUX_ORG", "heartguard"),
        )
        db.session.add(bucket)
        db.session.commit()
