"""
Middleware para autenticación JWT
"""
import logging
import jwt
from functools import wraps
from flask import request, jsonify
from typing import Callable

from .config import JWT_SECRET, JWT_ALGORITHM

logger = logging.getLogger(__name__)


def require_auth(f: Callable) -> Callable:
    """
    Decorador para requerir autenticación JWT en endpoints
    
    Espera header: Authorization: Bearer <token>
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Obtener token del header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            logger.warning("Request sin header Authorization")
            return jsonify({
                "error": "No authorization header",
                "message": "Se requiere token de autenticación"
            }), 401
        
        # Validar formato "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            logger.warning(f"Formato de Authorization inválido: {auth_header}")
            return jsonify({
                "error": "Invalid authorization header",
                "message": "Formato debe ser: Bearer <token>"
            }), 401
        
        token = parts[1]
        
        try:
            # Validar y decodificar token
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM]
            )
            
            # Agregar payload al request para uso posterior
            request.jwt_payload = payload
            logger.info(f"Token válido para usuario: {payload.get('sub', 'unknown')}")
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return jsonify({
                "error": "Token expired",
                "message": "El token ha expirado"
            }), 401
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token inválido: {e}")
            return jsonify({
                "error": "Invalid token",
                "message": "Token de autenticación inválido"
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f: Callable) -> Callable:
    """
    Decorador para autenticación opcional
    Si hay token, lo valida; si no hay, continúa sin autenticación
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                try:
                    payload = jwt.decode(
                        token,
                        JWT_SECRET,
                        algorithms=[JWT_ALGORITHM]
                    )
                    request.jwt_payload = payload
                except jwt.InvalidTokenError:
                    pass  # Ignorar errores en autenticación opcional
        
        return f(*args, **kwargs)
    
    return decorated_function
