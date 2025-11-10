"""Proxy de rutas hacia el Media Service."""
from __future__ import annotations

from http import HTTPStatus
from typing import Iterable

from flask import Blueprint, Response, current_app, jsonify, request

from ..services.media_client import MediaClient, MediaClientError

bp = Blueprint("media", __name__, url_prefix="/media")


def _get_media_client() -> MediaClient:
    return MediaClient(
        base_url=current_app.config["MEDIA_SERVICE_URL"],
        timeout=current_app.config["GATEWAY_SERVICE_TIMEOUT"],
    )


def _forward_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    for name in ("Authorization", "Content-Type", "Accept", "X-Trace-ID", "X-Trace-Id"):
        value = request.headers.get(name)
        if value:
            headers[name] = value
    return headers


def _filter_response_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    excluded = {"content-length", "transfer-encoding", "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "upgrade"}
    return {key: value for key, value in headers if key.lower() not in excluded}


def _proxy_media(path: str, method: str | None = None) -> Response:
    method = method or request.method
    headers = _forward_headers()

    json_payload = None
    data_payload = None
    files_payload = None
    
    if method in {"POST", "PUT", "PATCH"}:
        if request.is_json:
            json_payload = request.get_json(silent=True)
        elif request.files:
            # For multipart/form-data with files
            files_payload = {}
            for key, file in request.files.items():
                files_payload[key] = (file.filename, file.stream, file.content_type)
        else:
            data_payload = request.get_data() if request.data else None

    params = list(request.args.items(multi=True)) if request.args else None

    try:
        client = _get_media_client()
        upstream = client.proxy_request(
            method=method,
            path=path,
            headers=headers or None,
            json=json_payload,
            data=data_payload,
            files=files_payload,
            params=params,
        )
        filtered_headers = _filter_response_headers(upstream.headers.items())
        return Response(upstream.content, status=upstream.status_code, headers=filtered_headers)
    except MediaClientError as exc:
        return jsonify({"error": exc.error, "message": exc.message}), exc.status_code
    except Exception as exc:  # pragma: no cover - defensivo
        current_app.logger.error("Error en proxy media: %s", exc, exc_info=True)
        return jsonify({"error": "internal_error", "message": "Error interno del gateway"}), HTTPStatus.INTERNAL_SERVER_ERROR


@bp.route("/health", methods=["GET"])
def media_health() -> Response:
    return _proxy_media("/health", method="GET")


@bp.route("/users/<string:user_id>/photo", methods=["POST", "PUT", "DELETE"])
def proxy_user_photo(user_id: str) -> Response:
    return _proxy_media(f"/media/users/{user_id}/photo")


@bp.route("/patients/<string:patient_id>/photo", methods=["POST", "PUT", "DELETE"])
def proxy_patient_photo(patient_id: str) -> Response:
    return _proxy_media(f"/media/patients/{patient_id}/photo")
