from datetime import datetime, timedelta
from pathlib import Path
import sys
import types
import uuid

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
from common import auth as common_auth
from common.database import db
import models
import routes


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    common_auth._jwt_manager = None

    app = create_app("organization", routes.register_blueprint)
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        # Seed base organization and roles for tests
        org = models.Organization(id=uuid.uuid4(), code="acme", name="Acme Corp", created_at=datetime.utcnow())
        role = models.OrgRole(id=uuid.uuid4(), code="org_admin", label="Admin")
        db.session.add_all([org, role])
        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def issue_token(user_id: str, roles: list[str]):
    token_payload = {"sub": user_id, "roles": roles}
    manager = common_auth.get_jwt_manager()
    return manager.encode(token_payload)


def auth_headers(app, roles=("org_admin",)):
    user_id = str(uuid.uuid4())
    token = issue_token(user_id, list(roles))
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }, user_id


def test_create_invitation_success(app, client):
    headers, user_id = auth_headers(app)
    with app.app_context():
        org = models.Organization.query.first()
        role = models.OrgRole.query.first()

    payload = {
        "org_id": str(org.id),
        "email": "invitee@example.com",
        "role": role.code,
        "ttl_hours": 24,
    }

    response = client.post("/organization/invitations", json=payload, headers=headers)

    assert response.status_code == 201
    body = response.get_json()
    invitation = body["data"]["invitation"]
    assert invitation["org_id"] == str(org.id)
    assert invitation["email"] == "invitee@example.com"
    assert invitation["role"] == role.code
    assert invitation["status"] == "pending"
    assert invitation["token"]
    assert invitation["created_by"] == user_id
    link = body["data"]["link"]
    assert link["href"].startswith("/invite/")
    assert link["token"]
    metadata = body["data"]["metadata"]
    assert metadata["organization"]["id"] == str(org.id)
    assert metadata["suggested_role"]["id"] == str(role.id)
    assert metadata["expires_at"] == invitation["expires_at"]


def test_create_invitation_rejects_invalid_ttl(app, client):
    headers, _ = auth_headers(app)
    with app.app_context():
        org = models.Organization.query.first()
        role = models.OrgRole.query.first()

    payload = {
        "org_id": str(org.id),
        "role": role.code,
        "ttl_hours": 0,
    }

    response = client.post("/organization/invitations", json=payload, headers=headers)

    assert response.status_code == 400
    body = response.get_json()
    assert body["status"] == "error"
    assert body["error"]["id"] == "HG-ORG-INVITE-TTL-RANGE"


def test_list_invitations_filters_by_org(app, client):
    _, user_id = auth_headers(app)
    with app.app_context():
        org = models.Organization.query.first()
        role = models.OrgRole.query.first()
        org_id = str(org.id)

        other_org = models.Organization(id=uuid.uuid4(), code="beta", name="Beta", created_at=datetime.utcnow())
        db.session.add(other_org)

        now = datetime.utcnow()
        invite_org = models.OrgInvitation(
            organization=org,
            role=role,
            email="user1@example.com",
            token="token-1",
            expires_at=now + timedelta(hours=24),
            created_at=now,
            created_by=uuid.UUID(user_id),
        )
        invite_other = models.OrgInvitation(
            organization=other_org,
            role=role,
            email="user2@example.com",
            token="token-2",
            expires_at=now + timedelta(hours=24),
            created_at=now,
        )
        db.session.add_all([invite_org, invite_other])
        db.session.commit()

    response = client.get(f"/organization/invitations?org_id={org_id}", headers={"Accept": "application/json"})
    assert response.status_code == 200
    data = response.get_json()["data"]
    invitations = data["invitations"]
    assert len(invitations) == 1
    assert invitations[0]["org_id"] == org_id
    assert invitations[0]["email"] == "user1@example.com"


def test_cancel_invitation(app, client):
    headers, _ = auth_headers(app)
    with app.app_context():
        org = models.Organization.query.first()
        role = models.OrgRole.query.first()

        invitation = models.OrgInvitation(
            organization=org,
            role=role,
            email="user3@example.com",
            token="token-3",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            created_at=datetime.utcnow(),
        )
        db.session.add(invitation)
        db.session.commit()
        invitation_uuid = invitation.id
        invitation_id = str(invitation_uuid)

    response = client.post(
        f"/organization/invitations/{invitation_id}/cancel",
        headers=headers,
        json={},
    )
    assert response.status_code == 204

    with app.app_context():
        refreshed = db.session.get(models.OrgInvitation, invitation_uuid)
        assert refreshed.revoked_at is not None


def test_validate_invitation_returns_metadata(app, client):
    headers, _ = auth_headers(app)
    with app.app_context():
        org = models.Organization.query.first()
        role = models.OrgRole.query.first()

    payload = {
        "org_id": str(org.id),
        "role": role.code,
        "ttl_hours": 24,
    }

    response = client.post("/organization/invitations", json=payload, headers=headers)
    assert response.status_code == 201
    body = response.get_json()["data"]
    signed_token = body["link"]["token"]

    validation = client.get(f"/organization/invitations/{signed_token}/validate", headers={"Accept": "application/json"})
    assert validation.status_code == 200
    data = validation.get_json()["data"]
    assert data["invitation"]["org_id"] == str(org.id)
    assert data["metadata"]["suggested_role"]["code"] == role.code


def test_consume_invitation_marks_used(app, client):
    headers, _ = auth_headers(app)
    with app.app_context():
        org = models.Organization.query.first()
        role = models.OrgRole.query.first()

    create_resp = client.post(
        "/organization/invitations",
        json={"org_id": str(org.id), "role": role.code, "ttl_hours": 24},
        headers=headers,
    )
    signed_token = create_resp.get_json()["data"]["link"]["token"]

    consume_resp = client.post(
        f"/organization/invitations/{signed_token}/consume",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json={"action": "accept"},
    )
    assert consume_resp.status_code == 200
    used = consume_resp.get_json()["data"]["invitation"]["used_at"]
    assert used is not None


def test_consume_invitation_revoke(app, client):
    headers, _ = auth_headers(app)
    with app.app_context():
        org = models.Organization.query.first()
        role = models.OrgRole.query.first()

    create_resp = client.post(
        "/organization/invitations",
        json={"org_id": str(org.id), "role": role.code, "ttl_hours": 24},
        headers=headers,
    )
    signed_token = create_resp.get_json()["data"]["link"]["token"]

    revoke_resp = client.post(
        f"/organization/invitations/{signed_token}/consume",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json={"action": "revoke"},
    )
    assert revoke_resp.status_code == 200
    revoked = revoke_resp.get_json()["data"]["invitation"]["revoked_at"]
    assert revoked is not None
