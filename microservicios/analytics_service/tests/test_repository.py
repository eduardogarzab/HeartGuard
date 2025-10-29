"""Pruebas unitarias del repositorio de analytics."""
from __future__ import annotations

from typing import Any, Dict

import pytest
from sqlalchemy.exc import SQLAlchemyError

import repository
from repository import RepositoryError


def test_log_heartbeat_requires_configured_engine(monkeypatch):
    """Si no hay engine configurado debe lanzarse ``RepositoryError``."""

    monkeypatch.setattr(repository, "db_engine", None)

    with pytest.raises(RepositoryError):
        repository.log_heartbeat("gateway", "ok")


def test_log_heartbeat_executes_upsert(monkeypatch):
    """El método debe abrir una sesión y confirmar los cambios."""

    events: Dict[str, Any] = {}

    class DummySession:
        def __init__(self, engine):
            events["engine"] = engine

        def __enter__(self):
            events["entered"] = True
            return self

        def __exit__(self, exc_type, exc, tb):
            events["exited"] = True

        def execute(self, statement):
            events["statement"] = statement

        def commit(self):
            events["committed"] = True

    dummy_engine = object()

    monkeypatch.setattr(repository, "db_engine", dummy_engine)
    monkeypatch.setattr(repository, "Session", lambda engine: DummySession(engine))

    repository.log_heartbeat("gateway", "ok", details={"latency": 10})

    assert events["engine"] is dummy_engine
    assert events["entered"] is True
    assert events["committed"] is True
    assert events["exited"] is True
    assert events["statement"].table.name == "service_health"


def test_log_heartbeat_wraps_sqlalchemy_errors(monkeypatch):
    """Errores de SQLAlchemy deben envolverse como ``RepositoryError``."""

    class DummySession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def execute(self, statement):  # pragma: no cover - ejecutado indirectamente
            class DummySQLException(SQLAlchemyError):
                pass

            raise DummySQLException("db error")

        def commit(self):
            pass

    dummy_engine = object()

    monkeypatch.setattr(repository, "db_engine", dummy_engine)
    monkeypatch.setattr(repository, "Session", lambda engine: DummySession())

    with pytest.raises(RepositoryError):
        repository.log_heartbeat("gateway", "ok")


def test_get_overview_metrics_requires_audit_engine(monkeypatch):
    """Sin motor de auditoría configurado debe producir error."""

    monkeypatch.setattr(repository, "audit_db_engine", None)

    with pytest.raises(RepositoryError):
        repository.get_overview_metrics(org_id=None, include_all=True)


def test_get_overview_metrics_parses_results(monkeypatch):
    """El resultado debe normalizar ``timeline`` y ``entity_counts``."""

    captured: Dict[str, Any] = {}

    class DummyCursor:
        def __init__(self, row: Dict[str, Any]):
            self._row = row

        def first(self):
            return self._row

    class DummyResult:
        def __init__(self, row: Dict[str, Any]):
            self._row = row

        def mappings(self):
            return DummyCursor(self._row)

    class DummyConnection:
        def __init__(self, row: Dict[str, Any]):
            self._row = row

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def execute(self, query, params):
            captured["params"] = params
            return DummyResult(self._row)

    class DummyEngine:
        def __init__(self, row: Dict[str, Any]):
            self._row = row

        def connect(self):
            return DummyConnection(self._row)

    row = {
        "total_events": 7,
        "active_users_30d": 3,
        "timeline": '[{"day": "2024-01-01", "action": "login", "total": 5}]',
        "entity_counts": '{"user": 4}',
    }

    monkeypatch.setattr(repository, "audit_db_engine", DummyEngine(row))

    result = repository.get_overview_metrics(org_id=99, include_all=False)

    assert captured["params"] == {"org_id": 99}
    assert result["total_events"] == 7
    assert result["timeline"][0]["action"] == "login"
    assert result["entity_counts"]["user"] == 4


def test_get_overview_metrics_returns_defaults(monkeypatch):
    """Cuando no hay filas se deben devolver valores por defecto."""

    class DummyCursor:
        def first(self):
            return None

    class DummyResult:
        def mappings(self):
            return DummyCursor()

    class DummyConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def execute(self, query, params):
            return DummyResult()

    class DummyEngine:
        def connect(self):
            return DummyConnection()

    monkeypatch.setattr(repository, "audit_db_engine", DummyEngine())

    result = repository.get_overview_metrics(org_id=None, include_all=True)

    assert result == {
        "total_events": 0,
        "active_users_30d": 0,
        "timeline": [],
        "entity_counts": {},
    }
