import os

from flask import Flask, g

from .error_handler import register_error_handlers
from .middleware import get_metrics, init_app
from .models import get_user, update_user
from .utils_format import error_response, make_response, parse_body

app = Flask(__name__)
init_app(app)
register_error_handlers(app)


@app.route("/health", methods=["GET"])
def health():
    return make_response({"status": "ok", "service": "user"})


@app.route("/ready", methods=["GET"])
def ready():
    return make_response({"status": "ready"})


@app.route("/metrics", methods=["GET"])
def metrics():
    return make_response(get_metrics(), root_tag="Metrics")


# GET /user/me
# Response JSON/XML:
# {
#   "user": {
#     "user_id": "123",
#     "email": "demo@heartguard.com",
#     "name": "Demo User",
#     "phone": "+52-555-0101",
#     "preferences": {
#       "language": "es-MX",
#       "units": "metric"
#     },
#     "org_id": "default",
#     "role": "user"
#   }
# }
@app.route("/user/me", methods=["GET"])
def get_me():
    user_id = g.get("user_id")
    if not user_id:
        return error_response(401, "Missing user identity")
    profile = get_user(user_id)
    return make_response({"user": profile}, root_tag="UserProfile")


# PUT /user/me
# Request JSON/XML:
# {
#   "name": "Nuevo Nombre",
#   "phone": "+52-555-9999",
#   "preferences": {"language": "es-MX", "units": "metric"}
# }
# Response mirrors the updated profile.
@app.route("/user/me", methods=["PUT"])
def update_me():
    user_id = g.get("user_id")
    if not user_id:
        return error_response(401, "Missing user identity")
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    profile = update_user(user_id, body)
    return make_response({"user": profile}, root_tag="UserProfile")


if __name__ == "__main__":
    port = int(os.getenv("USER_PORT", "5003"))
    app.run(host="0.0.0.0", port=port)
