import json
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from dicttoxml import dicttoxml
from flask import Response, g, request
import xmltodict

DEFAULT_ROOT = "response"


def _negotiate() -> str:
    accept = request.headers.get("Accept", "application/json")
    if "application/xml" in accept.lower():
        return "xml"
    return "json"


def parse_body() -> Tuple[Dict[str, Any], str]:
    content_type = request.headers.get("Content-Type", "application/json").lower()
    raw = request.get_data(cache=False) or b"{}"
    if "application/json" in content_type:
        try:
            return json.loads(raw.decode("utf-8")), "json"
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON payload: {exc}")
    if "application/xml" in content_type:
        try:
            parsed = xmltodict.parse(raw)
            if isinstance(parsed, dict) and len(parsed) == 1:
                parsed = next(iter(parsed.values()))
            return dict(parsed), "xml"
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid XML payload: {exc}")
    raise ValueError("Unsupported Content-Type. Use application/json or application/xml")


def _to_xml(data: Any, root_tag: str) -> bytes:
    if not isinstance(data, dict):
        data = {"data": data}
    xml_bytes = dicttoxml(data, custom_root=root_tag, attr_type=False)
    return xml_bytes


def make_response(data: Dict[str, Any], status: int = 200, root_tag: str = DEFAULT_ROOT) -> Response:
    fmt = _negotiate()
    if fmt == "xml":
        payload = _to_xml(data, root_tag=root_tag)
        return Response(payload, status=status, mimetype="application/xml")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return Response(payload, status=status, mimetype="application/json")


def error_response(code: int, message: str, details: Any = None) -> Response:
    request_id = getattr(g, "request_id", None)
    body = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }
    if details is not None:
        body["error"]["details"] = details
    return make_response(body, status=code, root_tag="Error")
