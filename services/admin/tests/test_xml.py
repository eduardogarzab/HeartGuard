"""Test XML utilities."""
from __future__ import annotations

import xml.etree.ElementTree as ET

from admin.xml import dict_to_xml, xml_error_response, xml_response


def test_dict_to_xml_converts_simple_dict():
    """Should convert flat dict to XML element."""
    elem = dict_to_xml("root", {"key": "value", "number": 42})
    assert elem.tag == "root"
    assert elem.find("key").text == "value"
    assert elem.find("number").text == "42"


def test_dict_to_xml_converts_nested_dict():
    """Should handle nested dictionaries."""
    elem = dict_to_xml("root", {"outer": {"inner": "value"}})
    outer = elem.find("outer")
    assert outer is not None
    assert outer.find("inner").text == "value"


def test_dict_to_xml_converts_list():
    """Should convert list items."""
    elem = dict_to_xml("items", [{"id": 1}, {"id": 2}])
    children = list(elem)
    assert len(children) == 2
    assert children[0].find("id").text == "1"
    assert children[1].find("id").text == "2"


def test_xml_response_returns_flask_response():
    """Should return Response with XML mimetype."""
    response = xml_response({"status": "ok"})
    assert response.status_code == 200
    assert response.mimetype == "application/xml"

    root = ET.fromstring(response.data)
    assert root.tag == "response"
    assert root.find("status").text == "ok"


def test_xml_error_response_includes_error_structure():
    """Should wrap error details in error node."""
    response = xml_error_response("test_code", "Test message", status=400)
    assert response.status_code == 400

    root = ET.fromstring(response.data)
    error = root.find("error")
    assert error is not None
    assert error.find("code").text == "test_code"
    assert error.find("message").text == "Test message"


def test_xml_response_custom_root_tag():
    """Should allow custom root element name."""
    response = xml_response({"data": "test"}, root="custom")
    root = ET.fromstring(response.data)
    assert root.tag == "custom"
