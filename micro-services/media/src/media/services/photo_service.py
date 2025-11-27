"""Lógica de negocio para almacenar y eliminar fotos de perfil."""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from ..db import DatabaseClient, DatabaseError
from ..storage.spaces_client import SpacesClient, SpacesClientError

_DEFAULT_EXTENSION_MAP: Dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class MediaValidationError(ValueError):
    """Error de validación controlado para las operaciones de media."""

    def __init__(self, message: str, *, error_code: str = "validation_error", status_code: int = 400) -> None:
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


class MediaStorageError(RuntimeError):
    """Errores derivados del almacenamiento en Spaces."""

    def __init__(self, message: str, *, error_code: str = "storage_error", status_code: int = 502) -> None:
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


@dataclass(slots=True)
class PhotoUploadResult:
    """Representa los datos retornados tras subir una foto."""

    entity_type: str
    entity_id: str
    object_key: str
    url: str
    content_type: str
    size_bytes: int
    etag: str | None
    uploaded_at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "object_key": self.object_key,
            "url": self.url,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "etag": self.etag,
            "uploaded_at": self.uploaded_at.isoformat(),
        }


@dataclass(slots=True)
class PhotoDeleteResult:
    """Información sobre la eliminación de fotos."""

    entity_type: str
    entity_id: str
    deleted_objects: int
    prefix: str

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "deleted_objects": self.deleted_objects,
            "prefix": self.prefix,
        }


class MediaService:
    """Servicio que interactúa con Spaces para gestionar fotos de perfil."""

    def __init__(
        self,
        *,
        storage: SpacesClient,
        db_client: DatabaseClient,
        allowed_content_types: Iterable[str],
        max_file_size: int,
        namespace_users: str,
        namespace_patients: str,
    ) -> None:
        self.storage = storage
        self.db_client = db_client
        self.allowed_map = self._build_allowed_map(allowed_content_types)
        self.allowed_extensions = {ext for ext in self.allowed_map.values()}
        self.max_file_size = max_file_size
        self.namespace_users = namespace_users.strip("/")
        self.namespace_patients = namespace_patients.strip("/")

    def save_photo(self, *, entity_type: str, entity_id: str, file: FileStorage) -> PhotoUploadResult:
        entity_type = self._normalize_entity_type(entity_type)
        entity_id = self._validate_entity_id(entity_id)
        content_type, extension = self._resolve_content_type(file)

        file_bytes = file.read()
        size = len(file_bytes)
        if size == 0:
            raise MediaValidationError("El archivo está vacío", error_code="empty_file")
        if size > self.max_file_size:
            max_mb = round(self.max_file_size / (1024 * 1024), 2)
            raise MediaValidationError(
                f"El archivo excede el tamaño máximo permitido ({max_mb} MB)",
                error_code="file_too_large",
            )
        try:
            file.stream.seek(0)
        except Exception:  # pragma: no cover - defensivo
            pass

        prefix = self._build_prefix(entity_type, entity_id)
        
        # Obtener la URL anterior antes de borrar (para evitar race conditions)
        old_photo_url = None
        try:
            if entity_type == "users":
                old_photo_url = self.db_client.get_user_photo_url(entity_id)
            else:  # patients
                old_photo_url = self.db_client.get_patient_photo_url(entity_id)
        except Exception:
            pass  # Si no se puede obtener, continuamos
        
        object_key = self._build_object_key(prefix, extension)

        # Subir la NUEVA foto PRIMERO (antes de borrar nada)
        try:
            upload_meta = self.storage.upload_object(
                key=object_key,
                data=file_bytes,
                content_type=content_type,
            )
        except SpacesClientError as exc:  # pragma: no cover - entorno externo
            raise MediaStorageError("No se pudo subir la foto al almacenamiento", error_code="upload_failed") from exc

        photo_url = upload_meta["url"]
        
        # Persistir URL en la base de datos (ahora la nueva foto YA existe en Spaces)
        try:
            if entity_type == "users":
                updated = self.db_client.update_user_photo_url(entity_id, photo_url)
            else:  # patients
                updated = self.db_client.update_patient_photo_url(entity_id, photo_url)
            
            if not updated:
                # Si no se encuentra la entidad, eliminar la foto del almacenamiento
                try:
                    self.storage.delete_object(object_key)
                except SpacesClientError:
                    pass  # Ignorar error de limpieza
                raise MediaValidationError(
                    f"No se encontró el {'usuario' if entity_type == 'users' else 'paciente'} con ID {entity_id}",
                    error_code="entity_not_found",
                    status_code=404
                )
        except DatabaseError as exc:
            # Si falla la DB, intentar limpiar el almacenamiento (solo la nueva foto)
            try:
                self.storage.delete_object(object_key)
            except SpacesClientError:
                pass  # Ignorar error de limpieza
            raise MediaStorageError(
                "No se pudo guardar la referencia de la foto en la base de datos",
                error_code="database_error"
            ) from exc
        
        # AHORA que la BD está actualizada, borrar la foto ANTERIOR de forma segura
        # Esto minimiza el tiempo donde un cliente podría tener una URL obsoleta
        if old_photo_url and old_photo_url != photo_url:
            try:
                # Extraer el object key de la URL anterior
                old_object_key = self._extract_object_key_from_url(old_photo_url, prefix)
                if old_object_key:
                    self.storage.delete_object(old_object_key)
            except Exception:
                # Ignorar errores al borrar foto anterior (no crítico)
                pass

        uploaded_at = datetime.now(timezone.utc)
        return PhotoUploadResult(
            entity_type=entity_type,
            entity_id=entity_id,
            object_key=object_key,
            url=photo_url,
            content_type=content_type,
            size_bytes=size,
            etag=upload_meta.get("etag"),
            uploaded_at=uploaded_at,
        )

    def delete_photo(self, *, entity_type: str, entity_id: str) -> PhotoDeleteResult:
        entity_type = self._normalize_entity_type(entity_type)
        entity_id = self._validate_entity_id(entity_id)
        prefix = self._build_prefix(entity_type, entity_id)
        
        # Eliminar del almacenamiento
        try:
            deleted = self.storage.delete_prefix(prefix)
        except SpacesClientError as exc:  # pragma: no cover - entorno externo
            raise MediaStorageError("No se pudo eliminar la foto del almacenamiento", error_code="delete_failed") from exc
        
        # Eliminar referencia de la base de datos
        try:
            if entity_type == "users":
                self.db_client.update_user_photo_url(entity_id, None)
            else:  # patients
                self.db_client.update_patient_photo_url(entity_id, None)
        except DatabaseError as exc:
            # Log el error pero no fallar la operación si el almacenamiento ya fue limpiado
            import logging
            logging.getLogger(__name__).warning(
                f"No se pudo limpiar la URL de la foto en la DB para {entity_type}/{entity_id}: {exc}"
            )
        
        return PhotoDeleteResult(entity_type=entity_type, entity_id=entity_id, deleted_objects=deleted, prefix=prefix)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_allowed_map(content_types: Iterable[str]) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        for content_type in content_types:
            lowered = content_type.lower().strip()
            if not lowered:
                continue
            extension = _DEFAULT_EXTENSION_MAP.get(lowered)
            if not extension:
                extension = os.path.splitext(f"file.{lowered.split('/')[-1]}")[1]
                if not extension:
                    raise MediaValidationError(
                        f"Tipo de contenido no soportado: {content_type}",
                        error_code="unsupported_media_type",
                        status_code=415,
                    )
            mapping[lowered] = extension
        if not mapping:
            raise MediaValidationError(
                "No hay tipos de contenido permitidos configurados",
                error_code="unsupported_media_type",
                status_code=415,
            )
        return mapping

    @staticmethod
    def _validate_entity_id(entity_id: str) -> str:
        if not entity_id:
            raise MediaValidationError("El identificador es requerido", error_code="invalid_entity")
        try:
            uuid.UUID(str(entity_id))
        except ValueError as exc:
            raise MediaValidationError("El identificador debe ser un UUID válido", error_code="invalid_entity") from exc
        return str(entity_id)

    @staticmethod
    def _normalize_entity_type(entity_type: str) -> str:
        normalized = (entity_type or "").strip().lower()
        if normalized not in {"users", "patients", "user", "patient"}:
            raise MediaValidationError("Entidad no soportada", error_code="invalid_entity")
        return "users" if normalized.startswith("user") else "patients"

    def _resolve_content_type(self, file: FileStorage) -> tuple[str, str]:
        candidate = (file.mimetype or file.content_type or "").lower()
        if candidate in self.allowed_map:
            return candidate, self.allowed_map[candidate]
        
        # Log para debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Content type rechazado: '{candidate}' (mimetype={file.mimetype}, content_type={file.content_type}, filename={file.filename})")
        logger.error(f"Tipos permitidos: {list(self.allowed_map.keys())}")
        
        raise MediaValidationError(
            f"Tipo de archivo no permitido: {candidate or 'desconocido'}. Tipos aceptados: {', '.join(self.allowed_map.keys())}",
            error_code="unsupported_file_type",
            status_code=415,
        )

    def _extract_object_key_from_url(self, photo_url: str, prefix: str) -> str | None:
        """Extrae el object key de una URL de foto.
        
        Args:
            photo_url: URL completa de la foto
            prefix: Prefijo esperado (users/<id>/ o patients/<id>/)
            
        Returns:
            Object key si se pudo extraer, None en caso contrario
        """
        try:
            # URL format: https://bucket.region.digitaloceanspaces.com/prefix/filename.ext
            # Extraer la parte después del dominio
            if '/' not in photo_url:
                return None
            
            parts = photo_url.split('/', 3)  # ['https:', '', 'bucket.region.digitaloceanspaces.com', 'path...']
            if len(parts) < 4:
                return None
            
            path = parts[3]  # 'users/uuid/profile-xxx.jpg'
            
            # Verificar que empiece con el prefijo esperado
            if path.startswith(prefix):
                return path
            
            return None
        except Exception:
            return None
            return candidate, self.allowed_map[candidate]

        filename = secure_filename(file.filename or "")
        extension = os.path.splitext(filename)[1].lower()
        if extension in self.allowed_extensions:
            # Invertir el mapa para determinar el content-type
            for ctype, ext in self.allowed_map.items():
                if ext == extension:
                    return ctype, extension

        raise MediaValidationError(
            "Tipo de archivo no permitido",
            error_code="unsupported_media_type",
            status_code=415,
        )

    def _build_prefix(self, entity_type: str, entity_id: str) -> str:
        namespace = self.namespace_users if entity_type == "users" else self.namespace_patients
        return f"{namespace}/{entity_id}/"

    @staticmethod
    def _build_object_key(prefix: str, extension: str) -> str:
        unique = uuid.uuid4().hex
        return f"{prefix}profile-{unique}{extension}"
