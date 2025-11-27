"""Fixtures compartidas para pruebas del Media Service."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Asegura que existan las variables mínimas para instanciar la configuración."""
    monkeypatch.setenv("ID", "test-access-key")
    monkeypatch.setenv("KEY", "test-secret-key")
    monkeypatch.setenv("ORIGIN_ENDPOINT", "https://heartguard-bucket.atl1.digitaloceanspaces.com/")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("MEDIA_ALLOWED_CONTENT_TYPES", "image/jpeg,image/png")
    monkeypatch.setenv("DATABASE_URL", "postgres://test:test@localhost:5432/test")


@pytest.fixture
def flask_app():
    from media.app import create_app

    app = create_app()
    app.config.update(TESTING=True)
    yield app


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()
