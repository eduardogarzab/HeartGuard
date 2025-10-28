# signal_service/app/routes/streams.py
from flask import Blueprint, request, g
from ..shared_lib_mocks.lib import require_auth, create_response, notify_audit
from ..repository import stream_repository

streams_bp = Blueprint('streams_bp', __name__)

@streams_bp.route('/v1/streams', methods=['POST'])
@require_auth
def create_new_stream():
    """
    Creates a new signal stream.
    - Authenticated via @require_auth (JWT).
    - Uses g.org_id from the token.
    - Notifies the audit service.
    """
    data = request.get_json()
    if not data or not all(k in data for k in ['patient_id', 'device_key_id', 'stream_type']):
        return create_response({"error": "Missing required fields"}, 400)

    # g.org_id is populated by the @require_auth mock decorator
    org_id = g.org_id

    new_stream = stream_repository.create_stream(
        org_id=org_id,
        patient_id=data['patient_id'],
        device_key_id=data['device_key_id'],
        stream_type=data['stream_type']
    )

    # Notify the audit service about the creation
    notify_audit(
        event_type="stream_created",
        event_details={
            "stream_id": new_stream.id,
            "org_id": org_id,
            "created_by": g.user_id # Also from @require_auth
        }
    )

    # Prepare the response data
    response_data = {
        "id": new_stream.id,
        "org_id": new_stream.org_id,
        "patient_id": new_stream.patient_id,
        "status": new_stream.status
    }

    return create_response(response_data, 201)


@streams_bp.route('/v1/streams', methods=['GET'])
@require_auth
def get_streams_by_patient():
    """
    Retrieves all streams for a given patient.
    - Authenticated via @require_auth (JWT).
    - Filters by patient_id.
    """
    patient_id = request.args.get('patient_id')
    if not patient_id:
        return create_response({"error": "patient_id query parameter is required"}, 400)

    streams = stream_repository.find_streams_by_patient(int(patient_id))

    response_data = [
        {
            "id": stream.id,
            "org_id": stream.org_id,
            "patient_id": stream.patient_id,
            "stream_type": stream.stream_type,
            "status": stream.status
        } for stream in streams
    ]

    return create_response(response_data, 200)

# El endpoint GET /v1/streams/:id/data?from=&to= se deja como ejercicio
# ya que requiere una lógica de consulta de series temporales más compleja
# y no es el foco principal del boilerplate de ingesta.
