"""Pruebas de los blueprints del servicio de analytics."""
from __future__ import annotations

import os
from typing import Dict

import pytest

# Aseguramos que la clave de ingesta exista antes de importar la app.
os.environ.setdefault("INGEST_API_KEY", "test-key")
os.environ.setdefault("FLASK_ENV", "testing")

from app import app  # noqa: E402
import repository  # noqa: E402
from repository import RepositoryError  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    """Cliente de pruebas con claves y repositorios simulados."""

    monkeypatch.setattr("config.settings.INGEST_API_KEY", "test-key", raising=False)
    return app.test_client()


def test_ingest_requires_internal_api_key(client):
    """Sin cabecera de autenticación interna se debe rechazar la petición."""

    response = client.post(
        "/v1/metrics/heartbeat",
        json={"service_name": "gateway", "status": "ok"},
    )

    assert response.status_code == 401
    body: Dict[str, str] = response.get_json()
    assert body["status"] == "error"
    assert "Unauthorized" in body["message"]


def test_ingest_valid_payload_invokes_repository(monkeypatch, client):
    """Un heartbeat válido debe delegar en ``repository.log_heartbeat``."""

    captured = {}

    def fake_log(service_name, status, *, details):
        captured["service_name"] = service_name
        captured["status"] = status
        captured["details"] = details

    monkeypatch.setattr(repository, "log_heartbeat", fake_log)

    response = client.post(
        "/v1/metrics/heartbeat",
        headers={"X-Internal-Key": "test-key"},
        json={
            "service_name": "gateway",
            "status": "ok",
            "details": {"latency_ms": 120},
        },
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert captured == {
        "service_name": "gateway",
        "status": "ok",
        "details": {"latency_ms": 120},
    }


def test_ingest_handles_repository_errors(monkeypatch, client):
    """Errores del repositorio deben traducirse en respuestas 500."""

    def boom(*_, **__):
        raise RepositoryError("boom")

    monkeypatch.setattr(repository, "log_heartbeat", boom)

    response = client.post(
        "/v1/metrics/heartbeat",
        headers={"X-Internal-Key": "test-key"},
        json={"service_name": "media", "status": "ok"},
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body["status"] == "error"
    assert "No se pudo registrar el heartbeat" in body["message"]


def test_overview_requires_admin_role(client):
    """Solo roles admin o superadmin deben acceder al reporte."""

    response = client.get(
        "/v1/metrics/overview",
        headers={"X-Role": "viewer"},
    )

    assert response.status_code == 403
    body = response.get_json()
    assert body["status"] == "error"


def test_overview_requires_org_for_admin(client):
    """Los administradores deben proporcionar un identificador de organización."""

    response = client.get(
        "/v1/metrics/overview",
        headers={"X-Role": "admin"},
    )

    assert response.status_code == 400
    body = response.get_json()
    assert "Organización requerida" in body["message"]


def test_overview_returns_metrics_for_admin_with_org(monkeypatch, client):
    """Se deben recuperar métricas filtradas por organización para admins."""

    expected = {"total_events": 5, "timeline": [], "entity_counts": {}, "active_users_30d": 2}

    def fake_metrics(*, org_id, include_all):
        assert org_id == 42
        assert include_all is False
        return expected

    monkeypatch.setattr(repository, "get_overview_metrics", fake_metrics)

    response = client.get(
        "/v1/metrics/overview",
        headers={"X-Role": "admin", "X-Org-Id": "42"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["data"]["metrics"] == expected


def test_overview_returns_metrics_for_superadmin(monkeypatch, client):
    """Los superadmins deben consultar métricas globales."""

    expected = {"total_events": 10, "timeline": [], "entity_counts": {}, "active_users_30d": 4}

    def fake_metrics(*, org_id, include_all):
        assert org_id is None
        assert include_all is True
        return expected

    monkeypatch.setattr(repository, "get_overview_metrics", fake_metrics)

    response = client.get(
        "/v1/metrics/overview",
        headers={"X-Role": "superadmin"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["data"]["metrics"] == expected


def test_overview_handles_repository_errors(monkeypatch, client):
    """Errores del repositorio deben producir una respuesta 500 controlada."""

    def boom(*_, **__):
        raise RepositoryError("db down")

    monkeypatch.setattr(repository, "get_overview_metrics", boom)

    response = client.get(
        "/v1/metrics/overview",
        headers={"X-Role": "superadmin"},
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body["status"] == "error"
    assert "No fue posible obtener las métricas" in body["message"]
