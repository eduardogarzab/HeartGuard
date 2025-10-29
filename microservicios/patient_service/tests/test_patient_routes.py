import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from functools import wraps

import pytest

SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))


def _ensure_fake_modules():
    if "dotenv" not in sys.modules:
        dotenv_module = ModuleType("dotenv")
        dotenv_module.load_dotenv = lambda *_, **__: None
        sys.modules["dotenv"] = dotenv_module

    if "psycopg2" not in sys.modules:
        psycopg2_module = ModuleType("psycopg2")

        class _FakeCursor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

            def execute(self, *args, **kwargs):
                return None

            def fetchone(self):
                return None

            def fetchall(self):
                return []

        class _FakeConnection:
            def cursor(self, *args, **kwargs):
                return _FakeCursor()

        class _FakePool:
            def __init__(self, *args, **kwargs):
                pass

            def getconn(self):
                return _FakeConnection()

            def putconn(self, conn):
                return None

        pool_module = ModuleType("pool")
        pool_module.SimpleConnectionPool = _FakePool

        extras_module = ModuleType("extras")

        class _FakeRealDictCursor:
            pass

        extras_module.RealDictCursor = _FakeRealDictCursor

        psycopg2_module.pool = pool_module
        psycopg2_module.extras = extras_module

        sys.modules["psycopg2"] = psycopg2_module
        sys.modules["psycopg2.pool"] = pool_module
        sys.modules["psycopg2.extras"] = extras_module

    if "flask_jwt_extended" not in sys.modules:
        jwt_module = ModuleType("flask_jwt_extended")
        jwt_module.CURRENT_IDENTITY = {"user_id": "user-123", "org_id": "org-456"}

        class JWTManager:
            def __init__(self, app=None):
                self.app = app

            def invalid_token_loader(self, fn):
                return fn

            def unauthorized_loader(self, fn):
                return fn

            def expired_token_loader(self, fn):
                return fn

        def get_jwt_identity():
            return jwt_module.CURRENT_IDENTITY

        def jwt_required(*decorator_args, **decorator_kwargs):
            def decorator(fn):
                @wraps(fn)
                def wrapper(*args, **kwargs):
                    return fn(*args, **kwargs)

                return wrapper

            return decorator

        jwt_module.JWTManager = JWTManager
        jwt_module.get_jwt_identity = get_jwt_identity
        jwt_module.jwt_required = jwt_required

        sys.modules["flask_jwt_extended"] = jwt_module


@pytest.fixture
def app_client(monkeypatch):
    _ensure_fake_modules()

    jwt_module = sys.modules["flask_jwt_extended"]
    jwt_module.CURRENT_IDENTITY = {"user_id": "user-123", "org_id": "org-456"}

    import routes.patients as patients_routes

    patients_routes = importlib.reload(patients_routes)

    import app as patient_app

    patient_app = importlib.reload(patient_app)
    flask_app = patient_app.create_app()
    flask_app.testing = True

    with flask_app.test_client() as client:
        yield client, patients_routes


def test_create_patient_success(app_client, monkeypatch):
    client, routes = app_client

    monkeypatch.setattr(routes, "user_belongs_to_org", lambda user_id, org_id: True)

    def fake_create_patient(org_id, person_name, birthdate, sex_id, risk_level_id, profile_photo_url):
        assert org_id == "org-456"
        assert person_name == "Jane Doe"
        assert birthdate.year == 1980
        return "patient-999"

    monkeypatch.setattr(routes, "create_patient", fake_create_patient)

    monkeypatch.setattr(
        routes,
        "get_patient",
        lambda patient_id: {
            "id": patient_id,
            "org_id": "org-456",
            "person_name": "Jane Doe",
            "birthdate": "1980-02-10",
            "profile_photo_url": None,
        },
    )

    response = client.post(
        "/v1/patients",
        json={
            "org_id": "org-456",
            "person_name": "Jane Doe",
            "birthdate": "1980-02-10",
            "sex_id": "sex-f",
            "risk_level_id": "risk-low",
        },
        headers={"Authorization": "Bearer test"},
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["data"]["patient"]["id"] == "patient-999"
    assert payload["data"]["patient"]["person_name"] == "Jane Doe"


def test_list_patients_includes_signed_url(app_client, monkeypatch):
    client, routes = app_client

    monkeypatch.setattr(routes, "user_belongs_to_org", lambda user_id, org_id: True)
    monkeypatch.setattr(
        routes,
        "list_patients",
        lambda org_id, limit=50, offset=0: [
            {
                "id": "patient-1",
                "org_id": org_id,
                "person_name": "John Doe",
                "profile_photo_url": "org-456/patients/avatar.png",
            }
        ],
    )

    monkeypatch.setattr(
        routes,
        "request_signed_photo",
        lambda path, auth_header, org_id: SimpleNamespace(url="https://signed", expires_in=600),
    )

    response = client.get(
        "/v1/patients?limit=1&offset=0&include_photo_signed_url=true",
        headers={"Authorization": "Bearer test"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    patients = payload["data"]["patients"]
    assert len(patients) == 1
    assert patients[0]["profile_photo_signed_url"] == "https://signed"
    assert patients[0]["profile_photo_expires_in"] == 600
    assert payload["meta"]["pagination"]["limit"] == 1


def test_update_patient_requires_non_empty_name(app_client, monkeypatch):
    client, routes = app_client

    monkeypatch.setattr(routes, "user_belongs_to_org", lambda user_id, org_id: True)
    monkeypatch.setattr(
        routes,
        "get_patient",
        lambda patient_id: {
            "id": patient_id,
            "org_id": "org-456",
            "person_name": "Current Name",
        },
    )

    response = client.patch(
        "/v1/patients/patient-1",
        json={"person_name": "   "},
        headers={"Authorization": "Bearer test"},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["status"] == "error"
    assert payload["code"] == "name_required"


def test_delete_patient_success(app_client, monkeypatch):
    client, routes = app_client

    monkeypatch.setattr(routes, "user_belongs_to_org", lambda user_id, org_id: True)
    monkeypatch.setattr(
        routes,
        "get_patient",
        lambda patient_id: {
            "id": patient_id,
            "org_id": "org-456",
            "person_name": "Current Name",
        },
    )
    monkeypatch.setattr(routes, "delete_patient", lambda patient_id: True)

    response = client.delete(
        "/v1/patients/patient-1",
        headers={"Authorization": "Bearer test"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["data"]["deleted"] is True
    assert payload["data"]["patient_id"] == "patient-1"
