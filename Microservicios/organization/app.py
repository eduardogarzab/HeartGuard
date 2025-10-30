import os

from flask import Flask, g

from .error_handler import register_error_handlers
from .middleware import get_metrics, init_app
from .models import get_org, update_org
from .utils_format import error_response, make_response, parse_body

app = Flask(__name__)
init_app(app)
register_error_handlers(app)


@app.route("/health", methods=["GET"])
def health():
    return make_response({"status": "ok", "service": "organization"})


@app.route("/ready", methods=["GET"])
def ready():
    return make_response({"status": "ready"})


@app.route("/metrics", methods=["GET"])
def metrics():
    return make_response(get_metrics(), root_tag="Metrics")


# GET /organization/info
# Response JSON/XML:
# {
#   "organization": {
#     "name": "Heartguard Health",
#     "logo_url": "https://...",
#     "policies": "Default policies",
#     "settings": {
#       "alert_threshold_bpm": 120,
#       "timezone": "UTC"
#     }
#   }
# }
@app.route("/organization/info", methods=["GET"])
def organization_info():
    org_id = g.get("org_id", "default") or "default"
    profile = get_org(org_id)
    return make_response({"organization": profile}, root_tag="OrganizationInfo")


# PUT /organization/info
# Request JSON/XML:
# {
#   "name": "New Name",
#   "logo_url": "https://...",
#   "policies": "<b>Policies</b>",
#   "settings": {
#     "alert_threshold_bpm": 110,
#     "timezone": "America/Mexico_City"
#   }
# }
# Response mirrors the updated organization.
@app.route("/organization/info", methods=["PUT"])
def update_organization_info():
    try:
        body, _ = parse_body()
    except ValueError as exc:
        return error_response(400, str(exc))
    org_id = g.get("org_id", "default") or "default"
    profile = update_org(body, org_id)
    return make_response({"organization": profile}, root_tag="OrganizationInfo")


if __name__ == "__main__":
    port = int(os.getenv("ORG_PORT", "5002"))
    app.run(host="0.0.0.0", port=port)
