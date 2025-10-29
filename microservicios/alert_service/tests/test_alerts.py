import uuid
from typing import Dict

import jwt
import pytest

from microservicios.alert_service.app import create_app
from microservicios.alert_service.config import Config
from microservicios.alert_service.db import db
from microservicios.alert_service.models import Alert, AlertLevel, AlertStatus, AlertType


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    JWT_SECRET = "test-secret"


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def auth_context(app):
    org_id = uuid.uuid4()
    token = jwt.encode({"user_id": "user-1", "org_id": str(org_id)}, app.config["JWT_SECRET"], algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    return headers, org_id


@pytest.fixture
def client(app):
    return app.test_client()


def _seed_dependencies(org_id: uuid.UUID) -> Dict[str, uuid.UUID]:
    alert_type = AlertType(org_id=org_id, name="Vital", description="Vital alert")
    alert_level = AlertLevel(org_id=org_id, name="High", description="High risk")
    alert_status = AlertStatus(org_id=org_id, name="Open", description="Open alert")
    db.session.add_all([alert_type, alert_level, alert_status])
    db.session.commit()
    return {
        "alert_type_id": alert_type.id,
        "alert_level_id": alert_level.id,
        "alert_status_id": alert_status.id,
    }


def test_list_alerts_returns_empty(client, auth_context):
    headers, _ = auth_context
    response = client.get("/v1/alerts", headers=headers)
    assert response.status_code == 200
    assert response.get_json() == {"alerts": []}


def test_list_alerts_filters_by_org(client, auth_context):
    headers, org_id = auth_context
    other_org_id = uuid.uuid4()

    with client.application.app_context():
        ids = _seed_dependencies(org_id)
        other_ids = _seed_dependencies(other_org_id)

        alert = Alert(
            org_id=org_id,
            patient_id=uuid.uuid4(),
            alert_type_id=ids["alert_type_id"],
            alert_level_id=ids["alert_level_id"],
            alert_status_id=ids["alert_status_id"],
            message="Test alert",
        )
        db.session.add(alert)
        other_alert = Alert(
            org_id=other_org_id,
            patient_id=uuid.uuid4(),
            alert_type_id=other_ids["alert_type_id"],
            alert_level_id=other_ids["alert_level_id"],
            alert_status_id=other_ids["alert_status_id"],
            message="Should not appear",
        )
        db.session.add(other_alert)
        db.session.commit()

    response = client.get("/v1/alerts", headers=headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data["alerts"]) == 1
    assert data["alerts"][0]["message"] == "Test alert"


def test_list_alerts_returns_xml(client, auth_context):
    headers, _ = auth_context
    headers = {**headers, "Accept": "application/xml"}
    response = client.get("/v1/alerts", headers=headers)
    assert response.status_code == 200
    assert response.mimetype == "application/xml"
