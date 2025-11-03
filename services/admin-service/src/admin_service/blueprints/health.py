"""Health check blueprint."""

from __future__ import annotations

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Return service health information."""
    return jsonify({"status": "ok"})


__all__ = ["health_bp"]
