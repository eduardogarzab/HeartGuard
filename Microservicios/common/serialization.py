"""Utilities for parsing requests and rendering responses in JSON/XML."""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, Tuple

from flask import Request, Response, current_app, jsonify, make_response, request
import dicttoxml
import xmltodict

from .errors import APIError

SUPPORTED_CONTENT_TYPES = {"application/json", "application/xml", "text/xml"}


def negotiate_content_type(req: Request) -> str:
    """Return the preferred response content type based on the Accept header."""
    accept_header = req.headers.get("Accept", "application/json")
    if "application/xml" in accept_header.lower():
        return "application/xml"
    return "application/json"


def _prepare_envelope(status: str, code: int, data: Any = None, meta: Dict[str, Any] | None = None,
                      error: Dict[str, Any] | None = None) -> Dict[str, Any]:
    envelope: Dict[str, Any] = {
        "status": status,
        "code": code,
    }
    if meta:
        envelope["meta"] = meta
    if error is not None:
        envelope["error"] = error
    if data is not None:
        envelope["data"] = data
    return envelope


def render_response(
    data: Any,
    status_code: int = 200,
    meta: Dict[str, Any] | None = None,
    xml_item_name: str | Callable[[Any], str] | None = None,
) -> Response:
    """Render a Flask response honoring the Accept header for JSON or XML."""
    envelope = _prepare_envelope("success", status_code, data=data, meta=meta)
    content_type = negotiate_content_type(request)

    if content_type == "application/xml":
        kwargs = {"custom_root": "response", "attr_type": False}
        if xml_item_name:
            if callable(xml_item_name):
                kwargs["item_func"] = xml_item_name
            else:
                kwargs["item_func"] = lambda _: xml_item_name
        xml_body = dicttoxml.dicttoxml(envelope, **kwargs)
        response = make_response(xml_body, status_code)
        response.headers["Content-Type"] = "application/xml"
        return response

    response = jsonify(envelope)
    response.status_code = status_code
    return response


def render_error(error: APIError) -> Response:
    """Render an error response using the negotiation rules."""
    payload = _prepare_envelope(
        status="error",
        code=error.status_code,
        error={
            "id": error.error_id,
            "message": error.message,
            "details": error.details,
        },
        meta=error.meta,
    )
    content_type = negotiate_content_type(request)
    if content_type == "application/xml":
        xml_body = dicttoxml.dicttoxml(payload, custom_root="response", attr_type=False)
        response = make_response(xml_body, error.status_code)
        response.headers["Content-Type"] = "application/xml"
        return response

    response = jsonify(payload)
    response.status_code = error.status_code
    return response


def parse_request_data(req: Request) -> Tuple[Dict[str, Any], str]:
    """Parse JSON or XML payloads from the incoming request."""
    if req.method in {"GET", "DELETE"}:
        return {}, "application/json"

    content_type = req.headers.get("Content-Type", "").split(";")[0].strip().lower()
    if not content_type:
        raise APIError("Missing Content-Type header", status_code=415, error_id="HG-UNSUPPORTED-TYPE")

    if content_type not in SUPPORTED_CONTENT_TYPES:
        raise APIError(
            f"Unsupported Content-Type '{content_type}'",
            status_code=415,
            error_id="HG-UNSUPPORTED-TYPE",
        )

    if not req.data:
        raise APIError("Request body is empty", status_code=400, error_id="HG-EMPTY-BODY")

    try:
        if content_type == "application/json":
            return json.loads(req.data.decode("utf-8")), content_type
        # XML branch
        parsed = xmltodict.parse(req.data)
        # normalize to dict by removing possible root wrappers
        if isinstance(parsed, dict) and len(parsed) == 1:
            parsed = next(iter(parsed.values()))
        return json.loads(json.dumps(parsed)), content_type
    except Exception as exc:  # pragma: no cover - defensive
        current_app.logger.exception("Failed to parse request payload", exc_info=exc)
        raise APIError("Invalid request payload", status_code=400, error_id="HG-BAD-PAYLOAD") from exc
