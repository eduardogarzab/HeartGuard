"""Registro de blueprints para el servicio de analytics."""
from __future__ import annotations

from flask import Flask

from .ingest import ingest_bp
from .reports import reports_bp


def register_blueprints(app: Flask) -> None:
    """Registra todos los blueprints públicos del servicio."""

    app.register_blueprint(reports_bp)
    app.register_blueprint(ingest_bp)


__all__ = ["register_blueprints", "reports_bp", "ingest_bp"]
