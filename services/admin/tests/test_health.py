"""Test health endpoint."""
from __future__ import annotations

import xml.etree.ElementTree as ET


def test_healthcheck_returns_ok(client):
    """Health endpoint should return 200 with XML payload."""
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.mimetype == "application/xml"

    root = ET.fromstring(response.data)
    assert root.tag == "health"

    status = root.find("status")
    assert status is not None
    assert status.text == "ok"

    service = root.find("service")
    assert service is not None
    assert service.text == "heartguard-admin"


def test_healthcheck_includes_timestamp(client):
    """Health endpoint should include ISO timestamp."""
    response = client.get("/healthz")
    root = ET.fromstring(response.data)

    timestamp = root.find("timestamp")
    assert timestamp is not None
    assert timestamp.text is not None
    assert "T" in timestamp.text  # ISO format includes T separator
