"""Response utilities for the catalog service."""
from __future__ import annotations

from typing import Any

from dicttoxml import dicttoxml
from flask import Response, jsonify, request


def auto_response(data: Any, status_code: int = 200) -> Response:
    """Return JSON or XML depending on the request's Accept header."""

    if status_code == 204:
        return Response(status=status_code)

    accept_header = request.headers.get("Accept", "application/json")
    if "xml" in accept_header.lower():
        payload = data if isinstance(data, dict) else {"data": data}
        xml_body = dicttoxml(payload, custom_root="response", attr_type=False)
        return Response(xml_body, status=status_code, mimetype="application/xml")

    return jsonify(data), status_code
