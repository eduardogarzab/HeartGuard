"""Placeholder endpoints for the media service."""
from __future__ import annotations

import logging
from typing import NoReturn

from flask import Blueprint

from common.auth import require_auth
from common.errors import APIError
from common.serialization import render_response

bp = Blueprint("media", __name__)
logger = logging.getLogger(__name__)

PLACEHOLDER_MESSAGE = (
    "Media service placeholder. Functionality will be implemented in a future iteration."
)


def _raise_placeholder(endpoint: str) -> NoReturn:
    logger.info("Media placeholder endpoint hit: %s", endpoint)
    raise APIError(
        PLACEHOLDER_MESSAGE,
        status_code=501,
        error_id="HG-MEDIA-PLACEHOLDER",
        details={"endpoint": endpoint},
    )


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response(
        {
            "service": "media",
            "status": "placeholder",
            "implemented": False,
            "message": PLACEHOLDER_MESSAGE,
        }
    )


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_media() -> "Response":
    return render_response(
        {"media": []},
        meta={"total": 0, "placeholder": True, "message": PLACEHOLDER_MESSAGE},
    )


@bp.route("/upload", methods=["POST"])
@require_auth(optional=True)
def upload_media() -> "Response":
    _raise_placeholder("upload")


@bp.route("/<media_id>", methods=["GET"])
@require_auth(optional=True)
def get_media(media_id: str) -> "Response":
    _raise_placeholder(f"get:{media_id}")


@bp.route("/<media_id>", methods=["DELETE"])
@require_auth(required_roles=["admin", "org_admin"])
def delete_media(media_id: str) -> "Response":
    _raise_placeholder(f"delete:{media_id}")


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/media")
