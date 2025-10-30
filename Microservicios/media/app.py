import os

from flask import Flask, g, request

from .error_handler import register_error_handlers
from .gcs_client import delete_file, generate_signed_url, get_media, list_media, upload_file
from .middleware import get_metrics, init_app
from .utils_format import error_response, make_response

app = Flask(__name__)
init_app(app)
register_error_handlers(app)

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "application/pdf", "text/plain"}


@app.route("/health", methods=["GET"])
def health():
    return make_response({"status": "ok", "service": "media"})


@app.route("/ready", methods=["GET"])
def ready():
    status = 200
    details = {}
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path and os.path.exists(credentials_path):
        details["credentials"] = "found"
    else:
        details["credentials"] = "missing"
        status = 503
    try:
        from google.cloud import storage

        storage.Client().bucket(os.getenv("GCS_BUCKET", "heartguard-system"))
        details["gcs"] = "ok"
    except Exception as exc:  # pragma: no cover
        details["gcs"] = str(exc)
        status = 503
    return make_response({"status": "ready" if status == 200 else "degraded", "dependencies": details}, status=status)


@app.route("/metrics", methods=["GET"])
def metrics():
    return make_response(get_metrics(), root_tag="Metrics")


# POST /media/upload
# Multipart example (curl):
#   curl -F "file=@document.pdf" http://localhost:5004/media/upload
# Octet-stream example:
#   curl -H "Content-Type: application/octet-stream" -H "X-Filename: note.txt" -H "X-Mime-Type: text/plain" --data-binary @note.txt
# Response JSON/XML:
# {
#   "media": {
#     "media_id": "...",
#     "gcs_path": "user/uuid.pdf",
#     "mime_type": "application/pdf",
#     "size_bytes": 1024,
#     "signed_url": "https://...",
#     "created_at": "2025-10-29T18:07:00Z"
#   }
# }
@app.route("/media/upload", methods=["POST"])
def media_upload():
    user_id = g.get("user_id")
    if not user_id:
        return error_response(401, "Missing user identity")
    file_bytes = b""
    filename = None
    mime_type = None
    if request.files:
        file_storage = next(iter(request.files.values()))
        file_bytes = file_storage.read()
        filename = file_storage.filename
        mime_type = file_storage.mimetype or request.headers.get("X-Mime-Type")
    else:
        file_bytes = request.get_data()
        filename = request.headers.get("X-Filename", "upload.bin")
        mime_type = request.headers.get("X-Mime-Type", request.headers.get("Content-Type", "application/octet-stream"))
    if not mime_type:
        return error_response(400, "Unable to determine MIME type")
    if mime_type not in ALLOWED_MIME_TYPES:
        return error_response(415, f"MIME type {mime_type} not allowed")
    if len(file_bytes) > int(os.getenv("MAX_MEDIA_BYTES", "10485760")):
        return error_response(413, "Payload too large")
    metadata = upload_file(file_bytes, mime_type, user_id)
    metadata["filename"] = filename
    return make_response({"media": metadata}, status=201, root_tag="MediaUploadResponse")


# GET /media/file/<media_id>
# Response JSON/XML:
# {
#   "media": {
#     "media_id": "...",
#     "signed_url": "https://..."
#   }
# }
@app.route("/media/file/<media_id>", methods=["GET"])
def media_file(media_id: str):
    user_id = g.get("user_id")
    if not user_id:
        return error_response(401, "Missing user identity")
    meta = get_media(media_id)
    if not meta or meta.get("owner_user_id") != user_id and g.get("user_role") != "admin":
        return error_response(404, "Media not found")
    signed_url = generate_signed_url(meta["gcs_path"]) or meta.get("signed_url")
    return make_response({"media": {"media_id": media_id, "signed_url": signed_url}}, root_tag="MediaFile")


# GET /media/list
# Response JSON/XML:
# {
#   "media": [
#     {"media_id": "...", "mime_type": "application/pdf", ...}
#   ]
# }
@app.route("/media/list", methods=["GET"])
def media_list():
    user_id = g.get("user_id")
    if not user_id:
        return error_response(401, "Missing user identity")
    owner = None if g.get("user_role") in {"admin", "org_admin"} else user_id
    items = list_media(owner)
    return make_response({"media": items}, root_tag="MediaList")


# DELETE /media/file/<media_id>
# Response JSON/XML:
# {
#   "status": "deleted"
# }
@app.route("/media/file/<media_id>", methods=["DELETE"])
def media_delete(media_id: str):
    user_id = g.get("user_id")
    if not user_id:
        return error_response(401, "Missing user identity")
    meta = get_media(media_id)
    if not meta or (meta.get("owner_user_id") != user_id and g.get("user_role") != "admin"):
        return error_response(404, "Media not found")
    delete_file(meta["gcs_path"])
    return make_response({"status": "deleted"}, root_tag="MediaDeleteResponse")


if __name__ == "__main__":
    port = int(os.getenv("MEDIA_PORT", "5004"))
    app.run(host="0.0.0.0", port=port)
