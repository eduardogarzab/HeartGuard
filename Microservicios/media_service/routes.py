"""Media service for managing objects and signed URLs."""
from __future__ import annotations

import datetime as dt
import os
from typing import Dict
import logging

from flask import Blueprint, request
from google.cloud import storage
from google.oauth2 import service_account

from common.auth import require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("media", __name__)
logger = logging.getLogger(__name__)

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

# Initialize GCS client
_gcs_client = None


def _get_gcs_client():
    """Get or create GCS client with credentials."""
    global _gcs_client
    if _gcs_client is not None:
        return _gcs_client
    
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if credentials_path and os.path.exists(credentials_path):
        # Use service account credentials from file
        logger.info(f"Loading GCS credentials from {credentials_path}")
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        _gcs_client = storage.Client(credentials=credentials)
    else:
        # Try to use default credentials or application default
        logger.warning("No GOOGLE_APPLICATION_CREDENTIALS found, using default credentials")
        try:
            _gcs_client = storage.Client()
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            _gcs_client = None
    
    return _gcs_client


def _generate_signed_url(bucket_name: str, blob_name: str, expiration_minutes: int = 60) -> str:
    """Generate a signed URL for a GCS object."""
    try:
        client = _get_gcs_client()
        if client is None:
            # Fallback to fake URL if no credentials
            logger.warning("GCS client not available, generating mock URL")
            return f"https://storage.googleapis.com/{bucket_name}/{blob_name}?mock=true"
        
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # Generate signed URL valid for specified minutes
        url = blob.generate_signed_url(
            version="v4",
            expiration=dt.timedelta(minutes=expiration_minutes),
            method="GET",
        )
        
        return url
    except Exception as e:
        logger.error(f"Error generating signed URL: {e}")
        # Return a fallback URL
        return f"https://storage.googleapis.com/{bucket_name}/{blob_name}?error=true"


def _upload_to_gcs(bucket_name: str, blob_name: str, content: bytes, content_type: str) -> bool:
    """Upload content to GCS."""
    try:
        client = _get_gcs_client()
        if client is None:
            logger.warning("GCS client not available, skipping upload")
            return False
        
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        blob.upload_from_string(content, content_type=content_type)
        logger.info(f"Successfully uploaded {blob_name} to {bucket_name}")
        return True
    except Exception as e:
        logger.error(f"Error uploading to GCS: {e}")
        return False


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "media", "status": "healthy", "items": len(MEDIA_ITEMS)})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_media() -> "Response":
    items = []
    bucket_name = os.getenv("GCS_BUCKET", "heartguard-system")
    for item in MEDIA_ITEMS.values():
        enriched = dict(item)
        enriched["signed_url"] = _generate_signed_url(bucket_name, item["id"])
        items.append(enriched)
    return render_response({"media": items}, meta={"total": len(items)})


@bp.route("/upload", methods=["POST"])
@require_auth(optional=True)
def upload_media() -> "Response":
    payload, _ = parse_request_data(request)
    filename = payload.get("filename")
    mime_type = payload.get("mime_type")
    size_bytes = payload.get("size_bytes")
    content_base64 = payload.get("content")  # Base64 encoded content
    
    if not filename or not mime_type:
        raise APIError("filename and mime_type are required", status_code=400, error_id="HG-MEDIA-VALIDATION")
    if size_bytes and int(size_bytes) > int(os.getenv("MEDIA_MAX_FILE_SIZE_MB", "50")) * 1024 * 1024:
        raise APIError("File exceeds maximum allowed size", status_code=400, error_id="HG-MEDIA-SIZE")
    
    media_id = f"media-{len(MEDIA_ITEMS) + 1}"
    bucket_name = os.getenv("GCS_BUCKET", "heartguard-system")
    
    # Upload to GCS if content is provided
    if content_base64:
        import base64
        try:
            content = base64.b64decode(content_base64)
            _upload_to_gcs(bucket_name, media_id, content, mime_type)
        except Exception as e:
            logger.error(f"Error processing upload: {e}")
            raise APIError("Invalid content encoding", status_code=400, error_id="HG-MEDIA-ENCODING")
    
    item = {
        "id": media_id,
        "filename": filename,
        "mime_type": mime_type,
        "size_bytes": size_bytes or 0,
        "owner_id": payload.get("owner_id"),
        "bucket": bucket_name,
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    MEDIA_ITEMS[media_id] = item
    item_with_url = dict(item)
    item_with_url["signed_url"] = _generate_signed_url(bucket_name, media_id)
    return render_response({"media": item_with_url}, status_code=201)


@bp.route("/<media_id>", methods=["GET"])
@require_auth(optional=True)
def get_media(media_id: str) -> "Response":
    item = MEDIA_ITEMS.get(media_id)
    if not item:
        raise APIError("Media item not found", status_code=404, error_id="HG-MEDIA-NOT-FOUND")
    enriched = dict(item)
    bucket_name = os.getenv("GCS_BUCKET", "heartguard-system")
    enriched["signed_url"] = _generate_signed_url(bucket_name, media_id)
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
