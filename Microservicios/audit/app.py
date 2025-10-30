import os

from flask import Flask, g, request

from .error_handler import register_error_handlers
from .middleware import get_metrics, init_app
from .models import append_event, list_events
from .utils_format import error_response, make_response, parse_body

app = Flask(__name__)
init_app(app)
register_error_handlers(app)

ALLOWED_ROLES = {"admin", "org_admin"}


@app.route("/health", methods=["GET"])
def health():
    return make_response({"status": "ok", "service": "audit"})


@app.route("/ready", methods=["GET"])
def ready():
    return make_response({"status": "ready"})


@app.route("/metrics", methods=["GET"])
def metrics():
    return make_response(get_metrics(), root_tag="Metrics")


# POST /audit/event
# Request JSON/XML:
# {
#   "actor_user_id": "42",
#   "action": "user.login",
#   "entity_type": "user",
#   "entity_id": "42",
#   "ip": "203.0.113.5",
#   "metadata": {"method": "POST"}
# }
# Response:
# {
#   "event_id": "...",
#   "timestamp": "2025-10-29T18:00:00Z"
# }
@app.route("/audit/event", methods=["POST"])
def create_event():
    if g.get("user_role") not in ALLOWED_ROLES:
        return error_response(403, "Forbidden for role")
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    required = ["actor_user_id", "action", "entity_type", "entity_id", "ip"]
    missing = [field for field in required if field not in body]
    if missing:
        return error_response(400, f"Missing fields: {', '.join(missing)}")
    event = append_event(body)
    return make_response({"event": event}, status=201, root_tag="AuditEvent")


# GET /audit/events?actor_user_id=42&entity_type=user
# Response JSON/XML:
# {
#   "events": [
#     {"event_id": "...", "action": "user.login"}
#   ]
# }
@app.route("/audit/events", methods=["GET"])
def get_events():
    if g.get("user_role") not in ALLOWED_ROLES:
        return error_response(403, "Forbidden for role")
    filters = {
        "actor_user_id": request.args.get("actor_user_id"),
        "entity_type": request.args.get("entity_type"),
        "since": request.args.get("since"),
        "until": request.args.get("until"),
    }
    events = list_events(filters)
    return make_response({"events": events}, root_tag="AuditEvents")


if __name__ == "__main__":
    port = int(os.getenv("AUDIT_PORT", "5006"))
    app.run(host="0.0.0.0", port=port)
