"""Endpoints principales del Media Service."""
from __future__ import annotations

import uuid
from typing import Any

from flask import Blueprint, Response, current_app, g, request
from werkzeug.datastructures import FileStorage

from ..db import DatabaseClient
from ..middleware.auth import AuthSubject, require_token
from ..services import MediaService, MediaStorageError, MediaValidationError, PhotoDeleteResult, PhotoUploadResult
from ..storage import SpacesClient
from ..utils.responses import error_response, fail_response, success_response

media_bp = Blueprint("media", __name__, url_prefix="/media")


def _ensure_trace_id() -> None:
    if getattr(g, "trace_id", None):
        return
    header_trace = request.headers.get("X-Trace-ID") or request.headers.get("X-Trace-Id")
    g.trace_id = header_trace or uuid.uuid4().hex


@media_bp.before_request
def assign_trace_id() -> None:
    _ensure_trace_id()


def _get_media_service() -> MediaService:
    service = current_app.extensions.get("media_service")
    if service:
        return service

    cfg = current_app.config
    
    # Inicializar cliente de base de datos
    db_client = DatabaseClient(database_url=cfg["DATABASE_URL"])
    
    # Inicializar cliente de almacenamiento
    spaces_client = SpacesClient(
        bucket=cfg["SPACES_BUCKET"],
        region=cfg["SPACES_REGION"],
        endpoint_url=cfg["SPACES_ENDPOINT"],
        access_key=cfg["SPACES_ACCESS_KEY"],
        secret_key=cfg["SPACES_SECRET_KEY"],
        cdn_base_url=cfg["MEDIA_CDN_BASE_URL"],
        default_acl=cfg.get("MEDIA_DEFAULT_ACL", "public-read"),
    )
    
    # Crear servicio
    service = MediaService(
        storage=spaces_client,
        db_client=db_client,
        allowed_content_types=cfg["MEDIA_ALLOWED_CONTENT_TYPES"],
        max_file_size=cfg["MEDIA_MAX_FILE_BYTES"],
        namespace_users=cfg["MEDIA_NAMESPACE_USERS"],
        namespace_patients=cfg["MEDIA_NAMESPACE_PATIENTS"],
    )
    current_app.extensions["media_service"] = service
    current_app.extensions["db_client"] = db_client
    return service


def _extract_file() -> FileStorage:
    file = request.files.get("photo") or request.files.get("file")
    if file is None or not file.filename:
        raise MediaValidationError("Se requiere un archivo en el campo 'photo'", error_code="missing_file")
    return file


def _serialize_upload(result: PhotoUploadResult) -> dict[str, Any]:
    return {
        "photo": result.to_dict(),
    }


def _serialize_delete(result: PhotoDeleteResult) -> dict[str, Any]:
    return {
        "photo": result.to_dict(),
    }


def _handle_validation_error(exc: MediaValidationError) -> Response:
    return fail_response(message=str(exc), error_code=exc.error_code, status_code=exc.status_code)


def _handle_storage_error(exc: MediaStorageError, *, context: dict[str, Any]) -> Response:
    current_app.logger.exception(
        "Error en almacenamiento de media",
        extra={**context, "trace_id": getattr(g, "trace_id", None)},
    )
    return error_response(message=str(exc), error_code=exc.error_code, status_code=exc.status_code)


@media_bp.route("/users/<string:user_id>/photo", methods=["POST", "PUT"])
@require_token(allow={"user"})
def upload_user_photo(user_id: str, auth_subject: AuthSubject):
    if auth_subject.user_id != user_id:
        return fail_response(message="No puedes modificar la foto de otro usuario", error_code="forbidden", status_code=403)
    try:
        file = _extract_file()
    except MediaValidationError as exc:
        return _handle_validation_error(exc)

    service = _get_media_service()
    try:
        result = service.save_photo(entity_type="users", entity_id=user_id, file=file)
        message = "Foto actualizada correctamente" if request.method == "PUT" else "Foto cargada correctamente"
        status = 200 if request.method == "PUT" else 201
        return success_response(data=_serialize_upload(result), message=message, status_code=status)
    except MediaValidationError as exc:
        return _handle_validation_error(exc)
    except MediaStorageError as exc:
        return _handle_storage_error(exc, context={"user_id": user_id})


@media_bp.route("/users/<string:user_id>/photo", methods=["DELETE"])
@require_token(allow={"user"})
def delete_user_photo(user_id: str, auth_subject: AuthSubject):
    if auth_subject.user_id != user_id:
        return fail_response(message="No puedes eliminar la foto de otro usuario", error_code="forbidden", status_code=403)
    service = _get_media_service()
    try:
        result = service.delete_photo(entity_type="users", entity_id=user_id)
        return success_response(data=_serialize_delete(result), message="Foto eliminada", status_code=200)
    except MediaValidationError as exc:
        return _handle_validation_error(exc)
    except MediaStorageError as exc:
        return _handle_storage_error(exc, context={"user_id": user_id})


@media_bp.route("/patients/<string:patient_id>/photo", methods=["POST", "PUT"])
@require_token(allow={"user", "patient"})
def upload_patient_photo(patient_id: str, auth_subject: AuthSubject):
    if auth_subject.is_patient() and auth_subject.patient_id != patient_id:
        return fail_response(message="No puedes modificar la foto de otro paciente", error_code="forbidden", status_code=403)
    try:
        file = _extract_file()
    except MediaValidationError as exc:
        return _handle_validation_error(exc)

    service = _get_media_service()
    try:
        result = service.save_photo(entity_type="patients", entity_id=patient_id, file=file)
        message = "Foto actualizada correctamente" if request.method == "PUT" else "Foto cargada correctamente"
        status = 200 if request.method == "PUT" else 201
        return success_response(data=_serialize_upload(result), message=message, status_code=status)
    except MediaValidationError as exc:
        return _handle_validation_error(exc)
    except MediaStorageError as exc:
        return _handle_storage_error(exc, context={"patient_id": patient_id, "account_type": auth_subject.account_type})


@media_bp.route("/patients/<string:patient_id>/photo", methods=["DELETE"])
@require_token(allow={"user", "patient"})
def delete_patient_photo(patient_id: str, auth_subject: AuthSubject):
    if auth_subject.is_patient() and auth_subject.patient_id != patient_id:
        return fail_response(message="No puedes eliminar la foto de otro paciente", error_code="forbidden", status_code=403)
    service = _get_media_service()
    try:
        result = service.delete_photo(entity_type="patients", entity_id=patient_id)
        return success_response(data=_serialize_delete(result), message="Foto eliminada", status_code=200)
    except MediaValidationError as exc:
        return _handle_validation_error(exc)
    except MediaStorageError as exc:
        return _handle_storage_error(exc, context={"patient_id": patient_id, "account_type": auth_subject.account_type})
