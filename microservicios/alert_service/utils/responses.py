from typing import Any, Dict

from dicttoxml import dicttoxml
from flask import Response, jsonify, request


def auto_response(data: Dict[str, Any], status_code: int = 200) -> Response:
    """Return a Flask response based on the Accept header."""
    accept_header = request.headers.get("Accept", "application/json")

    if "application/xml" in accept_header:
        xml = dicttoxml(data, custom_root="response", attr_type=False)
        return Response(xml, status=status_code, mimetype="application/xml")

    response = jsonify(data)
    response.status_code = status_code
    return response


__all__ = ["auto_response"]
