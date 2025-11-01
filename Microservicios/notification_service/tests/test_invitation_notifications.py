"""Tests for invitation notification workflows."""
from __future__ import annotations

import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[2]
SERVICE_DIR = Path(__file__).resolve().parents[1]

for path in (BASE_DIR, SERVICE_DIR):
    if str(path) not in sys.path:
        sys.path.append(str(path))

if "flask_cors" not in sys.modules:
    sys.modules["flask_cors"] = types.SimpleNamespace(CORS=lambda app, resources=None: None)

if "dicttoxml" not in sys.modules:
    import xml.etree.ElementTree as _ET

    def _append_node(parent: _ET.Element, key: str, value, item_func):
        if isinstance(value, dict):
            node = _ET.SubElement(parent, key)
            for sub_key, sub_value in value.items():
                _append_node(node, sub_key, sub_value, item_func)
        elif isinstance(value, list):
            container = _ET.SubElement(parent, key)
            for item in value:
                tag = item_func(item) if item_func else "item"
                child = _ET.SubElement(container, tag)
                if isinstance(item, dict):
                    for sub_key, sub_value in item.items():
                        _append_node(child, sub_key, sub_value, item_func)
                elif item is not None:
                    child.text = str(item)
                else:
                    child.text = ""
        else:
            node = _ET.SubElement(parent, key)
            node.text = "" if value is None else str(value)

    def _dicttoxml(data, custom_root="root", attr_type=False, item_func=None):
        root = _ET.Element(custom_root)
        if isinstance(data, dict):
            for key, value in data.items():
                _append_node(root, key, value, item_func)
        else:
            _append_node(root, "item", data, item_func)
        return _ET.tostring(root, encoding="utf-8")

    sys.modules["dicttoxml"] = types.SimpleNamespace(dicttoxml=_dicttoxml)

if "xmltodict" not in sys.modules:
    import xml.etree.ElementTree as _ET

    def _element_to_dict(element: _ET.Element):
        children = list(element)
        if not children:
            return element.text or ""
        result = {}
        for child in children:
            result[child.tag] = _element_to_dict(child)
        return result

    def _parse_xml(xml_string: str):
        root = _ET.fromstring(xml_string)
        return {root.tag: _element_to_dict(root)}

    sys.modules["xmltodict"] = types.SimpleNamespace(parse=_parse_xml)

from common.app_factory import create_app
import routes


@pytest.fixture()
def app(monkeypatch):
    app = create_app("notification", routes.register_blueprint)
    app.config["TESTING"] = True
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_send_invitation_notification_records_payload(client):
    xml_body = (
        "<InvitationNotification>"
        "<invite_token>signed-token</invite_token>"
        "<email>invitee@example.com</email>"
        "<signed_url>/invite/signed-token</signed_url>"
        "<expires_at>2099-01-01T00:00:00Z</expires_at>"
        "</InvitationNotification>"
    )

    response = client.post(
        "/notifications/invitations/send",
        data=xml_body,
        headers={"Content-Type": "application/xml", "Accept": "application/json"},
    )

    assert response.status_code == 202
    payload = response.get_json()["data"]["notification"]
    assert payload["invite_token"] == "signed-token"
    assert payload["email"] == "invitee@example.com"


def test_sweep_invitation_expirations_revokes(client, monkeypatch):
    token = "signed-token"
    expires = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    routes.INVITATION_NOTIFICATIONS[token] = {
        "invite_token": token,
        "email": "invitee@example.com",
        "signed_url": "/invite/signed-token",
        "expires_at": expires,
        "status": "sent",
    }
    revoked_tokens: list[str] = []

    monkeypatch.setattr(routes, "_consume_invitation_token", lambda signed: revoked_tokens.append(signed))

    response = client.post(
        "/notifications/invitations/sweep",
        data="<SweepRequest />",
        headers={"Content-Type": "application/xml", "Accept": "application/json"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert token in data["expired_tokens"]
    assert revoked_tokens == [token]
