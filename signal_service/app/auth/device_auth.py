# signal_service/app/auth/device_auth.py
from functools import wraps
from flask import request, g, jsonify
from ..repository import device_key_repository

def require_device_key(f):
    """
    Decorator for device-specific authentication.
    Validates 'X-Device-UUID' and 'X-Device-Token' headers.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        device_uuid = request.headers.get('X-Device-UUID')
        device_token = request.headers.get('X-Device-Token')

        # 1. Check for presence of headers
        if not device_uuid or not device_token:
            return jsonify({"error": "Missing X-Device-UUID or X-Device-Token header"}), 400

        # 2. Find the device key in the database
        device_key = device_key_repository.find_key_by_uuid(device_uuid)
        if not device_key:
            return jsonify({"error": "Unauthorized: Invalid device UUID"}), 401

        # 3. Verify the API key/token
        if not device_key_repository.verify_api_key(device_key, device_token):
            return jsonify({"error": "Unauthorized: Invalid device token"}), 401

        # 4. Check if the device key is active
        if device_key.status != 'active':
            return jsonify({"error": f"Device key is not active. Status: {device_key.status}"}), 401

        # 5. Attach the authenticated device object to the request context
        g.device = device_key

        return f(*args, **kwargs)
    return decorated_function
