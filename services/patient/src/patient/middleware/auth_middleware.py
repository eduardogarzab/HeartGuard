"""
Middleware de autenticación JWT
"""
from functools import wraps
from flask import request, jsonify
from ..utils.jwt_utils import extract_token_from_header, verify_patient_token


def require_patient_token(f):
    """
    Decorador que requiere un token JWT válido de paciente.
    Extrae el patient_id del token y lo pasa a la función decorada.
    
    Usage:
        @app.route('/patient/dashboard')
        @require_patient_token
        def dashboard(patient_id):
            # patient_id está disponible aquí
            return jsonify({"patient_id": patient_id})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Obtener el header Authorization
            auth_header = request.headers.get('Authorization')
            
            # Extraer el token
            token = extract_token_from_header(auth_header)
            
            # Verificar y decodificar el token
            payload = verify_patient_token(token)
            
            # Pasar el patient_id a la función decorada
            return f(patient_id=payload['patient_id'], *args, **kwargs)
            
        except ValueError as e:
            return jsonify({
                "error": "Unauthorized",
                "message": str(e)
            }), 401
        except Exception as e:
            return jsonify({
                "error": "Authentication failed",
                "message": "Error al validar el token"
            }), 401
    
    return decorated_function
