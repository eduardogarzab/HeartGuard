# signal_service/app/routes/ingest.py
import os
import json
import redis
from flask import Blueprint, request, jsonify, g
from pydantic import ValidationError
from dotenv import load_dotenv

from ..auth.device_auth import require_device_key
from ..models.schemas import TimeseriesDataItem

# Cargar variables de entorno
load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")

# Conectar a Redis
try:
    redis_queue = redis.from_url(REDIS_URL)
except redis.exceptions.ConnectionError as e:
    # Si Redis no está disponible al iniciar, se manejará en el endpoint
    redis_queue = None
    print(f"Could not connect to Redis: {e}")

ingest_bp = Blueprint('ingest_bp', __name__)

@ingest_bp.route('/v1/data/ingest', methods=['POST'])
@require_device_key
def ingest_data():
    """
    Asynchronous data ingestion endpoint.
    - Authenticated via @require_device_key.
    - Validates payload with Pydantic.
    - Enqueues the valid payload into a Redis queue.
    - Returns 202 Accepted.
    """
    # Verificar la conexión a Redis
    if not redis_queue:
        return jsonify({"error": "Service Unavailable: Could not connect to the queue"}), 503

    # Obtener el stream_type del query parameter
    stream_type = request.args.get('stream_type')
    if not stream_type:
        return jsonify({"error": "Bad Request: 'stream_type' query parameter is required"}), 400

    # Obtener el payload
    try:
        payload_data = request.get_json()
        if not isinstance(payload_data, list):
            return jsonify({"error": "Bad Request: Payload must be a JSON list"}), 400
        if not payload_data:
            return jsonify({"error": "Bad Request: No JSON payload provided"}), 400
    except Exception:
        return jsonify({"error": "Bad Request: Invalid JSON format"}), 400

    # Validar el payload usando Pydantic
    try:
        validated_data = [TimeseriesDataItem.parse_obj(item) for item in payload_data]
    except ValidationError as e:
        return jsonify({"error": "Bad Request: Payload validation failed", "details": e.errors()}), 400

    # Encontrar el stream específico para este dispositivo y tipo de stream
    target_stream = None
    for stream in g.device.signal_streams:
        if stream.stream_type == stream_type:
            target_stream = stream
            break

    if not target_stream:
        return jsonify({"error": f"Forbidden: No stream of type '{stream_type}' is configured for this device"}), 403

    if target_stream.status != 'active':
        return jsonify({"error": f"Forbidden: Stream '{stream_type}' is not active"}), 403

    # Enriquecer el payload con el stream_id para el worker
    message_for_worker = {
        "stream_id": target_stream.id,
        "data": [item.dict() for item in validated_data]
    }

    # Publicar en la cola de Redis
    try:
        redis_queue.lpush('data_ingest', json.dumps(message_for_worker))
    except redis.exceptions.ConnectionError:
        # Manejar fallo de conexión en tiempo de ejecución
        return jsonify({"error": "Service Unavailable: Could not connect to the queue"}), 503

    return jsonify({"status": "queued"}), 202
