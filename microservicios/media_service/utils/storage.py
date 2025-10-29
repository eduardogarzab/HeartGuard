"""Google Cloud Storage helpers."""

from datetime import timedelta
from typing import IO
from uuid import uuid4

from google.api_core.exceptions import NotFound
from google.cloud import storage

from config import settings

_client = storage.Client()
_bucket = _client.bucket(settings.GCS_BUCKET)


class StorageError(Exception):
    """Domain exception for storage failures."""


def _safe_entity(entity: str) -> str:
    allowed = {"patients", "users"}
    entity = (entity or "").strip().lower()
    if entity not in allowed:
        raise StorageError("Tipo de entidad inválido")
    return entity


def build_object_name(entity: str, filename: str | None = None) -> str:
    entity = _safe_entity(entity)
    extension = ""
    if filename and "." in filename:
        extension = "." + filename.rsplit(".", 1)[1].lower()
    return f"{uuid4()}" + extension


def object_path(org_id: str, entity: str, object_name: str) -> str:
    entity = _safe_entity(entity)
    cleaned = (object_name or "").strip().lstrip("/")
    if not cleaned:
        raise StorageError("Nombre de objeto requerido")
    if "/" in cleaned:
        raise StorageError("Nombre de objeto inválido")
    return f"{org_id}/{entity}/{cleaned}"


def upload(org_id: str, entity: str, file_obj: IO[bytes], filename: str, content_type: str | None) -> str:
    name = build_object_name(entity, filename)
    full_path = object_path(org_id, entity, name)
    blob = _bucket.blob(full_path)
    file_obj.seek(0)
    blob.upload_from_file(file_obj, content_type=content_type)
    return full_path


def generate_signed_url(full_path: str, method: str = "GET") -> str:
    blob = _bucket.blob(full_path)
    expiration = timedelta(seconds=settings.SIGNED_URL_TTL_SECONDS)
    return blob.generate_signed_url(expiration=expiration, method=method)


def delete(full_path: str) -> None:
    blob = _bucket.blob(full_path)
    try:
        blob.delete()
    except NotFound as exc:
        raise StorageError("Archivo no encontrado") from exc


def ensure_exists(full_path: str) -> None:
    blob = _bucket.blob(full_path)
    if not blob.exists():
        raise StorageError("Archivo no encontrado")
