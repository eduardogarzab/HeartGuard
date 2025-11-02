"""Registro de blueprints del gateway."""
from __future__ import annotations

from flask import Blueprint, Flask

from . import health

ROUTES: tuple[Blueprint, ...] = (
    health.bp,
)


def register_blueprints(app: Flask) -> None:
    """Adjunta los blueprints al objeto Flask."""
    for blueprint in ROUTES:
        app.register_blueprint(blueprint)
