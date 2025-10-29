"""Request payload parsing helpers."""

from __future__ import annotations

from typing import Any, Dict

from flask import Request, request

try:  # pragma: no cover - optional dependency for XML support
    import xmltodict
except Exception:  # pragma: no cover - handled gracefully
    xmltodict = None  # type: ignore


def parse_body(req: Request | None = None) -> Dict[str, Any]:
    req = req or request
    if req.is_json:
        return req.get_json() or {}

    if req.mimetype in {"application/xml", "text/xml"} and xmltodict:
        raw = req.get_data(cache=False, as_text=True)
        try:
            data = xmltodict.parse(raw)
        except Exception as exc:  # pragma: no cover - xml errors
            raise ValueError(f"XML inválido: {exc}") from exc
        if isinstance(data, dict):
            # Flatten common wrapper keys like response/payload
            for key in ("response", "payload", "signal"):
                if key in data and isinstance(data[key], dict):
                    return data[key]
        return data if isinstance(data, dict) else {}

    raise ValueError("Formato de contenido no soportado; use JSON")
