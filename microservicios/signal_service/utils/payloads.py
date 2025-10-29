"""Utilities for parsing and validating incoming payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from flask import Request, request
import xmltodict

from responses import err


class PayloadError(Exception):
    """Raised when the incoming payload is invalid."""


def _extract_xml_payload(raw_xml: str) -> Dict[str, Any]:
    parsed = xmltodict.parse(raw_xml)
    if not isinstance(parsed, dict):
        raise PayloadError("XML mal formado")
    # Try to locate the first dict with the data
    for value in parsed.values():
        if isinstance(value, dict):
            return dict(value)
    return dict(parsed)


def parse_request_payload(req: Optional[Request] = None) -> Dict[str, Any]:
    req = req or request
    if req.is_json:
        payload = req.get_json(silent=True)
        if not isinstance(payload, dict):
            raise PayloadError("JSON inválido o vacío")
        return payload

    content_type = req.headers.get("Content-Type", "")
    if "application/xml" in content_type:
        raw_data = req.data
        raw = raw_data.decode("utf-8") if isinstance(raw_data, (bytes, bytearray)) else str(raw_data)
        if not raw.strip():
            raise PayloadError("XML vacío")
        return _extract_xml_payload(raw)

    raise PayloadError("Formato de contenido no soportado")


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if value in (None, ""):
        return None
    try:
        cleaned = value.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        return datetime.fromisoformat(cleaned)
    except ValueError as exc:
        raise PayloadError("Fecha inválida, use formato ISO 8601") from exc


def validate_signal_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    required_fields = ["patient_id", "signal_type", "value", "unit"]
    missing = [field for field in required_fields if field not in data or data[field] in (None, "")]
    if missing:
        raise PayloadError(f"Campos requeridos faltantes: {', '.join(missing)}")

    try:
        value = float(data["value"])
    except (TypeError, ValueError) as exc:
        raise PayloadError("Valor numérico inválido para 'value'") from exc

    recorded_at = parse_iso_datetime(data.get("recorded_at"))

    return {
        "patient_id": str(data["patient_id"]),
        "signal_type": str(data["signal_type"]),
        "value": value,
        "unit": str(data["unit"]),
        "recorded_at": recorded_at,
    }


def handle_payload_error(exc: PayloadError):
    return err(str(exc), code="invalid_payload", status=400)
