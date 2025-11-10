"""Clientes de almacenamiento para Media Service."""
from __future__ import annotations

from .spaces_client import SpacesClient, SpacesClientError

__all__ = ["SpacesClient", "SpacesClientError"]
