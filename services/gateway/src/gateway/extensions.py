"""Gestión centralizada de extensiones Flask."""
from __future__ import annotations

from typing import Any
from flask_cors import CORS


def init_extensions(app: Any) -> None:
    """Inicializa extensiones asociadas al gateway."""
    # Habilitar CORS para permitir requests desde cualquier origen
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })
