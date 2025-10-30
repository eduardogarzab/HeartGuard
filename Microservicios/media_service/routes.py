"""Media service for managing objects and signed URLs."""
from __future__ import annotations

import datetime as dt
import hashlib
import os
from typing import Dict

from flask import Blueprint, request

from common.auth import require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("media", __name__)

MEDIA_ITEMS: Dict[str, Dict] = {
    "media-1": {
        "id": "media-1",
        "filename": "report.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 12048,
        "owner_id": "usr-2",
        "bucket": os.getenv("GCS_BUCKET", "heartguard-system"),
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
}


def _signed_url(media_id: str) -> str:
    secret = os.getenv("MEDIA_SIGNING_SECRET", "demo-secret")
    digest = hashlib.sha256(f"{media_id}:{secret}".encode("utf-8")).hexdigest()
    return f"https://storage.googleapis.com/{os.getenv('GCS_BUCKET', 'heartguard-system')}/{media_id}?signature={digest}"


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "media", "status": "healthy", "items": len(MEDIA_ITEMS)})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_media() -> "Response":
    items = []
    for item in MEDIA_ITEMS.values():
        enriched = dict(item)
        enriched["signed_url"] = _signed_url(item["id"])
        items.append(enriched)
    return render_response({"media": items}, meta={"total": len(items)})


@bp.route("/upload", methods=["POST"])
@require_auth(optional=True)
def upload_media() -> "Response":
    payload, _ = parse_request_data(request)
    filename = payload.get("filename")
    mime_type = payload.get("mime_type")
    size_bytes = payload.get("size_bytes")
    if not filename or not mime_type:
        raise APIError("filename and mime_type are required", status_code=400, error_id="HG-MEDIA-VALIDATION")
    if size_bytes and int(size_bytes) > int(os.getenv("MEDIA_MAX_FILE_SIZE_MB", "50")) * 1024 * 1024:
        raise APIError("File exceeds maximum allowed size", status_code=400, error_id="HG-MEDIA-SIZE")
    media_id = f"media-{len(MEDIA_ITEMS) + 1}"
    item = {
        "id": media_id,
        "filename": filename,
        "mime_type": mime_type,
        "size_bytes": size_bytes or 0,
        "owner_id": payload.get("owner_id"),
        "bucket": os.getenv("GCS_BUCKET", "heartguard-system"),
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    MEDIA_ITEMS[media_id] = item
    item_with_url = dict(item)
    item_with_url["signed_url"] = _signed_url(media_id)
    return render_response({"media": item_with_url}, status_code=201)


@bp.route("/<media_id>", methods=["GET"])
@require_auth(optional=True)
def get_media(media_id: str) -> "Response":
    item = MEDIA_ITEMS.get(media_id)
    if not item:
        raise APIError("Media item not found", status_code=404, error_id="HG-MEDIA-NOT-FOUND")
    enriched = dict(item)
    enriched["signed_url"] = _signed_url(media_id)
    return render_response({"media": enriched})


@bp.route("/<media_id>", methods=["DELETE"])
@require_auth(required_roles=["admin", "org_admin"])
def delete_media(media_id: str) -> "Response":
    if media_id not in MEDIA_ITEMS:
        raise APIError("Media item not found", status_code=404, error_id="HG-MEDIA-NOT-FOUND")
    MEDIA_ITEMS.pop(media_id)
    return render_response({"message": "Media deleted"})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/media")
