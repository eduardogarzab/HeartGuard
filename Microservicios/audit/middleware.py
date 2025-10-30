import json
import os
import time
import uuid
from typing import Any, Dict

from flask import Flask, g, request

from .utils_format import error_response

SERVICE_NAME = "audit"
MAX_BODY_BYTES = int(os.getenv("MAX_JSON_BODY_BYTES", "1048576"))
REQUEST_STATS: Dict[str, Any] = {
    "count": 0,
    "total_latency_ms": 0.0,
    "start_time": time.time(),
}


def init_app(app: Flask) -> None:
    @app.before_request
    def _before_request():
        g.start_time = time.time()
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        g.user_id = request.headers.get("X-User-ID")
        g.user_role = request.headers.get("X-User-Role")
        if request.content_length and request.content_length > MAX_BODY_BYTES:
            return error_response(413, "Payload too large")

    @app.after_request
    def _after_request(response):
        latency_ms = int((time.time() - getattr(g, "start_time", time.time())) * 1000)
        REQUEST_STATS["count"] += 1
        REQUEST_STATS["total_latency_ms"] += latency_ms
        response.headers["X-Request-ID"] = getattr(g, "request_id", "")
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "service": SERVICE_NAME,
            "request_id": getattr(g, "request_id", ""),
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "latency_ms": latency_ms,
            "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
            "user_id": getattr(g, "user_id", None),
            "role": getattr(g, "user_role", None),
        }
        app.logger.info(json.dumps(log_entry, ensure_ascii=False))
        return response


def get_metrics() -> Dict[str, Any]:
    uptime_seconds = time.time() - REQUEST_STATS["start_time"]
    count = REQUEST_STATS["count"] or 1
    avg_latency = REQUEST_STATS["total_latency_ms"] / count
    return {
        "service": SERVICE_NAME,
        "requests_total": REQUEST_STATS["count"],
        "avg_latency_ms": round(avg_latency, 2),
        "uptime_seconds": int(uptime_seconds),
    }
