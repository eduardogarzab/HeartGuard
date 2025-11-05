"""Test request payload parsing utilities."""
from __future__ import annotations

from unittest.mock import MagicMock

from admin.request_utils import parse_payload


def test_parse_payload_with_json():
    """Should parse JSON content-type."""
    request = MagicMock()
    request.is_json = True
    request.get_json.return_value = {"key": "value"}
    request.form = {}

    result = parse_payload(request)
    assert result == {"key": "value"}


def test_parse_payload_with_xml():
    """Should parse XML content-type."""
    request = MagicMock()
    request.is_json = False
    request.mimetype = "application/xml"
    request.get_data.return_value = """
        <request>
            <name>Test</name>
            <email>test@example.com</email>
        </request>
    """
    request.headers.get.return_value = "application/xml"
    request.form = {}

    result = parse_payload(request)
    assert "name" in result
    assert result["name"] == "Test"
    assert result["email"] == "test@example.com"


def test_parse_payload_with_form_data():
    """Should parse form data when no JSON or XML."""
    request = MagicMock()
    request.is_json = False
    request.mimetype = "application/x-www-form-urlencoded"
    request.headers.get.return_value = "application/x-www-form-urlencoded"
    request.form = {"key": "value", "number": "42"}

    result = parse_payload(request)
    assert result == {"key": "value", "number": "42"}


def test_parse_payload_empty_returns_dict():
    """Should return empty dict when no payload."""
    request = MagicMock()
    request.is_json = False
    request.mimetype = "text/plain"
    request.headers.get.return_value = "text/plain"
    request.get_json.return_value = None
    request.form = {}

    result = parse_payload(request)
    assert result == {}
