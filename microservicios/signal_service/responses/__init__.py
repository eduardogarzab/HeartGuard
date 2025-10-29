"""Unified response helpers for the signal service."""

from flask import Response, jsonify, request
from dicttoxml import dicttoxml


def dual_response(payload: dict, status: int = 200):
    if "application/xml" in request.headers.get("Accept", ""):
        xml = dicttoxml(payload, custom_root="response", attr_type=False)
        return Response(xml, status=status, mimetype="application/xml")
    return jsonify(payload), status


def ok(data=None, meta=None, status: int = 200):
    return dual_response({"status": "ok", "data": data or {}, "meta": meta or {}}, status)


def err(message, code="bad_request", status: int = 400, details=None):
    return dual_response(
        {"status": "error", "code": code, "message": message, "details": details or {}},
        status,
    )
