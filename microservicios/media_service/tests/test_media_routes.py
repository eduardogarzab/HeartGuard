import importlib
import io
import sys
from pathlib import Path
from functools import wraps
from typing import Any, Dict
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

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

    if "jwt" not in sys.modules:
        sys.modules["jwt"] = SimpleNamespace(
            ExpiredSignatureError=Exception,
            InvalidTokenError=Exception,
            decode=lambda *_, **__: {
                "identity": {"user_id": "user-123", "org_id": "org-456"}
            },
        )

    if "google" not in sys.modules:
        sys.modules["google"] = ModuleType("google")

    google_module = sys.modules["google"]

    if not hasattr(google_module, "api_core"):
        api_core_module = ModuleType("api_core")
        exceptions_module = ModuleType("exceptions")
        exceptions_module.NotFound = Exception
        api_core_module.exceptions = exceptions_module
        sys.modules["google.api_core"] = api_core_module
        sys.modules["google.api_core.exceptions"] = exceptions_module
        google_module.api_core = api_core_module

    if not hasattr(google_module, "cloud"):
        cloud_module = ModuleType("cloud")
        sys.modules["google.cloud"] = cloud_module
        google_module.cloud = cloud_module
    else:
        cloud_module = sys.modules["google.cloud"]

    if "google.cloud.storage" not in sys.modules:
        storage_module = ModuleType("storage")

        class _FakeBlob:
            def __init__(self, name):
                self.name = name

            def upload_from_file(self, file_obj, content_type=None):
                return None

            def generate_signed_url(self, **kwargs):
                return "https://fake-signed-url"

            def delete(self):
                return None

            def exists(self):
                return True

        class _FakeBucket:
            def blob(self, name):
                return _FakeBlob(name)

        class _FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            def bucket(self, name):
                return _FakeBucket()

        storage_module.Client = _FakeClient
        cloud_module.storage = storage_module
        sys.modules["google.cloud.storage"] = storage_module


def _patch_token_required(monkeypatch):
    _ensure_fake_modules()
    from flask import g
    import utils.auth as auth_module

    def fake_token_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            g.user_id = "user-123"
            g.org_id = "org-456"
            return fn(*args, **kwargs)
        return wrapper

    monkeypatch.setattr(auth_module, "token_required", fake_token_required)


@pytest.fixture
def app_client(monkeypatch):
    _patch_token_required(monkeypatch)

    import routes.media as media_routes

    media_routes = importlib.reload(media_routes)

    import app as media_app

    media_app = importlib.reload(media_app)
    flask_app = media_app.create_app()
    flask_app.testing = True

    with flask_app.test_client() as client:
        yield client


def _mock_storage(monkeypatch, **overrides: Dict[str, Any]):
    import utils.storage as storage

    defaults = {
        "upload": MagicMock(return_value="org-456/patients/generated-object.png"),
        "generate_signed_url": MagicMock(return_value="https://fake-signed-url"),
        "object_path": storage.object_path,
        "ensure_exists": MagicMock(),
        "delete": MagicMock(),
    }
    defaults.update(overrides)

    for name, value in defaults.items():
        monkeypatch.setattr(storage, name, value)

    return defaults


def test_upload_media_success(app_client, monkeypatch):
    mocks = _mock_storage(monkeypatch)

    data = {
        "file": (io.BytesIO(b"fake image"), "scan.png"),
    }
    response = app_client.post(
        "/v1/media/patients",
        data=data,
        headers={"Authorization": "Bearer fake"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["data"]["object_path"].startswith("org-456/patients/")
    assert payload["data"]["signed_url"] == "https://fake-signed-url"
    mocks["upload"].assert_called_once()


def test_upload_media_missing_file(app_client, monkeypatch):
    _mock_storage(monkeypatch)

    response = app_client.post(
        "/v1/media/patients",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["code"] == "file_missing"


def test_retrieve_media_success(app_client, monkeypatch):
    mocks = _mock_storage(monkeypatch)

    response = app_client.get(
        "/v1/media/patients/object-123.png",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["data"]["signed_url"] == "https://fake-signed-url"
    mocks["ensure_exists"].assert_called_once()
    mocks["generate_signed_url"].assert_called_once()


def test_delete_media_success(app_client, monkeypatch):
    mocks = _mock_storage(monkeypatch)

    response = app_client.delete(
        "/v1/media/patients/object-123.png",
        headers={"Authorization": "Bearer fake"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["data"]["deleted"] is True
    mocks["delete"].assert_called_once()
