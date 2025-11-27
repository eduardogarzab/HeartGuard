"""Smoke test para healthcheck."""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://localhost:5432/heartguard")
os.environ.setdefault("SKIP_DB_INIT", "1")

from auth.app import create_app


def test_health_endpoint_returns_ok():
    app = create_app()
    app.config.update(TESTING=True)

    with app.test_client() as client:
        response = client.get("/health/")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["service"] == "heartguard-auth"
