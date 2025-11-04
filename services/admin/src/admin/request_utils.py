"""Helpers for parsing HTTP request payloads."""
from __future__ import annotations

from typing import Any

import xmltodict
from flask import Request


def parse_payload(req: Request) -> dict[str, Any]:
    """Return a dict payload regardless of JSON or XML input."""
    data: dict[str, Any] | None = None

    if req.is_json:
        parsed = req.get_json(silent=True)
        if isinstance(parsed, dict):
            return parsed
        if parsed is not None:
            return {"value": parsed}

    if _looks_like_xml(req):
        xml_text = req.get_data(as_text=True)
        if xml_text.strip():
            try:
                parsed_xml = xmltodict.parse(xml_text)
                data = _normalize(parsed_xml)
            except Exception:
                data = None

    if data is None and req.form:
        data = {key: value for key, value in req.form.items()}

    return data or {}


def _looks_like_xml(req: Request) -> bool:
    mimetype = (req.mimetype or "").lower()
    if "xml" in mimetype:
        return True
    content_type = (req.headers.get("Content-Type") or "").lower()
    return "xml" in content_type


def _normalize(obj: Any) -> dict[str, Any]:
    if not isinstance(obj, dict):
        return {"value": obj}
    if len(obj) == 1:
        only_value = next(iter(obj.values()))
        if isinstance(only_value, dict):
            return {key: _normalize_value(value) for key, value in only_value.items()}
        return {next(iter(obj.keys())): _normalize_value(only_value)}
    return {key: _normalize_value(value) for key, value in obj.items()}


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _normalize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    return value
