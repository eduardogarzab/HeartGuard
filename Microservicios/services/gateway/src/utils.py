import json
import html
from flask import request, make_response


def dict_to_xml(tag_name, data):
    def _to_xml(name, value):
        if isinstance(value, dict):
            return f"<{name}>" + "".join(_to_xml(k, v) for k, v in value.items()) + f"</{name}>"
        if isinstance(value, list):
            return "".join(_to_xml(name, item) for item in value)
        if value is None:
            return f"<{name}/>"
        return f"<{name}>{html.escape(str(value))}</{name}>"

    return f"<{tag_name}>" + "".join(_to_xml(k, v) for k, v in data.items()) + f"</{tag_name}>"


def response_payload(payload, status=200):
    accept = request.headers.get("Accept", "application/json")
    if "application/xml" in accept and not accept.endswith("json"):
        xml_body = dict_to_xml("response", payload if isinstance(payload, dict) else {"result": payload})
        response = make_response(xml_body, status)
        response.headers["Content-Type"] = "application/xml"
        return response
    response = make_response(json.dumps(payload), status)
    response.headers["Content-Type"] = "application/json"
    return response


def error_response(code, message, status=400):
    body = {"error": {"code": code, "message": message}}
    return response_payload(body, status=status)
