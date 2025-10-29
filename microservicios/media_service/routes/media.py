from flask import Blueprint, g, request

from config import settings
from responses import ok, err
from utils.auth import token_required
from utils import storage
from utils.storage import StorageError

bp = Blueprint("media", __name__, url_prefix="/v1/media")


@bp.post("/<entity>")
@token_required
def upload_media(entity: str):
    uploaded = request.files.get("file")
    if not uploaded:
        return err("Archivo es requerido", code="file_missing", status=400)

    try:
        path = storage.upload(
            g.org_id,
            entity,
            uploaded.stream,
            uploaded.filename or "",
            uploaded.mimetype,
        )
        signed_url = storage.generate_signed_url(path)
    except StorageError as exc:
        return err(str(exc), code="invalid_entity", status=400)
    except Exception as exc:  # pragma: no cover - errores externos
        return err("Error al subir archivo", code="upload_error", status=500, details={"error": str(exc)})

    return ok(
        {
            "object_path": path,
            "signed_url": signed_url,
            "expires_in": settings.SIGNED_URL_TTL_SECONDS,
        }
    )


@bp.get("/<entity>/<object_name>")
@token_required
def retrieve_media(entity: str, object_name: str):
    try:
        path = storage.object_path(g.org_id, entity, object_name)
        storage.ensure_exists(path)
        signed_url = storage.generate_signed_url(path)
    except StorageError as exc:
        code = "not_found" if "no encontrado" in str(exc).lower() else "invalid_path"
        status = 404 if code == "not_found" else 400
        return err(str(exc), code=code, status=status)
    except Exception as exc:  # pragma: no cover
        return err("Error al generar URL", code="signed_url_error", status=500, details={"error": str(exc)})

    return ok(
        {
            "object_path": path,
            "signed_url": signed_url,
            "expires_in": settings.SIGNED_URL_TTL_SECONDS,
        }
    )


@bp.delete("/<entity>/<object_name>")
@token_required
def delete_media(entity: str, object_name: str):
    try:
        path = storage.object_path(g.org_id, entity, object_name)
        storage.delete(path)
    except StorageError as exc:
        code = "not_found" if "no encontrado" in str(exc).lower() else "invalid_path"
        status = 404 if code == "not_found" else 400
        return err(str(exc), code=code, status=status)
    except Exception as exc:  # pragma: no cover
        return err("Error al eliminar archivo", code="delete_error", status=500, details={"error": str(exc)})

    return ok({"deleted": True, "object_path": path})
