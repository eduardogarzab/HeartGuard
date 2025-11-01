import sys
import types
import uuid
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
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

from common import auth as common_auth
from common.app_factory import create_app
from common.database import db
import models
import routes


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    common_auth._jwt_manager = None

    app = create_app("patient", routes.register_blueprint)
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _seed_catalogs(app):
    with app.app_context():
        sex = models.Sex(id=uuid.uuid4(), code="F", label="Femenino")
        risk_high = models.RiskLevel(id=uuid.uuid4(), code="high", label="Alto")
        risk_low = models.RiskLevel(id=uuid.uuid4(), code="low", label="Bajo")
        level_high = models.AlertLevel(id=uuid.uuid4(), code="high", label="Alta")
        level_critical = models.AlertLevel(id=uuid.uuid4(), code="critical", label="Crítica")
        status_open = models.AlertStatus(id=uuid.uuid4(), code="open", description="Abierta")
        status_ack = models.AlertStatus(id=uuid.uuid4(), code="ack", description="Reconocida")

        db.session.add_all([
            sex,
            risk_high,
            risk_low,
            level_high,
            level_critical,
            status_open,
            status_ack,
        ])
        db.session.commit()

        return {
            "sex_id": sex.id,
            "risk_high_id": risk_high.id,
            "risk_low_id": risk_low.id,
            "level_high_id": level_high.id,
            "level_critical_id": level_critical.id,
            "status_open_id": status_open.id,
            "status_ack_id": status_ack.id,
        }


def test_list_patients_returns_enriched_xml(app, client):
    catalogs = _seed_catalogs(app)
    org_id = uuid.uuid4()
    other_org = uuid.uuid4()

    with app.app_context():
        patient = models.Patient(
            id=uuid.uuid4(),
            org_id=org_id,
            person_name="Ana Gómez",
            birthdate=date.today(),
            sex_id=catalogs["sex_id"],
            risk_level_id=catalogs["risk_high_id"],
            created_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
        )
        other_patient = models.Patient(
            id=uuid.uuid4(),
            org_id=other_org,
            person_name="Luis Pérez",
            birthdate=date(1990, 5, 15),
            sex_id=catalogs["sex_id"],
            risk_level_id=catalogs["risk_low_id"],
            created_at=datetime(2024, 1, 5, tzinfo=timezone.utc),
        )

        alert_old = models.Alert(
            patient_id=patient.id,
            alert_level_id=catalogs["level_high_id"],
            status_id=catalogs["status_open_id"],
            created_at=datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc),
        )
        alert_recent = models.Alert(
            patient_id=patient.id,
            alert_level_id=catalogs["level_critical_id"],
            status_id=catalogs["status_ack_id"],
            created_at=datetime(2024, 3, 3, 9, 30, tzinfo=timezone.utc),
        )

        db.session.add_all([patient, other_patient, alert_old, alert_recent])
        db.session.commit()

    response = client.get(
        f"/patients?org_id={org_id}",
        headers={"Accept": "application/xml"},
    )

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/xml")

    xml_root = ET.fromstring(response.data)
    patients_nodes = xml_root.findall(".//patients/Patient")
    assert len(patients_nodes) == 1

    patient_node = patients_nodes[0]
    assert patient_node.findtext("name") == "Ana Gómez"
    assert patient_node.findtext("gender") == "Femenino"
    assert patient_node.findtext("risk_level") == "high"
    assert patient_node.findtext("org_id") == str(org_id)
    assert patient_node.findtext("admission_date") == "2024-01-10T00:00:00+00:00"
    assert patient_node.findtext("updated_at") == "2024-03-03T09:30:00+00:00"

    alerts_nodes = patient_node.findall("alerts/Alert")
    assert len(alerts_nodes) == 2
    assert alerts_nodes[0].findtext("severity") == "critical"
    assert alerts_nodes[0].findtext("status") == "ack"
    assert alerts_nodes[0].findtext("created_at") == "2024-03-03T09:30:00+00:00"
    assert alerts_nodes[1].findtext("severity") == "high"
    assert alerts_nodes[1].findtext("status") == "open"


def test_list_patients_requires_org_id(client):
    response = client.get("/patients", headers={"Accept": "application/json"})
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["status"] == "error"
    assert payload["error"]["id"] == "HG-PATIENT-ORG-ID-REQUIRED"
