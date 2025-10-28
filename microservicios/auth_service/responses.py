from flask import request, jsonify, Response
from dicttoxml import dicttoxml

def dual_response(payload: dict, status: int = 200):
    accept = request.headers.get("Accept", "")
    if "application/xml" in accept:
        xml = dicttoxml(payload, custom_root="response", attr_type=False)
        return Response(xml, status=status, mimetype="application/xml")
    return jsonify(payload), status

def ok(data=None, meta=None, status=200):
    return dual_response({"status": "ok", "data": data or {}, "meta": meta or {}}, status)

def err(message: str, code="bad_request", status=400, details=None):
    return dual_response({"status": "error", "code": code, "message": message, "details": details or {}}, status)
