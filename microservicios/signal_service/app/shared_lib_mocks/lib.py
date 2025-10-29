# signal_service/app/shared_lib_mocks/lib.py
import logging
from functools import wraps
from flask import request, g, jsonify, Response
from dicttoxml import dicttoxml

# Configuración básica de logging para notify_audit
logging.basicConfig(level=logging.INFO)

def require_auth(f):
    """
    Mock decorator for JWT-based authentication.
    Simulates extracting user_id and org_id from a token and attaching them to the Flask g object.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # En un sistema real, aquí se decodificaría un JWT.
        # Para el mock, simplemente asignamos valores fijos.
        g.user_id = "mock_user_id_from_jwt"
        g.org_id = "mock_org_id_from_jwt"
        return f(*args, **kwargs)
    return decorated_function

def create_response(data, status_code=200):
    """
    Mock response creation function.
    Determines the response format (JSON or XML) based on the 'Accept' header.
    Defaults to JSON if the header is not specified or is '*/*'.
    """
    accept_header = request.headers.get('Accept', 'application/json')

    if 'application/xml' in accept_header:
        # Convert dict to XML and create an XML response
        xml_data = dicttoxml(data, custom_root='response', attr_type=False)
        return Response(xml_data, status=status_code, mimetype='application/xml')
    else:
        # Default to JSON
        return jsonify(data), status_code

def notify_audit(event_type, event_details):
    """
    Mock audit notification function.
    In a real system, this would make an HTTP request to the audit_service.
    Here, it just logs the event to the console.
    """
    log_message = f"[AUDIT LOG] Event Type: {event_type}, Details: {event_details}"
    logging.info(log_message)
    print(log_message) # Also print for visibility during development
