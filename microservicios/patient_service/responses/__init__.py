"""Utility helpers to format JSON or XML responses."""

from flask import jsonify, request, Response
from dicttoxml import dicttoxml


def dual_response(payload, status: int = 200):
    accept = request.headers.get("Accept", "")
    if "application/xml" in accept:
        xml = dicttoxml(payload, custom_root="response", attr_type=False)
        return Response(xml, status=status, mimetype="application/xml")
    return jsonify(payload), status


def ok(data=None, meta=None, status: int = 200):
    return dual_response({"status": "ok", "data": data or {}, "meta": meta or {}}, status)


def err(message, code: str = "bad_request", status: int = 400, details=None):
    return dual_response(
        {"status": "error", "code": code, "message": message, "details": details or {}},
        status,
    )
