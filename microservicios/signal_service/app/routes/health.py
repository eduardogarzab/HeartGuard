# signal_service/app/routes/health.py
from flask import Blueprint, jsonify

health_bp = Blueprint('health_bp', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    Returns a 200 OK response if the service is running.
    """
    return jsonify({"status": "ok"}), 200
