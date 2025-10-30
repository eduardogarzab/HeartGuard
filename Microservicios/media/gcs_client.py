"""Google Cloud Storage helper functions.
The module uploads files to GCS and stores metadata in-memory for quick retrieval.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from google.cloud import storage

GCS_BUCKET = os.getenv("GCS_BUCKET", "heartguard-system")
SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL")
MEDIA_METADATA: Dict[str, Dict] = {}

ALLOWED_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
    "text/plain": ".txt",
}


def _client() -> storage.Client:
    return storage.Client()


def upload_file(file_bytes: bytes, mime_type: str, owner_user_id: str) -> Dict:
    extension = ALLOWED_EXTENSIONS.get(mime_type, "")
    media_id = str(uuid4())
    object_path = f"{owner_user_id}/{media_id}{extension}"
    metadata = {
        "media_id": media_id,
        "gcs_path": object_path,
        "mime_type": mime_type,
        "size_bytes": len(file_bytes),
        "owner_user_id": owner_user_id,
    }
    try:
        client = _client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(object_path)
        blob.upload_from_string(file_bytes, content_type=mime_type)
        signed_url = blob.generate_signed_url(expiration=timedelta(minutes=5), method="GET")
        metadata["signed_url"] = signed_url
    except Exception as exc:  # pragma: no cover - runtime dependency
        metadata["signed_url"] = f"https://storage.googleapis.com/{GCS_BUCKET}/{object_path}"
        metadata["warning"] = str(exc)
    created_at = datetime.now(timezone.utc).isoformat()
    MEDIA_METADATA[media_id] = {**metadata, "created_at": created_at}
    return {**metadata, "created_at": created_at}


def generate_signed_url(gcs_path: str) -> Optional[str]:
    try:
        client = _client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(gcs_path)
        return blob.generate_signed_url(expiration=timedelta(minutes=5), method="GET")
    except Exception:  # pragma: no cover
        for meta in MEDIA_METADATA.values():
            if meta.get("gcs_path") == gcs_path:
                return meta.get("signed_url")
        return None


def list_media(owner_user_id: Optional[str] = None) -> List[Dict]:
    if owner_user_id is None:
        return list(MEDIA_METADATA.values())
    return [item for item in MEDIA_METADATA.values() if item.get("owner_user_id") == owner_user_id]


def delete_file(gcs_path: str) -> None:
    try:
        client = _client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(gcs_path)
        blob.delete()
    except Exception:  # pragma: no cover
        pass
    for media_id, meta in list(MEDIA_METADATA.items()):
        if meta.get("gcs_path") == gcs_path:
            MEDIA_METADATA.pop(media_id, None)
            break


def get_media(media_id: str) -> Optional[Dict]:
    return MEDIA_METADATA.get(media_id)
