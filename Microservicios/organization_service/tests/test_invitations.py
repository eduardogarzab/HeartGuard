from datetime import datetime, timedelta
from pathlib import Path
import sys
from types import SimpleNamespace
import uuid

import pytest
from xml.etree import ElementTree as ET

BASE_DIR = Path(__file__).resolve().parents[2]
SERVICE_DIR = Path(__file__).resolve().parents[1]

for path in (BASE_DIR, SERVICE_DIR):
    if str(path) not in sys.path:
        sys.path.append(str(path))

if "flask_cors" not in sys.modules:
    sys.modules["flask_cors"] = SimpleNamespace(CORS=lambda app, **_: app)

if "xmltodict" not in sys.modules:
    class _XmlToDictModule:
        @staticmethod
        def parse(xml_string):
            root = ET.fromstring(xml_string)

            def _convert(element):
                children = list(element)
                if not children:
                    return element.text
                result = {}
                for child in children:
                    value = _convert(child)
                    existing = result.get(child.tag)
                    if existing is None:
                        result[child.tag] = value
                    else:
                        if not isinstance(existing, list):
                            result[child.tag] = [existing]
                        result[child.tag].append(value)
                return result

            return {root.tag: _convert(root)}

    sys.modules["xmltodict"] = _XmlToDictModule()

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


def _parse_xml_response(response):
    body = response.data.decode("utf-8")
    root = ET.fromstring(body)
    invitation = root.find("invitation")
    assert invitation is not None
    parsed: dict[str, str] = {}
    for child in invitation:
        parsed[child.tag] = child.text
    return parsed


def test_validate_invitation_pending(app, client):
    with app.app_context():
        org = models.Organization.query.first()
        role = models.OrgRole.query.first()

        invitation = models.OrgInvitation(
            organization=org,
            role=role,
            email="user4@example.com",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            created_at=datetime.utcnow(),
        )
        db.session.add(invitation)
        db.session.commit()
        token = invitation.token

    response = client.get(
        f"/organization/invitations/{token}/validate",
        headers={"Accept": "application/xml"},
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/xml")
    data = _parse_xml_response(response)
    assert data["token"] == token
    assert data["result"] == "valid"
    assert data["state"] == "pending"


def test_consume_invitation_flow(app, client):
    with app.app_context():
        org = models.Organization.query.first()
        role = models.OrgRole.query.first()

        invitation = models.OrgInvitation(
            organization=org,
            role=role,
            email="user5@example.com",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            created_at=datetime.utcnow(),
        )
        db.session.add(invitation)
        db.session.commit()
        token = invitation.token

    consume_response = client.post(
        f"/organization/invitations/{token}/consume",
        headers={"Accept": "application/xml"},
    )

    assert consume_response.status_code == 200
    consume_data = _parse_xml_response(consume_response)
    assert consume_data["token"] == token
    assert consume_data["result"] == "used"
    assert consume_data["state"] == "used"

    validate_response = client.get(
        f"/organization/invitations/{token}/validate",
        headers={"Accept": "application/xml"},
    )
    assert validate_response.status_code == 200
    validate_data = _parse_xml_response(validate_response)
    assert validate_data["result"] == "used"
    assert validate_data["state"] == "used"


def test_consume_revoked_invitation(app, client):
    with app.app_context():
        org = models.Organization.query.first()
        role = models.OrgRole.query.first()

        invitation = models.OrgInvitation(
            organization=org,
            role=role,
            email="user6@example.com",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            revoked_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        db.session.add(invitation)
        db.session.commit()
        token = invitation.token

    response = client.post(
        f"/organization/invitations/{token}/consume",
        headers={"Accept": "application/xml"},
    )

    assert response.status_code == 409
    data = _parse_xml_response(response)
    assert data["result"] == "revoked"
    assert data["state"] == "revoked"
    assert "reason" in data
