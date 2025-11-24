"""XML utilities for realtime-data-generator service."""
from __future__ import annotations

from typing import Any
from xml.etree.ElementTree import Element, tostring

from flask import Response


def dict_to_xml(tag: str, data: Any) -> Element:
    """Convert a dictionary to an XML element."""
    elem = Element(tag)
    if isinstance(data, dict):
        for key, value in data.items():
            child = dict_to_xml(str(key), value)
            elem.append(child)
    elif isinstance(data, list):
        item_tag = _infer_item_tag(tag)
        for item in data:
            child = dict_to_xml(item_tag, item)
            elem.append(child)
    else:
        elem.text = "" if data is None else str(data)
    return elem


def xml_response(payload: dict[str, Any], *, status: int = 200, root: str = "response") -> Response:
    """Create an XML response from a dictionary."""
    elem = dict_to_xml(root, payload)
    return Response(
        tostring(elem, encoding="utf-8"),
        status=status,
        mimetype="application/xml",
    )


def xml_error_response(code: str, message: str, *, status: int = 400) -> Response:
    """Create an XML error response."""
    payload = {"error": {"code": code, "message": message}}
    return xml_response(payload, status=status)


def _infer_item_tag(parent_tag: str) -> str:
    """Infer the singular tag name from a plural parent tag."""
    base = parent_tag.rstrip().lower()
    if base.endswith("status"):
        return "status"
    if base.endswith("ies") and len(parent_tag) > 3:
        return parent_tag[:-3] + "y"
    if base.endswith("ses") and len(parent_tag) > 3:
        return parent_tag[:-2]
    if base.endswith("s") and len(parent_tag) > 1 and not base.endswith("us") and not base.endswith("ss"):
        return parent_tag[:-1]
    return "item"
