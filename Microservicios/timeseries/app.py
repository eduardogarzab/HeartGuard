import os

from flask import Flask, g, request

from .error_handler import register_error_handlers
from .influx_client import ping, query_aggregated, write_line_protocol, write_point
from .middleware import get_metrics, init_app
from .utils_format import error_response, make_response, parse_body

app = Flask(__name__)
init_app(app)
register_error_handlers(app)

ALLOWED_WRITE_ROLES = {"admin", "system", "device"}
ALLOWED_QUERY_ROLES = {"admin", "org_admin", "user", "system"}


@app.route("/health", methods=["GET"])
def health():
    return make_response({"status": "ok", "service": "timeseries"})


@app.route("/ready", methods=["GET"])
def ready():
    is_ready = ping()
    status = 200 if is_ready else 503
    return make_response({"status": "ready" if is_ready else "degraded", "dependencies": {"influx": is_ready}}, status=status)


@app.route("/metrics", methods=["GET"])
def metrics():
    return make_response(get_metrics(), root_tag="Metrics")


def _format_flux_time(value: str, default: str) -> str:
    if not value:
        return default
    if value.startswith("-") or value.endswith("()"):
        return value
    return f'time(v: "{value}")'


# POST /timeseries/write
# JSON/XML request:
# {
#   "measurement": "heart_rate",
#   "tags": {"user_id": "42", "device_id": "abc"},
#   "fields": {"bpm": 87.5, "hrv": 42.1},
#   "timestamp": "2025-10-29T18:07:00Z"
# }
# Response:
# {"status": "accepted"}
@app.route("/timeseries/write", methods=["POST"])
def timeseries_write():
    role = g.get("user_role")
    if role not in ALLOWED_WRITE_ROLES:
        return error_response(403, "Forbidden for role")
    if request.headers.get("Content-Type", "").startswith("text/plain"):
        payload = request.get_data().decode("utf-8")
        if not payload.strip():
            return error_response(400, "Empty payload")
        try:
            write_line_protocol(payload)
        except Exception as exc:  # pragma: no cover - depends on Influx
            return error_response(500, "Failed to write line protocol", str(exc))
        return make_response({"status": "accepted"}, status=202, root_tag="TimeSeriesWriteResponse")
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    required = ["measurement", "tags", "fields", "timestamp"]
    missing = [field for field in required if field not in body]
    if missing:
        return error_response(400, f"Missing fields: {', '.join(missing)}")
    if "user_id" not in body.get("tags", {}):
        return error_response(400, "tags.user_id is required")
    try:
        write_point(body["measurement"], dict(body["tags"]), dict(body["fields"]), body["timestamp"])
    except Exception as exc:  # pragma: no cover
        return error_response(500, "Failed to write point", str(exc))
    return make_response({"status": "accepted"}, status=202, root_tag="TimeSeriesWriteResponse")


# GET /timeseries/query?measurement=heart_rate&user_id=42&start=-1h&agg=mean&window=1m
# Response JSON/XML:
# {
#   "series": [
#     {"time": "2025-10-29T18:07:00Z", "bpm_mean": 87.5}
#   ],
#   "page": 1,
#   "next_page": 2,
#   "window": "1m",
#   "agg": "mean",
#   "measurement": "heart_rate",
#   "user_id": "42"
# }
@app.route("/timeseries/query", methods=["GET"])
def timeseries_query():
    role = g.get("user_role")
    if role not in ALLOWED_QUERY_ROLES:
        return error_response(403, "Forbidden for role")
    measurement = request.args.get("measurement")
    user_id = request.args.get("user_id") or g.get("user_id")
    if not measurement or not user_id:
        return error_response(400, "measurement and user_id are required")
    if role == "user" and user_id != g.get("user_id"):
        return error_response(403, "Users may only query their own data")
    start_raw = request.args.get("start")
    end_raw = request.args.get("end")
    window = request.args.get("window", "1m")
    agg = request.args.get("agg", "mean")
    limit = int(request.args.get("limit", "100"))
    page = int(request.args.get("page", "1"))
    start = _format_flux_time(start_raw, "-1h")
    end = _format_flux_time(end_raw, "now()")
    try:
        data = query_aggregated(measurement, user_id, start, end, window, agg, limit, page)
    except Exception as exc:  # pragma: no cover
        return error_response(500, "Failed to query timeseries", str(exc))
    next_page = page + 1 if len(data) == limit else None
    response_body = {
        "series": data,
        "page": page,
        "next_page": next_page,
        "window": window,
        "agg": agg,
        "measurement": measurement,
        "user_id": user_id,
    }
    return make_response(response_body, root_tag="TimeSeriesQueryResult")


if __name__ == "__main__":
    port = int(os.getenv("TIMESERIES_PORT", "5005"))
    app.run(host="0.0.0.0", port=port)
