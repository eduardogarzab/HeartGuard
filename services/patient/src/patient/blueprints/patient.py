"""
Blueprint principal del servicio de pacientes
"""
from flask import Blueprint, jsonify, request
from ..middleware.auth_middleware import require_patient_token
from ..services.patient_service import PatientService

# Crear blueprint
patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

# Instanciar servicio
patient_service = PatientService()


@patient_bp.route('/dashboard', methods=['GET'])
@require_patient_token
def get_dashboard(patient_id: str):
    """
    Obtiene todos los datos del dashboard del paciente
    
    Returns:
        JSON con perfil, estadísticas, alertas recientes y equipo de cuidado
    """
    try:
        data = patient_service.get_dashboard_data(patient_id)
        return jsonify(data), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Error al obtener dashboard', 'details': str(e)}), 500


@patient_bp.route('/profile', methods=['GET'])
@require_patient_token
def get_profile(patient_id: str):
    """
    Obtiene el perfil completo del paciente
    
    Returns:
        JSON con información del perfil
    """
    try:
        profile = patient_service.get_profile(patient_id)
        return jsonify(profile), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'Error al obtener perfil', 'details': str(e)}), 500


@patient_bp.route('/alerts', methods=['GET'])
@require_patient_token
def get_alerts(patient_id: str):
    """
    Obtiene alertas del paciente con paginación y filtros
    
    Query params:
        - status: (opcional) Filtrar por estado (new, ack, resolved)
        - limit: (opcional) Cantidad de resultados (default: 20)
        - offset: (opcional) Desplazamiento para paginación (default: 0)
    
    Returns:
        JSON con lista de alertas y metadata de paginación
    """
    try:
        # Obtener query params
        status = request.args.get('status')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Validar limit
        if limit > 100:
            limit = 100
        
        data = patient_service.get_alerts(patient_id, status, limit, offset)
        return jsonify(data), 200
    except ValueError as e:
        return jsonify({'error': 'Parámetros inválidos', 'details': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Error al obtener alertas', 'details': str(e)}), 500


@patient_bp.route('/devices', methods=['GET'])
@require_patient_token
def get_devices(patient_id: str):
    """
    Obtiene dispositivos asignados al paciente
    
    Returns:
        JSON con lista de dispositivos
    """
    try:
        data = patient_service.get_devices(patient_id)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': 'Error al obtener dispositivos', 'details': str(e)}), 500


@patient_bp.route('/caregivers', methods=['GET'])
@require_patient_token
def get_caregivers(patient_id: str):
    """
    Obtiene cuidadores (caregivers) asignados al paciente
    
    Returns:
        JSON con lista de cuidadores con su relación y estado
    """
    try:
        data = patient_service.get_caregivers(patient_id)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': 'Error al obtener cuidadores', 'details': str(e)}), 500


@patient_bp.route('/readings', methods=['GET'])
@require_patient_token
def get_readings(patient_id: str):
    """
    Obtiene historial de lecturas de señales del paciente
    
    Query params:
        - limit: (opcional) Cantidad de resultados (default: 50)
        - offset: (opcional) Desplazamiento para paginación (default: 0)
    
    Returns:
        JSON con historial de lecturas
    """
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        if limit > 100:
            limit = 100
        
        data = patient_service.get_signal_readings(patient_id, limit, offset)
        return jsonify(data), 200
    except ValueError as e:
        return jsonify({'error': 'Parámetros inválidos', 'details': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Error al obtener lecturas', 'details': str(e)}), 500


@patient_bp.route('/care-team', methods=['GET'])
@require_patient_token
def get_care_team(patient_id: str):
    """
    Obtiene el equipo de cuidado asignado al paciente
    
    Returns:
        JSON con equipos y miembros
    """
    try:
        data = patient_service.get_care_team(patient_id)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': 'Error al obtener equipo de cuidado', 'details': str(e)}), 500


@patient_bp.route('/location/latest', methods=['GET'])
@require_patient_token
def get_latest_location(patient_id: str):
    """
    Obtiene la última ubicación registrada del paciente
    
    Returns:
        JSON con ubicación o null si no hay datos
    """
    try:
        data = patient_service.get_latest_location(patient_id)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': 'Error al obtener ubicación', 'details': str(e)}), 500


@patient_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint (no requiere autenticación)
    
    Returns:
        JSON con estado del servicio
    """
    return jsonify({
        'status': 'healthy',
        'service': 'patient-service',
        'version': '1.0.0'
    }), 200
