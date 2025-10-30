import base64
import os
import mimetypes
from datetime import timedelta

from google.cloud import storage

GCS_BUCKET = os.getenv("GCS_BUCKET", "heartguard-system")
SERVICE_ACCOUNT = os.getenv("SERVICE_ACCOUNT_EMAIL")
SIGNED_URL_TTL = int(os.getenv("media_SIGNED_URL_TTL", "900"))

_client = None


def get_client():
    global _client
    if _client is None:
        _client = storage.Client()
    return _client


def upload_file(file_name: str, data_base64: str, content_type: str, path_prefix: str) -> str:
    client = get_client()
    bucket = client.bucket(GCS_BUCKET)
    blob_path = f"{path_prefix}/{file_name}"
    blob = bucket.blob(blob_path)
    if not content_type:
        content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    blob.upload_from_string(base64.b64decode(data_base64), content_type=content_type)
    return blob_path


def generate_signed_url(blob_path: str) -> str:
    client = get_client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(blob_path)
    return blob.generate_signed_url(expiration=timedelta(seconds=SIGNED_URL_TTL), version="v4")


def delete_blob(blob_path: str) -> None:
    client = get_client()
    bucket = client.bucket(GCS_BUCKET)
    bucket.delete_blob(blob_path)
