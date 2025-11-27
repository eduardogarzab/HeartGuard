"""Cliente para el servicio de IA."""
from __future__ import annotations

import logging
import os
from typing import Any

import requests
from flask import Response

logger = logging.getLogger(__name__)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:5007")


def forward_request(
    method: str,
    path: str,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    params: dict[str, Any] | None = None,
) -> Response:
    """
    Reenvía una solicitud al servicio de IA.
    
    Args:
        method: Método HTTP (GET, POST, etc.)
        path: Ruta del endpoint (ej: /predict)
        headers: Headers de la solicitud
        data: Cuerpo de la solicitud
        params: Parámetros de query string
        
    Returns:
        Response de Flask con la respuesta del servicio de IA
    """
    url = f"{AI_SERVICE_URL}{path}"
    
    # Filtrar headers que no deben reenviarse
    excluded_headers = {"host", "content-length", "connection", "authorization"}
    filtered_headers = {
        key: value
        for key, value in (headers or {}).items()
        if key.lower() not in excluded_headers
    }
    
    # Añadir X-Internal-Key para autenticación service-to-service
    internal_key = os.getenv("INTERNAL_SERVICE_KEY", "dev_internal_key")
    filtered_headers["X-Internal-Key"] = internal_key
    
    try:
        logger.info(f"Forwarding {method} request to AI service: {url}")
        
        response = requests.request(
            method=method,
            url=url,
            headers=filtered_headers,
            data=data,
            params=params,
            timeout=30,  # Timeout de 30 segundos
            allow_redirects=False,
        )
        
        # Crear respuesta de Flask
        flask_response = Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers),
        )
        
        return flask_response
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al conectar con el servicio de IA: {url}")
        return Response(
            '{"error": "Service timeout", "message": "El servicio de IA no respondió a tiempo"}',
            status=504,
            content_type="application/json",
        )
        
    except requests.exceptions.ConnectionError:
        logger.error(f"Error de conexión con el servicio de IA: {url}")
        return Response(
            '{"error": "Service unavailable", "message": "No se puede conectar con el servicio de IA"}',
            status=503,
            content_type="application/json",
        )
        
    except Exception as e:
        logger.exception(f"Error inesperado al reenviar solicitud: {e}")
        return Response(
            '{"error": "Gateway error", "message": "Error interno del gateway"}',
            status=500,
            content_type="application/json",
        )
