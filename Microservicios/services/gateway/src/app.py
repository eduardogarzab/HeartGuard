import os
import time
import logging
import uuid
from urllib.parse import urljoin

import jwt
import requests
import redis
from flask import Flask, request, Response
from dotenv import load_dotenv

from utils import response_payload, error_response

load_dotenv()

app = Flask(__name__)

logging.basicConfig(level=os.getenv("gateway_LOG_LEVEL", "INFO"))
logger = logging.getLogger("gateway")

ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("gateway_ALLOWED_ORIGINS", "*").split(",")]
JWT_SECRET = os.getenv("gateway_JWT_SECRET", "super-secret")
RATE_LIMIT_CONF = os.getenv("gateway_RATE_LIMIT", "100/min")
REDIS_URL = os.getenv("gateway_REDIS_URL")

redis_client = None
if REDIS_URL:
    try:
        redis_client = redis.Redis.from_url(REDIS_URL)
        redis_client.ping()
    except redis.RedisError:
        logger.warning("Redis no disponible para rate limiting; usando memoria local")
        redis_client = None

LOCAL_RATE = {}

SERVICE_ROUTES = {
    "auth": os.getenv("AUTH_URL", "http://auth:5001"),
    "organization": os.getenv("ORG_URL", "http://organization:5002"),
    "users": os.getenv("USER_URL", "http://user:5003"),
    "media": os.getenv("MEDIA_URL", "http://media:5004"),
    "timeseries": os.getenv("INFLUX_PROXY_URL", "http://influx:5005"),
    "audit": os.getenv("AUDIT_URL", "http://audit:5006"),
}

RBAC_RULES = {
    "organization": {
        "PUT": {"admin", "manager"},
        "GET": {"admin", "manager", "user"}
    },
    "media": {
        "DELETE": {"admin"}
    },
    "audit": {
        "GET": {"admin"}
    }
}

PUBLIC_PATHS = {
    ("GET", "gateway/health"),
    ("GET", "gateway/metrics"),
    ("POST", "auth/login"),
    ("POST", "auth/register"),
    ("POST", "auth/refresh"),
    ("GET", "auth/health"),
    ("GET", "timeseries/health"),
    ("GET", "timeseries/ready"),
}

REQUEST_METRICS = {
    "total": 0,
    "errors": 0,
    "latency_sum": 0.0
}


def parse_rate_limit(config):
    try:
        amount, interval = config.split("/")
        amount = int(amount)
        interval = interval.strip()
        window_seconds = {
            "sec": 1,
            "s": 1,
            "min": 60,
            "m": 60,
            "hour": 3600,
            "h": 3600
        }.get(interval, 60)
        return amount, window_seconds
    except ValueError:
        return 100, 60


LIMIT, WINDOW = parse_rate_limit(RATE_LIMIT_CONF)


def rate_limited(identifier):
    if redis_client:
        key = f"ratelimit:{identifier}"
        current = redis_client.incr(key)
        if current == 1:
            redis_client.expire(key, WINDOW)
        if current > LIMIT:
            return True, current
        return False, current
    now = time.time()
    bucket = LOCAL_RATE.setdefault(identifier, [])
    bucket[:] = [ts for ts in bucket if ts > now - WINDOW]
    if len(bucket) >= LIMIT:
        return True, len(bucket)
    bucket.append(now)
    return False, len(bucket)


def requires_auth(method, path):
    normalized = path.strip("/")
    return (method, normalized) not in PUBLIC_PATHS


def validate_jwt(token):
    decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    return decoded


def check_rbac(claims, prefix, method):
    roles = RBAC_RULES.get(prefix, {})
    required = roles.get(method)
    if not required:
        return True
    return claims.get("role") in required


@app.before_request
def before():
    request.start_time = time.time()
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.request_id = request_id
    identifier = request.headers.get("Authorization", request.remote_addr or "anonymous")
    limited, current = rate_limited(identifier)
    if limited:
        logger.warning("Rate limit excedido", extra={"request_id": request_id, "identifier": identifier})
        return error_response("GATEWAY_429", "Rate limit exceeded", status=429)


@app.after_request
def after(response):
    latency = (time.time() - getattr(request, "start_time", time.time())) * 1000
    REQUEST_METRICS["total"] += 1
    REQUEST_METRICS["latency_sum"] += latency
    if response.status_code >= 400:
        REQUEST_METRICS["errors"] += 1
    origin = request.headers.get("Origin")
    if "*" in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
    elif origin and origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, X-Request-ID"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    response.headers["X-Request-ID"] = getattr(request, "request_id", "")
    return response


@app.route("/gateway/health", methods=["GET"])
def health():
    return response_payload({"status": "ok", "service": "gateway"})


@app.route("/gateway/metrics", methods=["GET"])
def metrics():
    avg_latency = REQUEST_METRICS["latency_sum"] / REQUEST_METRICS["total"] if REQUEST_METRICS["total"] else 0
    payload = {
        "requests_total": REQUEST_METRICS["total"],
        "requests_errors": REQUEST_METRICS["errors"],
        "latency_avg_ms": round(avg_latency, 2)
    }
    accept = request.headers.get("Accept", "application/json")
    if "text/plain" in accept:
        metrics_text = "\n".join([
            f"gateway_requests_total {REQUEST_METRICS['total']}",
            f"gateway_requests_errors {REQUEST_METRICS['errors']}",
            f"gateway_latency_avg_ms {round(avg_latency, 2)}"
        ])
        return Response(metrics_text, mimetype="text/plain")
    return response_payload(payload)


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
def proxy(path):
    if request.method == "OPTIONS":
        return Response(status=204)

    segments = path.split("/") if path else []
    if not segments or segments[0] == "gateway":
        return error_response("GATEWAY_404", "Ruta no encontrada", status=404)

    prefix = segments[0]
    upstream = SERVICE_ROUTES.get(prefix)
    if not upstream:
        return error_response("GATEWAY_404", "Servicio no disponible", status=404)

    token = None
    claims = None
    if requires_auth(request.method, path):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error_response("GATEWAY_401", "Authorization header missing", status=401)
        token = auth_header.split(" ", 1)[1]
        try:
            claims = validate_jwt(token)
        except jwt.ExpiredSignatureError:
            return error_response("GATEWAY_401", "Token expired", status=401)
        except jwt.InvalidTokenError:
            return error_response("GATEWAY_401", "Invalid token", status=401)
        if not check_rbac(claims, prefix, request.method):
            return error_response("GATEWAY_403", "Insufficient role", status=403)

    url = urljoin(upstream + "/", "/".join(segments[1:]))
    headers = {key: value for key, value in request.headers if key.lower() not in {"host"}}
    headers["X-Forwarded-For"] = request.remote_addr or ""
    headers["X-Request-ID"] = getattr(request, "request_id", str(uuid.uuid4()))

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=15
        )
        excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
        response_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded]
        response = Response(resp.content, resp.status_code, response_headers)
        return response
    except requests.RequestException as exc:
        logger.exception("Error proxying request", extra={"request_id": getattr(request, "request_id", ""), "error": str(exc)})
        return error_response("GATEWAY_502", "Upstream error", status=502)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("gateway_PORT", 5000)))
