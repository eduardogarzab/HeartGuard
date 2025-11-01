"""Tests for registering users from organization invitations."""
from __future__ import annotations

import sys
import types
import uuid

import pytest

from datetime import datetime
from pathlib import Path

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
from common.database import db
import models
import routes


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setattr(models.UserOrgMembership, "user", None, raising=False)
    monkeypatch.setattr(models.UserOrgMembership, "role", None, raising=False)
    app = create_app("user", routes.register_blueprint)
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        status = models.UserStatus(id=uuid.uuid4(), code="active", label="Active")
        role = models.OrgRole(id=uuid.uuid4(), code="clinician", label="Clinician")
        db.session.add_all([status, role])
        db.session.commit()
        app.config["_test_role_id"] = role.id

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_register_from_invitation_creates_user(app, client, monkeypatch):
    org_id = uuid.uuid4()
    role_id = app.config["_test_role_id"]
    signed_token = "signed-token"
    invitation_payload = {
        "invitation": {
            "org_id": str(org_id),
            "org_role_id": str(role_id),
            "email": "invitee@example.com",
            "expires_at": datetime.utcnow().isoformat() + "Z",
        },
        "metadata": {
            "organization": {"id": str(org_id), "name": "Acme"},
            "suggested_role": {"id": str(role_id), "code": "clinician", "label": "Clinician"},
            "expires_at": datetime.utcnow().isoformat() + "Z",
        },
    }
    consumed_payload = {}

    monkeypatch.setattr(routes, "_fetch_invitation_details", lambda token: invitation_payload)
    monkeypatch.setattr(
        routes,
        "_consume_invitation_token",
        lambda token, payload: consumed_payload.update({"token": token, "payload": payload}),
    )

    xml_body = (
        "<UserRegistration>"
        f"<invite_token>{signed_token}</invite_token>"
        "<name>Jane Doe</name>"
        "<email>invitee@example.com</email>"
        "<password>s3cret!</password>"
        "</UserRegistration>"
    )

    response = client.post(
        "/users/register",
        data=xml_body,
        headers={"Content-Type": "application/xml", "Accept": "application/json"},
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["user"]["email"] == "invitee@example.com"
    assert consumed_payload["token"] == signed_token
    assert consumed_payload["payload"]["action"] == "accept"

    with app.app_context():
        user = models.User.query.filter_by(email="invitee@example.com").first()
        assert user is not None
        membership = models.UserOrgMembership.query.filter_by(user_id=user.id).first()
        assert membership is not None
        assert membership.org_id == org_id
        assert membership.org_role_id == role_id
