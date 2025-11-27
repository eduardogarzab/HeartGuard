from __future__ import annotations

from media.utils.responses import error_response, fail_response, success_response


def test_success_response_json(flask_app):
    with flask_app.test_request_context(headers={"Accept": "application/json"}):
        resp = success_response(data={"foo": "bar"}, message="Hecho", status_code=201)
        assert resp.status_code == 201
        assert resp.mimetype == "application/json"
        payload = resp.get_json()
        assert payload["status"] == "success"
        assert payload["data"] == {"foo": "bar"}
        assert payload["message"] == "Hecho"
        assert "trace_id" in payload


def test_success_response_xml(flask_app):
    with flask_app.test_request_context(headers={"Accept": "application/xml"}):
        resp = success_response(data={"foo": "bar"}, message="Hecho")
        assert resp.status_code == 200
        assert resp.mimetype == "application/xml"
        body = resp.get_data(as_text=True)
        assert "<status>success</status>" in body
        assert "<foo>bar</foo>" in body


def test_error_response_structure(flask_app):
    with flask_app.test_request_context():
        resp = error_response(message="Falla", error_code="internal_error", status_code=500)
        assert resp.status_code == 500
        payload = resp.get_json()
        assert payload["status"] == "error"
        assert payload["error"] == {"code": "internal_error"}


def test_fail_response_structure(flask_app):
    with flask_app.test_request_context():
        resp = fail_response(message="Validación", error_code="validation_error", status_code=422)
        assert resp.status_code == 422
        payload = resp.get_json()
        assert payload["status"] == "fail"
        assert payload["error"] == {"code": "validation_error"}
