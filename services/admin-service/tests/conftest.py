"""Pytest fixtures for admin service."""

from __future__ import annotations

import pytest

from src.admin_service.app import create_app


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        yield app


@pytest.fixture()
def client(app):
    return app.test_client()
