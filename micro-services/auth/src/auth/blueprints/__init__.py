"""Registro de blueprints para Auth Service."""
from __future__ import annotations

from flask import Blueprint, Flask

from . import auth, health

ROUTES: tuple[Blueprint, ...] = (
    health.bp,
    auth.bp,
)


def register_blueprints(app: Flask) -> None:
    for blueprint in ROUTES:
        app.register_blueprint(blueprint)
