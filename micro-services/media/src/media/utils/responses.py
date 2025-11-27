"""Helpers para construir respuestas JSON/XML con trazabilidad."""
from __future__ import annotations

import uuid
from typing import Any
from xml.etree.ElementTree import Element, tostring

from flask import Response, g, jsonify, request

_JSON_MIMETYPE = "application/json"
_XML_MIMETYPE = "application/xml"


def _ensure_trace_id() -> str:
    trace_id = getattr(g, "trace_id", None)
    if not trace_id:
        trace_id = uuid.uuid4().hex
        g.trace_id = trace_id
    return trace_id


def _preferred_format() -> str:
    accept_mimetypes = request.accept_mimetypes
    if accept_mimetypes:
        json_q = accept_mimetypes[_JSON_MIMETYPE]
        xml_q = accept_mimetypes[_XML_MIMETYPE]
        if xml_q > json_q:
            return "xml"
        if json_q >= xml_q and json_q > 0:
            return "json"
    header = request.headers.get("Accept", "")
    if "application/xml" in header.lower() and "application/json" not in header.lower():
        return "xml"
    return "json"


def _dict_to_xml(tag: str, data: Any) -> Element:
    elem = Element(tag)
    if isinstance(data, dict):
        for key, value in data.items():
            child = _dict_to_xml(str(key), value)
            elem.append(child)
    elif isinstance(data, (list, tuple)):
        item_tag = _infer_item_tag(tag)
        for item in data:
            child = _dict_to_xml(item_tag, item)
            elem.append(child)
    else:
        elem.text = "" if data is None else str(data)
    return elem


def _infer_item_tag(parent_tag: str) -> str:
    base = parent_tag.lower()
    if base.endswith("s") and not base.endswith("ss"):
        return parent_tag[:-1]
    return "item"


def _render(payload: dict[str, Any], *, status_code: int) -> Response:
    fmt = _preferred_format()
    if fmt == "xml":
        root = _dict_to_xml("response", payload)
        xml_bytes = tostring(root, encoding="utf-8")
        response = Response(xml_bytes, mimetype=_XML_MIMETYPE)
        response.status_code = status_code
        return response

    response = jsonify(payload)
    response.status_code = status_code
    return response


def _build_envelope(*, status: str, message: str | None, data: Any, error: Any) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "data": data,
        "error": error,
        "trace_id": _ensure_trace_id(),
    }


def success_response(*, data: Any = None, message: str | None = "OK", status_code: int = 200) -> Response:
    payload = _build_envelope(status="success", message=message, data=data, error=None)
    return _render(payload, status_code=status_code)


def fail_response(*, message: str, error_code: str = "validation_error", data: Any = None, status_code: int = 400) -> Response:
    error = {"code": error_code}
    payload = _build_envelope(status="fail", message=message, data=data, error=error)
    return _render(payload, status_code=status_code)


def error_response(*, message: str, error_code: str = "internal_error", data: Any = None, status_code: int = 500) -> Response:
    error = {"code": error_code}
    payload = _build_envelope(status="error", message=message, data=data, error=error)
    return _render(payload, status_code=status_code)
