import json
import os
import logging
import html
import base64
import uuid
from datetime import datetime
from functools import wraps

import jwt
import xmltodict
from dicttoxml import dicttoxml
from flask import Flask, request, g, make_response
from dotenv import load_dotenv

from db import init_db, session_scope, MediaItem
from storage import upload_file, generate_signed_url, delete_blob

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=os.getenv("media_LOG_LEVEL", "INFO"))
logger = logging.getLogger("media-service")

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("media_ALLOWED_ORIGINS", "*").split(",")]
JWT_SECRET = os.getenv("auth_JWT_SECRET", os.getenv("gateway_JWT_SECRET", "super-secret"))
MAX_UPLOAD_MB = int(os.getenv("media_MAX_UPLOAD_MB", "5"))

init_db()

REQUEST_METRICS = {"requests": 0, "errors": 0, "latency_sum": 0.0}


def render(data, status=200, root="response"):
    accept = request.headers.get("Accept", "application/json")
    if "application/xml" in accept and "json" not in accept:
        xml_body = dicttoxml(data, custom_root=root, attr_type=False).decode("utf-8")
        resp = make_response(xml_body, status)
        resp.headers["Content-Type"] = "application/xml"
        return resp
    resp = make_response(json.dumps(data), status)
    resp.headers["Content-Type"] = "application/json"
    return resp


def error(code, message, status=400):
    return render({"error": {"code": code, "message": message}}, status=status, root="Error")


def parse_body():
    if request.method not in {"POST", "PUT", "PATCH"}:
        return {}
    content_type = request.headers.get("Content-Type", "application/json").split(";")[0]
    if "application/json" in content_type:
        data = request.get_json(silent=True)
        if data is None:
            raise ValueError("Invalid JSON body")
        return data
    if "application/xml" in content_type:
        try:
            parsed = xmltodict.parse(request.data or b"")
            root = next(iter(parsed.values())) if parsed else {}
            return dict(root)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("Invalid XML body") from exc
    raise ValueError("Unsupported Content-Type")


def sanitize(data):
    return {k: html.escape(v.strip()) if isinstance(v, str) else v for k, v in data.items()}


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error("MEDIA_401", "Authorization required", status=401)
        token = auth_header.split(" ", 1)[1]
        try:
            claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return error("MEDIA_401", "Token expired", status=401)
        except jwt.InvalidTokenError:
            return error("MEDIA_401", "Invalid token", status=401)
        g.claims = claims
        return f(*args, **kwargs)

    return decorated


def require_role(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.claims.get("role") not in roles:
                return error("MEDIA_403", "Forbidden", status=403)
            return f(*args, **kwargs)

        return decorated

    return wrapper


def serialize_item(item: MediaItem, include_signed=False):
    data = {
        "id": item.id,
        "file_name": item.file_name,
        "content_type": item.content_type,
        "size_bytes": item.size_bytes,
        "gcs_path": item.gcs_path,
        "owner_id": item.owner_id,
        "organization_id": item.organization_id,
        "created_at": item.created_at.isoformat() if item.created_at else None
    }
    if item.extra_metadata:
        try:
            data["metadata"] = json.loads(item.extra_metadata)
        except json.JSONDecodeError:
            data["metadata"] = {}
    if include_signed:
        try:
            data["signed_url"] = generate_signed_url(item.gcs_path)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to generate signed URL", extra={"error": str(exc)})
            data["signed_url"] = None
    return data


@app.before_request
def before_request():
    request.start_time = datetime.utcnow()


@app.after_request
def after_request(response):
    latency = (datetime.utcnow() - getattr(request, "start_time", datetime.utcnow())).total_seconds() * 1000
    REQUEST_METRICS["requests"] += 1
    REQUEST_METRICS["latency_sum"] += latency
    if response.status_code >= 400:
        REQUEST_METRICS["errors"] += 1
    origin = request.headers.get("Origin")
    if "*" in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
    elif origin and origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, X-Request-ID"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response


@app.route("/media/health", methods=["GET"])
def health():
    return render({"status": "ok", "service": "media"})


@app.route("/media/metrics", methods=["GET"])
def metrics():
    avg = REQUEST_METRICS["latency_sum"] / REQUEST_METRICS["requests"] if REQUEST_METRICS["requests"] else 0
    return render({
        "requests_total": REQUEST_METRICS["requests"],
        "errors_total": REQUEST_METRICS["errors"],
        "latency_avg_ms": round(avg, 2)
    })


@app.route("/media/upload", methods=["POST"])
@token_required
def upload():
    try:
        payload = sanitize(parse_body())
    except ValueError as exc:
        return error("MEDIA_415", str(exc), status=415)
    required = {"file_name", "content_type", "data_base64"}
    if not required.issubset(payload):
        return error("MEDIA_400", "Missing fields", status=400)
    data_base64 = payload["data_base64"]
    try:
        raw_bytes = base64.b64decode(data_base64)
    except Exception:  # noqa: BLE001
        return error("MEDIA_400", "Invalid base64 data", status=400)
    size_mb = len(raw_bytes) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        return error("MEDIA_413", f"File too large (>{MAX_UPLOAD_MB}MB)", status=413)
    owner_id = g.claims.get("sub")
    org_id = g.claims.get("org_id")
    path_prefix = f"org_{org_id}/user_{owner_id}"
    try:
        gcs_path = upload_file(payload["file_name"], data_base64, payload.get("content_type"), path_prefix)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to upload to GCS", extra={"error": str(exc)})
        return error("MEDIA_500", "Upload error", status=500)
    item_id = str(uuid.uuid4())
    metadata = payload.get("metadata")
    metadata_json = json.dumps(metadata) if isinstance(metadata, (dict, list)) else None
    with session_scope() as session:
        item = MediaItem(
            id=item_id,
            file_name=payload["file_name"],
            content_type=payload.get("content_type"),
            size_bytes=len(raw_bytes),
            gcs_path=gcs_path,
            owner_id=owner_id,
            organization_id=org_id,
            extra_metadata=metadata_json
        )
        session.add(item)
        session.flush()
        return render(serialize_item(item, include_signed=True), status=201, root="MediaItem")


@app.route("/media/items", methods=["GET"])
@token_required
def list_items():
    org_id = g.claims.get("org_id")
    owner_id = g.claims.get("sub")
    role = g.claims.get("role")
    with session_scope() as session:
        query = session.query(MediaItem).filter(MediaItem.organization_id == org_id)
        if role != "admin":
            query = query.filter(MediaItem.owner_id == owner_id)
        items = query.all()
        payload = {"items": [serialize_item(item, include_signed=False) for item in items]}
        return render(payload, root="MediaItems")


@app.route("/media/items/<item_id>/download", methods=["GET"])
@token_required
def download(item_id):
    with session_scope() as session:
        item = session.get(MediaItem, item_id)
        if not item:
            return error("MEDIA_404", "Not found", status=404)
        if g.claims.get("role") != "admin" and item.owner_id != g.claims.get("sub"):
            return error("MEDIA_403", "Forbidden", status=403)
        data = serialize_item(item, include_signed=True)
        return render(data, root="MediaItem")


@app.route("/media/items/<item_id>", methods=["DELETE"])
@token_required
@require_role("admin")
def delete_item(item_id):
    with session_scope() as session:
        item = session.get(MediaItem, item_id)
        if not item:
            return error("MEDIA_404", "Not found", status=404)
        gcs_path = item.gcs_path
        session.delete(item)
    try:
        delete_blob(gcs_path)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to delete blob", extra={"error": str(exc)})
    return render({"status": "deleted", "id": item_id}, root="DeleteResponse")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("media_PORT", 5004)))
