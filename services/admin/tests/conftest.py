"""Test configuration and fixtures."""
from __future__ import annotations

import pytest

from admin.app import create_app


@pytest.fixture
def app():
    """Create application fixture for testing."""
    app = create_app()
    app.config.update(
        TESTING=True,
        DATABASE_URL="postgresql://test:test@localhost:5432/test_db",
        AUTH_SERVICE_URL="http://localhost:5001",
    )
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()
