"""Media service for managing objects and signed URLs."""
from __future__ import annotations

import datetime as dt
import datetime as dt
import hashlib
import os
import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import MediaItem

bp = Blueprint("media", __name__)


def _signed_url(media_id: str) -> str:
    secret = os.getenv("MEDIA_SIGNING_SECRET", "demo-secret")
    digest = hashlib.sha256(f"{media_id}:{secret}".encode("utf-8")).hexdigest()
    return f"https://storage.googleapis.com/{os.getenv('GCS_BUCKET', 'heartguard-system')}/{media_id}?signature={digest}"


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "media", "status": "healthy", "items": MediaItem.query.count()})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_media() -> "Response":
    items = [
        _serialize_media(item)
        for item in MediaItem.query.order_by(MediaItem.created_at.desc()).all()
    ]
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
    media = MediaItem(
        id=f"media-{uuid.uuid4()}",
        filename=filename,
        mime_type=mime_type,
        size_bytes=int(size_bytes or 0),
        owner_id=payload.get("owner_id"),
        bucket=os.getenv("GCS_BUCKET", "heartguard-system"),
        created_at=dt.datetime.utcnow(),
    )
    db.session.add(media)
    db.session.commit()
    return render_response({"media": _serialize_media(media)}, status_code=201)


@bp.route("/<media_id>", methods=["GET"])
@require_auth(optional=True)
def get_media(media_id: str) -> "Response":
    item = MediaItem.query.get(media_id)
    if not item:
        raise APIError("Media item not found", status_code=404, error_id="HG-MEDIA-NOT-FOUND")
    return render_response({"media": _serialize_media(item)})


@bp.route("/<media_id>", methods=["DELETE"])
@require_auth(required_roles=["admin", "org_admin"])
def delete_media(media_id: str) -> "Response":
    item = MediaItem.query.get(media_id)
    if not item:
        raise APIError("Media item not found", status_code=404, error_id="HG-MEDIA-NOT-FOUND")
    db.session.delete(item)
    db.session.commit()
    return render_response({"message": "Media deleted"})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/media")
    with app.app_context():
        _seed_default_item()


def _serialize_media(item: MediaItem) -> dict:
    return {
        "id": item.id,
        "filename": item.filename,
        "mime_type": item.mime_type,
        "size_bytes": item.size_bytes,
        "owner_id": item.owner_id,
        "bucket": item.bucket,
        "created_at": (item.created_at or dt.datetime.utcnow()).isoformat() + "Z",
        "signed_url": _signed_url(item.id),
    }


def _seed_default_item() -> None:
    if MediaItem.query.count() > 0:
        return
    media = MediaItem(
        id="media-1",
        filename="report.pdf",
        mime_type="application/pdf",
        size_bytes=12048,
        owner_id="usr-2",
        bucket=os.getenv("GCS_BUCKET", "heartguard-system"),
    )
    db.session.add(media)
    db.session.commit()
