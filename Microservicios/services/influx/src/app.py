import json
import os
import logging
import html
from datetime import datetime
from functools import wraps

import jwt
import xmltodict
from dicttoxml import dicttoxml
from flask import Flask, request, make_response, g
from dotenv import load_dotenv

from influx_client import write_points, query_aggregate, list_buckets, create_bucket, delete_bucket, query_data, DEFAULT_BUCKET

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=os.getenv("influx_LOG_LEVEL", "INFO"))
logger = logging.getLogger("influx-service")

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("influx_ALLOWED_ORIGINS", "*").split(",")]
JWT_SECRET = os.getenv("auth_JWT_SECRET", os.getenv("gateway_JWT_SECRET", "super-secret"))

REQUEST_METRICS = {"requests": 0, "errors": 0, "latency_sum": 0.0}


def render(data, status=200, root="response"):
    accept = request.headers.get("Accept", "application/json")
    if "application/xml" in accept and "json" not in accept:
        xml_body = dicttoxml(data, custom_root=root, attr_type=False).decode("utf-8")
        resp = make_response(xml_body, status)
        resp.headers["Content-Type"] = "application/xml"
        return resp
    resp = make_response(json.dumps(data), status)
    resp.headers["Content-Type"] = "application/json"
    return resp


def error(code, message, status=400):
    return render({"error": {"code": code, "message": message}}, status=status, root="Error")


def parse_body():
    if request.method not in {"POST", "PUT", "PATCH"}:
        return {}
    content_type = request.headers.get("Content-Type", "application/json").split(";")[0]
    if "application/json" in content_type:
        data = request.get_json(silent=True)
        if data is None:
            raise ValueError("Invalid JSON body")
        return data
    if "application/xml" in content_type:
        try:
            parsed = xmltodict.parse(request.data or b"")
            root = next(iter(parsed.values())) if parsed else {}
            return dict(root)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("Invalid XML body") from exc
    raise ValueError("Unsupported Content-Type")


def sanitize(data):
    return {k: html.escape(v.strip()) if isinstance(v, str) else v for k, v in data.items()}


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error("INFLUX_401", "Authorization required", status=401)
        token = auth_header.split(" ", 1)[1]
        try:
            claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return error("INFLUX_401", "Token expired", status=401)
        except jwt.InvalidTokenError:
            return error("INFLUX_401", "Invalid token", status=401)
        g.claims = claims
        return f(*args, **kwargs)

    return decorated


@app.before_request
def before_request():
    request.start_time = datetime.utcnow()


@app.after_request
def after_request(response):
    latency = (datetime.utcnow() - getattr(request, "start_time", datetime.utcnow())).total_seconds() * 1000
    REQUEST_METRICS["requests"] += 1
    REQUEST_METRICS["latency_sum"] += latency
    if response.status_code >= 400:
        REQUEST_METRICS["errors"] += 1
    origin = request.headers.get("Origin")
    if "*" in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
    elif origin and origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, X-Request-ID"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
    return response


@app.route("/timeseries/health", methods=["GET"])
def health():
    return render({"status": "ok", "service": "influx"})


@app.route("/timeseries/ready", methods=["GET"])
def ready():
    try:
        buckets = list_buckets()
        return render({"status": "ready", "buckets": [b.name for b in buckets]}, root="Ready")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Influx not ready", extra={"error": str(exc)})
        return error("INFLUX_503", "InfluxDB not ready", status=503)


@app.route("/timeseries/metrics", methods=["GET"])
def metrics():
    avg = REQUEST_METRICS["latency_sum"] / REQUEST_METRICS["requests"] if REQUEST_METRICS["requests"] else 0
    return render({
        "requests_total": REQUEST_METRICS["requests"],
        "errors_total": REQUEST_METRICS["errors"],
        "latency_avg_ms": round(avg, 2)
    })


@app.route("/timeseries/write", methods=["POST"])
@token_required
def write():
    try:
        payload = sanitize(parse_body())
    except ValueError as exc:
        return error("INFLUX_415", str(exc), status=415)
    bucket = payload.get("bucket", DEFAULT_BUCKET)
    points = payload.get("points")
    if not points or not isinstance(points, list):
        return error("INFLUX_400", "points must be a list", status=400)
    try:
        write_points(bucket, points)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to write points", extra={"error": str(exc)})
        return error("INFLUX_500", "Write error", status=500)
    return render({"success": True, "inserted": len(points)}, root="WriteResult")


@app.route("/timeseries/query", methods=["POST"])
@token_required
def query():
    try:
        payload = sanitize(parse_body())
    except ValueError as exc:
        return error("INFLUX_415", str(exc), status=415)
    bucket = payload.get("bucket", DEFAULT_BUCKET)
    measurement = payload.get("measurement")
    if not measurement:
        return error("INFLUX_400", "measurement is required", status=400)
    start = payload.get("range_start", "-1h")
    stop = payload.get("range_stop", "now()")
    limit = int(payload.get("limit", 100))
    offset = int(payload.get("offset", 0))
    aggregate = payload.get("aggregate")
    window = payload.get("window", "1m")
    try:
        if aggregate:
            results = query_aggregate(bucket, measurement, start, stop, window, aggregate)
        else:
            flux = f"from(bucket: \"{bucket}\") |> range(start: {start}, stop: {stop}) |> filter(fn: (r) => r._measurement == \"{measurement}\")"
            if limit:
                flux += f" |> limit(n: {limit}, offset: {offset})"
            results = query_data(flux)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Query error", extra={"error": str(exc)})
        return error("INFLUX_500", "Query error", status=500)
    return render({"results": results, "count": len(results)}, root="QueryResult")


@app.route("/timeseries/buckets", methods=["GET"])
@token_required
def buckets():
    try:
        buckets_list = list_buckets()
        payload = {"buckets": [{"id": b.id, "name": b.name, "retention_seconds": b.retention_rules[0].every_seconds if b.retention_rules else 0} for b in buckets_list]}
        return render(payload, root="Buckets")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Bucket list error", extra={"error": str(exc)})
        return error("INFLUX_500", "Bucket list error", status=500)


@app.route("/timeseries/buckets", methods=["POST"])
@token_required
def create_bucket_route():
    try:
        payload = sanitize(parse_body())
    except ValueError as exc:
        return error("INFLUX_415", str(exc), status=415)
    name = payload.get("name") or payload.get("bucket")
    retention = int(payload.get("retention_seconds", 0))
    if not name:
        return error("INFLUX_400", "name is required", status=400)
    try:
        bucket = create_bucket(name, retention_seconds=retention)
        return render({"id": bucket.id, "name": bucket.name}, status=201, root="Bucket")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Bucket create error", extra={"error": str(exc)})
        return error("INFLUX_500", "Bucket create error", status=500)


@app.route("/timeseries/buckets/<bucket_id>", methods=["DELETE"])
@token_required
def delete_bucket_route(bucket_id):
    try:
        delete_bucket(bucket_id)
        return render({"status": "deleted", "bucket_id": bucket_id}, root="BucketDelete")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Bucket delete error", extra={"error": str(exc)})
        return error("INFLUX_500", "Bucket delete error", status=500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("influx_PORT", 5005)))
