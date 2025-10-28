import jwt
from functools import wraps
from flask import request, jsonify, g
from config import Config

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            try:
                # Espera un token "Bearer <token>"
                token_parts = request.headers['Authorization'].split()
                if token_parts[0].lower() != 'bearer' or len(token_parts) != 2:
                    raise ValueError("Formato de token inválido")
                token = token_parts[1]
            except Exception:
                 return jsonify({"message": "Formato de token inválido"}), 401

        if not token:
            return jsonify({"message": "Token es requerido"}), 401

        try:
            # Decodificar el token usando la clave y algoritmo de la config
            data = jwt.decode(
                token, 
                Config.JWT_SECRET_KEY, 
                algorithms=[Config.JWT_ALGORITHM]
            )
            
            # Almacenar datos del token en el contexto global de Flask (g)
            # para que la ruta del proxy pueda implementar la Tenancy (x-org-ID)
            g.user_id = data.get('user_id')
            g.org_id = data.get('org_id')

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token ha expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token inválido"}), 401
        except Exception as e:
            return jsonify({"message": "Error al procesar el token", "error": str(e)}), 401

        return f(*args, **kwargs)

    return decorated