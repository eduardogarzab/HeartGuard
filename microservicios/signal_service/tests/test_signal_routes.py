import importlib
import sys
from functools import wraps
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, Dict

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
            def cursor(self):
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

        psycopg2_module.pool = pool_module
        sys.modules["psycopg2"] = psycopg2_module
        sys.modules["psycopg2.pool"] = pool_module

    if "dicttoxml" not in sys.modules:
        dicttoxml_module = ModuleType("dicttoxml")
        dicttoxml_module.dicttoxml = lambda payload, **kwargs: b"<response/>"
        sys.modules["dicttoxml"] = dicttoxml_module

    if "xmltodict" not in sys.modules:
        xmltodict_module = ModuleType("xmltodict")
        xmltodict_module.parse = lambda raw: {"signal": {}}
        sys.modules["xmltodict"] = xmltodict_module

    if "jwt" not in sys.modules:
        sys.modules["jwt"] = SimpleNamespace(
            ExpiredSignatureError=Exception,
            InvalidTokenError=Exception,
            decode=lambda *_, **__: {"identity": {"user_id": "user-123", "org_id": "org-456"}},
        )


def _patch_auth(monkeypatch):
    _ensure_fake_modules()

    import repository.memberships as memberships

    monkeypatch.setattr(memberships, "user_belongs_to_org", lambda *args, **kwargs: True)
    monkeypatch.setattr(memberships, "resolve_primary_org", lambda *args, **kwargs: "org-456")

    import utils.auth as auth_module

    def fake_token_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask import g

            g.user_id = "user-123"
            g.org_id = "org-456"
            return fn(*args, **kwargs)

        return wrapper

    monkeypatch.setattr(auth_module, "token_required", fake_token_required)
    monkeypatch.setattr(auth_module, "user_belongs_to_org", lambda *args, **kwargs: True)
    monkeypatch.setattr(auth_module, "resolve_primary_org", lambda *args, **kwargs: "org-456")


@pytest.fixture
def app_client(monkeypatch):
    _patch_auth(monkeypatch)

    import routes.signals as signals_routes

    signals_routes = importlib.reload(signals_routes)

    import app as signal_app

    signal_app = importlib.reload(signal_app)
    flask_app = signal_app.create_app()
    flask_app.testing = True

    with flask_app.test_client() as client:
        yield client


def test_register_signal_success(app_client, monkeypatch):
    from repository import signals as repo_signals

    expected_payload: Dict[str, Any] = {
        "id": "sig-001",
        "patient_id": "pat-123",
        "org_id": "org-456",
        "signal_type": "heart_rate",
        "value": 72.0,
        "unit": "bpm",
        "recorded_at": "2024-01-01T00:00:00Z",
        "created_by": "user-123",
        "created_at": "2024-01-01T00:00:01Z",
    }

    def fake_create_signal(**kwargs):
        assert kwargs["patient_id"] == "pat-123"
        assert kwargs["org_id"] == "org-456"
        assert kwargs["signal_type"] == "heart_rate"
        assert kwargs["unit"] == "bpm"
        assert kwargs["created_by"] == "user-123"
        return expected_payload

    monkeypatch.setattr(repo_signals, "create_signal", fake_create_signal)

    response = app_client.post(
        "/v1/signals",
        json={
            "patient_id": "pat-123",
            "signal_type": "heart_rate",
            "value": 72,
            "unit": "bpm",
            "recorded_at": "2024-01-01T00:00:00Z",
        },
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["data"]["id"] == "sig-001"


def test_register_signal_missing_fields(app_client):
    response = app_client.post(
        "/v1/signals",
        json={"patient_id": "pat-123"},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["code"] == "missing_fields"


def test_list_signals(app_client, monkeypatch):
    from repository import signals as repo_signals

    monkeypatch.setattr(
        repo_signals,
        "list_signals",
        lambda **kwargs: [
            {
                "id": "sig-001",
                "patient_id": "pat-123",
                "org_id": "org-456",
                "signal_type": "spo2",
                "value": 98.0,
                "unit": "%",
                "recorded_at": "2024-01-01T00:00:00Z",
                "created_by": "user-123",
                "created_at": "2024-01-01T00:00:01Z",
            }
        ],
    )

    response = app_client.get(
        "/v1/signals",
        query_string={"patient_id": "pat-123", "limit": 5},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["data"]["items"][0]["signal_type"] == "spo2"


def test_retrieve_signal_not_found(app_client, monkeypatch):
    from repository import signals as repo_signals

    monkeypatch.setattr(repo_signals, "get_signal", lambda *args, **kwargs: None)

    response = app_client.get(
        "/v1/signals/sig-404",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 404
    payload = response.get_json()
    assert payload["code"] == "signal_not_found"


def test_delete_signal_success(app_client, monkeypatch):
    from repository import signals as repo_signals

    monkeypatch.setattr(repo_signals, "delete_signal", lambda *args, **kwargs: True)

    response = app_client.delete(
        "/v1/signals/sig-001",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]["deleted"] is True
