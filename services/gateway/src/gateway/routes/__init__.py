"""Registro de blueprints del gateway."""
from __future__ import annotations

from flask import Blueprint, Flask

from . import admin_proxy, auth_proxy, health, user_proxy

ROUTES: tuple[Blueprint, ...] = (
    health.bp,
    auth_proxy.bp,
    admin_proxy.bp,
    user_proxy.bp,
)


def register_blueprints(app: Flask) -> None:
    """Adjunta los blueprints al objeto Flask."""
    for blueprint in ROUTES:
        app.register_blueprint(blueprint)
