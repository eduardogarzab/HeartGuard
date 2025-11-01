"""Middleware para validar API Key en comunicación interna."""
from __future__ import annotations

import os
from functools import wraps

from flask import request

from common.errors import APIError


def require_api_key(f):
    """
    Decorator para requerir API Key en endpoints del gateway.
    
    El API Key debe venir en el header: X-Internal-API-Key
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Solo validar si REQUIRE_API_KEY está habilitado
        if os.getenv("REQUIRE_API_KEY", "false").lower() != "true":
            return f(*args, **kwargs)
        
        api_key = request.headers.get("X-Internal-API-Key")
        expected_key = os.getenv("INTERNAL_API_KEY")
        
        if not api_key:
            raise APIError(
                "Missing API Key",
                status_code=401,
                error_id="HG-GW-NO-API-KEY"
            )
        
        if not expected_key:
            raise APIError(
                "API Key not configured",
                status_code=500,
                error_id="HG-GW-API-KEY-NOT-CONFIGURED"
            )
        
        if api_key != expected_key:
            raise APIError(
                "Invalid API Key",
                status_code=403,
                error_id="HG-GW-INVALID-API-KEY"
            )
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_api_key_middleware(app):
    """
    Middleware global para validar API Key en todas las requests al gateway.
    Excepto el endpoint /health.
    """
    @app.before_request
    def check_api_key():
        # Permitir health check sin API Key
        if request.path == "/health":
            return None
        
        # Solo validar si REQUIRE_API_KEY está habilitado
        if os.getenv("REQUIRE_API_KEY", "false").lower() != "true":
            return None
        
        api_key = request.headers.get("X-Internal-API-Key")
        expected_key = os.getenv("INTERNAL_API_KEY")
        
        if not api_key:
            raise APIError(
                "Missing API Key - Use header X-Internal-API-Key",
                status_code=401,
                error_id="HG-GW-NO-API-KEY"
            )
        
        if not expected_key:
            raise APIError(
                "API Key not configured on server",
                status_code=500,
                error_id="HG-GW-API-KEY-NOT-CONFIGURED"
            )
        
        if api_key != expected_key:
            raise APIError(
                "Invalid API Key",
                status_code=403,
                error_id="HG-GW-INVALID-API-KEY"
            )
        
        return None
