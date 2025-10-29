from flask import Blueprint


alerts_bp = Blueprint("alerts", __name__, url_prefix="/v1")

from . import alerts  # noqa: E402,F401
