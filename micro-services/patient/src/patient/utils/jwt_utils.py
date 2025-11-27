"""
Utilidades para trabajar con JWT
"""
import jwt
from datetime import datetime, timedelta
from ..config import get_config

config = get_config()


def decode_token(token: str) -> dict:
    """
    Decodifica y valida un JWT token
    
    Args:
        token: Token JWT en formato string
        
    Returns:
        dict: Payload del token decodificado
        
    Raises:
        jwt.ExpiredSignatureError: Si el token ha expirado
        jwt.InvalidTokenError: Si el token es inválido
    """
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expirado")
    except jwt.InvalidTokenError:
        raise ValueError("Token inválido")


def verify_patient_token(token: str) -> dict:
    """
    Verifica que el token sea de un paciente válido
    
    Args:
        token: Token JWT en formato string
        
    Returns:
        dict: Payload del token con patient_id
        
    Raises:
        ValueError: Si el token no es de paciente o es inválido
    """
    payload = decode_token(token)
    
    # Verificar que sea un token de paciente
    if payload.get('account_type') != 'patient':
        raise ValueError("Token no es de paciente")
    
    # Verificar que tenga patient_id
    if 'patient_id' not in payload:
        raise ValueError("Token no contiene patient_id")
    
    return payload


def extract_token_from_header(authorization_header: str) -> str:
    """
    Extrae el token del header Authorization
    
    Args:
        authorization_header: Header Authorization completo
        
    Returns:
        str: Token sin el prefijo "Bearer "
        
    Raises:
        ValueError: Si el header no tiene el formato correcto
    """
    if not authorization_header:
        raise ValueError("Header Authorization no proporcionado")
    
    parts = authorization_header.split()
    
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise ValueError("Header Authorization debe ser 'Bearer <token>'")
    
    return parts[1]
