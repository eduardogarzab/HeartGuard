"""Gestión centralizada de extensiones Flask."""
from __future__ import annotations

from typing import Any


# Mantiene la firma para futuras extensiones (cache, tracing, etc.).
def init_extensions(app: Any) -> None:
    """Inicializa extensiones asociadas al gateway."""
    # Actualmente no hay extensiones registradas.
    # Placeholder para la futura integración de cache, tracing, etc.
    _ = app
