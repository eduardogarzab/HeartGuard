"""Blueprint principal del User Service"""
from __future__ import annotations

import uuid

from flask import Blueprint, current_app, g, request

from ..middleware.auth_middleware import require_user_token
from ..services.user_service import UserService
from ..utils.response_builder import error_response, fail_response, success_response

user_bp = Blueprint('user', __name__)
user_service = UserService()


def _parse_int_param(name: str, *, default: int, minimum: int = 0, maximum: int | None = None) -> int:
    raw_value = request.args.get(name, default)
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"El parámetro {name} debe ser un entero válido") from exc
    if value < minimum:
        value = minimum
    if maximum is not None and value > maximum:
        value = maximum
    return value


@user_bp.before_request
def assign_trace_id() -> None:
    """Asigna un trace_id a cada request para seguimiento."""
    header_trace = request.headers.get('X-Trace-ID') or request.headers.get('X-Trace-Id')
    g.trace_id = header_trace or uuid.uuid4().hex


@user_bp.route('/', methods=['GET'])
def root():
    """Información básica del servicio."""
    data = {
        'service': 'HeartGuard User Service',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'profile': '/users/me',
            'update_profile': '/users/me',
            'memberships': '/users/me/org-memberships',
            'membership_detail': '/orgs/<org_id>/members/<user_id>',
            'health': '/health',
        },
    }
    return success_response(data=data, message='Servicio User operativo')


@user_bp.route('/users/me', methods=['GET'])
@require_user_token
def get_current_user(current_user_id: str):
    """Obtiene el perfil del usuario autenticado."""
    try:
        profile = user_service.get_profile(current_user_id)
        return success_response(data={'user': profile}, message='Perfil obtenido correctamente')
    except ValueError as exc:
        return fail_response(message=str(exc), error_code='not_found', status_code=404)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al obtener perfil de usuario', extra={'trace_id': g.trace_id, 'user_id': current_user_id})
        return error_response(message='Error interno al obtener perfil', error_code='internal_error', status_code=500)


@user_bp.route('/users/me', methods=['PATCH'])
@require_user_token
def update_current_user(current_user_id: str):
    """Actualiza campos permitidos del perfil del usuario."""
    payload = request.get_json(silent=True)
    if payload is None:
        return fail_response(message='Se requiere un cuerpo JSON válido', error_code='invalid_payload', status_code=400)

    try:
        updated = user_service.update_profile(current_user_id, payload)
        return success_response(data={'user': updated}, message='Perfil actualizado correctamente')
    except ValueError as exc:
        message = str(exc)
        lower = message.lower()
        if 'no encontrado' in lower:
            return fail_response(message=message, error_code='not_found', status_code=404)
        return fail_response(message=message, error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al actualizar perfil', extra={'trace_id': g.trace_id, 'user_id': current_user_id})
        return error_response(message='Error interno al actualizar perfil', error_code='internal_error', status_code=500)


@user_bp.route('/users/me/org-memberships', methods=['GET'])
@require_user_token
def list_memberships(current_user_id: str):
    """Lista las organizaciones a las que pertenece el usuario."""
    try:
        memberships = user_service.list_org_memberships(current_user_id)
        return success_response(data={'memberships': memberships}, message='Membresías obtenidas correctamente')
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al obtener membresías', extra={'trace_id': g.trace_id, 'user_id': current_user_id})
        return error_response(message='Error interno al obtener membresías', error_code='internal_error', status_code=500)


@user_bp.route('/orgs/<string:org_id>/members/<string:user_id>', methods=['GET'])
@require_user_token
def membership_detail(org_id: str, user_id: str, current_user_id: str):
    """Devuelve detalles de la membresía del usuario en una organización."""
    if user_id != current_user_id:
        return fail_response(message='No autorizado para consultar esta membresía', error_code='forbidden', status_code=403)

    try:
        membership = user_service.get_org_membership(org_id, current_user_id)
        return success_response(data={'membership': membership}, message='Membresía recuperada correctamente')
    except ValueError as exc:
        return fail_response(message=str(exc), error_code='not_found', status_code=404)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al obtener detalle de membresía', extra={'trace_id': g.trace_id, 'user_id': current_user_id, 'org_id': org_id})
        return error_response(message='Error interno al obtener detalle de membresía', error_code='internal_error', status_code=500)


@user_bp.route('/orgs/<string:org_id>/dashboard', methods=['GET'])
@require_user_token
def org_dashboard(org_id: str, current_user_id: str):
    try:
        data = user_service.get_org_dashboard(org_id, current_user_id)
        return success_response(data=data, message='Dashboard de organización recuperado correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except ValueError as exc:
        return fail_response(message=str(exc), error_code='not_found', status_code=404)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al obtener dashboard de organización', extra={'trace_id': g.trace_id, 'org_id': org_id, 'user_id': current_user_id})
        return error_response(message='Error interno al obtener dashboard de organización', error_code='internal_error', status_code=500)


@user_bp.route('/orgs/<string:org_id>/care-teams', methods=['GET'])
@require_user_token
def org_care_teams(org_id: str, current_user_id: str):
    try:
        data = user_service.list_org_care_teams(org_id, current_user_id)
        return success_response(data=data, message='Equipos de cuidado recuperados correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al listar equipos de cuidado', extra={'trace_id': g.trace_id, 'org_id': org_id, 'user_id': current_user_id})
        return error_response(message='Error interno al listar equipos de cuidado', error_code='internal_error', status_code=500)


@user_bp.route('/orgs/<string:org_id>/care-team-patients', methods=['GET'])
@require_user_token
def org_care_team_patients(org_id: str, current_user_id: str):
    try:
        data = user_service.list_org_care_team_patients(org_id, current_user_id)
        return success_response(data=data, message='Pacientes por equipo de cuidado recuperados correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al listar pacientes por equipo', extra={'trace_id': g.trace_id, 'org_id': org_id, 'user_id': current_user_id})
        return error_response(message='Error interno al listar pacientes por equipo', error_code='internal_error', status_code=500)


@user_bp.route('/orgs/<string:org_id>/care-teams/<string:team_id>/devices', methods=['GET'])
@require_user_token
def care_team_devices(org_id: str, team_id: str, current_user_id: str):
    try:
        data = user_service.list_care_team_devices(org_id, team_id, current_user_id, request.args)
        current_app.logger.info(
            'Dispositivos clínicos listados',
            extra={
                'trace_id': g.trace_id,
                'user_id': current_user_id,
                'org_id': org_id,
                'care_team_id': team_id,
                'returned': len(data.get('devices', [])),
            },
        )
        return success_response(data=data, message='Dispositivos clínicos recuperados correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except ValueError as exc:
        return fail_response(message=str(exc), error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al listar dispositivos clínicos', extra={'trace_id': g.trace_id, 'user_id': current_user_id, 'org_id': org_id, 'care_team_id': team_id})
        return error_response(message='Error interno al listar dispositivos clínicos', error_code='internal_error', status_code=500)


@user_bp.route('/orgs/<string:org_id>/care-teams/<string:team_id>/devices/disconnected', methods=['GET'])
@require_user_token
def care_team_disconnected_devices(org_id: str, team_id: str, current_user_id: str):
    try:
        data = user_service.list_care_team_disconnected_devices(org_id, team_id, current_user_id, request.args)
        current_app.logger.info(
            'Dispositivos desconectados detectados',
            extra={
                'trace_id': g.trace_id,
                'user_id': current_user_id,
                'org_id': org_id,
                'care_team_id': team_id,
                'count': len(data.get('devices', [])),
            },
        )
        return success_response(data=data, message='Dispositivos desconectados recuperados correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except ValueError as exc:
        return fail_response(message=str(exc), error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al obtener dispositivos desconectados', extra={'trace_id': g.trace_id, 'user_id': current_user_id, 'org_id': org_id, 'care_team_id': team_id})
        return error_response(message='Error interno al obtener dispositivos desconectados', error_code='internal_error', status_code=500)


@user_bp.route('/orgs/<string:org_id>/care-teams/<string:team_id>/devices/<string:device_id>', methods=['GET'])
@require_user_token
def care_team_device_detail(org_id: str, team_id: str, device_id: str, current_user_id: str):
    try:
        data = user_service.get_care_team_device_detail(org_id, team_id, device_id, current_user_id)
        return success_response(data=data, message='Dispositivo clínico recuperado correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except ValueError as exc:
        message = str(exc)
        if 'no encontrado' in message.lower():
            return fail_response(message=message, error_code='not_found', status_code=404)
        return fail_response(message=message, error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al obtener detalle de dispositivo clínico', extra={'trace_id': g.trace_id, 'user_id': current_user_id, 'org_id': org_id, 'care_team_id': team_id, 'device_id': device_id})
        return error_response(message='Error interno al obtener dispositivo clínico', error_code='internal_error', status_code=500)


@user_bp.route('/orgs/<string:org_id>/care-teams/<string:team_id>/devices/<string:device_id>/streams', methods=['GET'])
@require_user_token
def care_team_device_streams(org_id: str, team_id: str, device_id: str, current_user_id: str):
    try:
        data = user_service.list_care_team_device_streams(org_id, team_id, device_id, current_user_id, request.args)
        current_app.logger.info(
            'Streams de dispositivo recuperados',
            extra={
                'trace_id': g.trace_id,
                'user_id': current_user_id,
                'org_id': org_id,
                'care_team_id': team_id,
                'device_id': device_id,
                'returned': len(data.get('streams', [])),
            },
        )
        return success_response(data=data, message='Streams del dispositivo recuperados correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except ValueError as exc:
        message = str(exc)
        if 'no encontrado' in message.lower():
            return fail_response(message=message, error_code='not_found', status_code=404)
        return fail_response(message=message, error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al obtener streams de dispositivo', extra={'trace_id': g.trace_id, 'user_id': current_user_id, 'org_id': org_id, 'care_team_id': team_id, 'device_id': device_id})
        return error_response(message='Error interno al obtener streams del dispositivo', error_code='internal_error', status_code=500)


@user_bp.route('/orgs/<string:org_id>/patients/<string:patient_id>', methods=['GET'])
@require_user_token
def org_patient_detail(org_id: str, patient_id: str, current_user_id: str):
    try:
        data = user_service.get_org_patient_detail(org_id, patient_id, current_user_id)
        return success_response(data=data, message='Paciente recuperado correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except ValueError as exc:
        message = str(exc)
        if 'no encontrado' in message.lower():
            return fail_response(message=message, error_code='not_found', status_code=404)
        return fail_response(message=message, error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al obtener detalle de paciente', extra={'trace_id': g.trace_id, 'org_id': org_id, 'patient_id': patient_id, 'user_id': current_user_id})
        return error_response(message='Error interno al obtener detalle de paciente', error_code='internal_error', status_code=500)


@user_bp.route('/orgs/<string:org_id>/patients/<string:patient_id>/alerts', methods=['GET'])
@require_user_token
def org_patient_alerts(org_id: str, patient_id: str, current_user_id: str):
    try:
        limit = _parse_int_param('limit', default=25, minimum=1, maximum=200)
        offset = _parse_int_param('offset', default=0, minimum=0)
    except ValueError as exc:
        return fail_response(message=str(exc), error_code='validation_error', status_code=400)

    try:
        data = user_service.list_org_patient_alerts(org_id, patient_id, current_user_id, limit=limit, offset=offset)
        return success_response(data=data, message='Alertas de paciente recuperadas correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except ValueError as exc:
        message = str(exc)
        if 'no encontrado' in message.lower():
            return fail_response(message=message, error_code='not_found', status_code=404)
        return fail_response(message=message, error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al listar alertas de paciente', extra={'trace_id': g.trace_id, 'org_id': org_id, 'patient_id': patient_id, 'user_id': current_user_id})
        return error_response(message='Error interno al listar alertas de paciente', error_code='internal_error', status_code=500)


@user_bp.route('/orgs/<string:org_id>/patients/<string:patient_id>/notes', methods=['GET'])
@require_user_token
def org_patient_notes(org_id: str, patient_id: str, current_user_id: str):
    try:
        limit = _parse_int_param('limit', default=50, minimum=1, maximum=200)
    except ValueError as exc:
        return fail_response(message=str(exc), error_code='validation_error', status_code=400)

    try:
        data = user_service.list_org_patient_notes(org_id, patient_id, current_user_id, limit=limit)
        return success_response(data=data, message='Notas del paciente recuperadas correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except ValueError as exc:
        message = str(exc)
        if 'no encontrado' in message.lower():
            return fail_response(message=message, error_code='not_found', status_code=404)
        return fail_response(message=message, error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al listar notas de paciente', extra={'trace_id': g.trace_id, 'org_id': org_id, 'patient_id': patient_id, 'user_id': current_user_id})
        return error_response(message='Error interno al listar notas de paciente', error_code='internal_error', status_code=500)


@user_bp.route('/orgs/<string:org_id>/metrics', methods=['GET'])
@require_user_token
def org_metrics(org_id: str, current_user_id: str):
    try:
        data = user_service.get_org_metrics(org_id, current_user_id)
        return success_response(data=data, message='Métricas de organización recuperadas correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al obtener métricas de organización', extra={'trace_id': g.trace_id, 'org_id': org_id, 'user_id': current_user_id})
        return error_response(message='Error interno al obtener métricas de organización', error_code='internal_error', status_code=500)


@user_bp.route('/care-team/locations', methods=['GET'])
@require_user_token
def care_team_locations(current_user_id: str):
    try:
        data = user_service.list_care_team_locations(current_user_id, request.args)
        current_app.logger.info(
            'Care team locations recuperadas',
            extra={
                'trace_id': g.trace_id,
                'user_id': current_user_id,
                'total': data.get('count', 0),
                'patients': len(data.get('patients', [])),
                'members': len(data.get('members', [])),
            },
        )
        return success_response(data=data, message='Ubicaciones de equipos recuperadas correctamente')
    except ValueError as exc:
        return fail_response(message=str(exc), error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al obtener ubicaciones de care teams', extra={'trace_id': g.trace_id, 'user_id': current_user_id})
        return error_response(message='Error interno al obtener ubicaciones de equipos', error_code='internal_error', status_code=500)


@user_bp.route('/caregiver/patients', methods=['GET'])
@require_user_token
def caregiver_patients(current_user_id: str):
    try:
        data = user_service.list_caregiver_patients(current_user_id)
        return success_response(data=data, message='Pacientes del cuidador recuperados correctamente')
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al listar pacientes del cuidador', extra={'trace_id': g.trace_id, 'user_id': current_user_id})
        return error_response(message='Error interno al listar pacientes del cuidador', error_code='internal_error', status_code=500)


@user_bp.route('/caregiver/patients/locations', methods=['GET'])
@require_user_token
def caregiver_patient_locations(current_user_id: str):
    try:
        data = user_service.list_caregiver_patient_locations(current_user_id, request.args)
        current_app.logger.info(
            'Caregiver patient locations recuperadas',
            extra={
                'trace_id': g.trace_id,
                'user_id': current_user_id,
                'total': data.get('count', 0),
                'returned': len(data.get('patients', [])),
            },
        )
        return success_response(data=data, message='Ubicaciones de pacientes del cuidador recuperadas correctamente')
    except ValueError as exc:
        return fail_response(message=str(exc), error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al obtener ubicaciones de pacientes para cuidador', extra={'trace_id': g.trace_id, 'user_id': current_user_id})
        return error_response(message='Error interno al obtener ubicaciones de pacientes', error_code='internal_error', status_code=500)


@user_bp.route('/caregiver/patients/<string:patient_id>', methods=['GET'])
@require_user_token
def caregiver_patient_detail(patient_id: str, current_user_id: str):
    try:
        data = user_service.get_caregiver_patient_detail(patient_id, current_user_id)
        return success_response(data=data, message='Detalle de paciente recuperado correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except ValueError as exc:
        message = str(exc)
        if 'no encontrado' in message.lower():
            return fail_response(message=message, error_code='not_found', status_code=404)
        return fail_response(message=message, error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al obtener detalle de paciente para cuidador', extra={'trace_id': g.trace_id, 'patient_id': patient_id, 'user_id': current_user_id})
        return error_response(message='Error interno al obtener detalle de paciente', error_code='internal_error', status_code=500)


@user_bp.route('/caregiver/patients/<string:patient_id>/alerts', methods=['GET'])
@require_user_token
def caregiver_patient_alerts(patient_id: str, current_user_id: str):
    try:
        limit = _parse_int_param('limit', default=25, minimum=1, maximum=200)
        offset = _parse_int_param('offset', default=0, minimum=0)
    except ValueError as exc:
        return fail_response(message=str(exc), error_code='validation_error', status_code=400)

    try:
        data = user_service.list_caregiver_patient_alerts(patient_id, current_user_id, limit=limit, offset=offset)
        return success_response(data=data, message='Alertas del paciente recuperadas correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except ValueError as exc:
        message = str(exc)
        if 'no encontrado' in message.lower():
            return fail_response(message=message, error_code='not_found', status_code=404)
        return fail_response(message=message, error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al listar alertas para cuidador', extra={'trace_id': g.trace_id, 'patient_id': patient_id, 'user_id': current_user_id})
        return error_response(message='Error interno al listar alertas del paciente', error_code='internal_error', status_code=500)


@user_bp.route('/caregiver/patients/<string:patient_id>/notes', methods=['GET'])
@require_user_token
def caregiver_patient_notes(patient_id: str, current_user_id: str):
    try:
        limit = _parse_int_param('limit', default=50, minimum=1, maximum=200)
    except ValueError as exc:
        return fail_response(message=str(exc), error_code='validation_error', status_code=400)

    try:
        data = user_service.list_caregiver_patient_notes(patient_id, current_user_id, limit=limit)
        return success_response(data=data, message='Notas del paciente recuperadas correctamente')
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except ValueError as exc:
        message = str(exc)
        if 'no encontrado' in message.lower():
            return fail_response(message=message, error_code='not_found', status_code=404)
        return fail_response(message=message, error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al listar notas para cuidador', extra={'trace_id': g.trace_id, 'patient_id': patient_id, 'user_id': current_user_id})
        return error_response(message='Error interno al listar notas del paciente', error_code='internal_error', status_code=500)


@user_bp.route('/caregiver/patients/<string:patient_id>/notes', methods=['POST'])
@require_user_token
def caregiver_patient_add_note(patient_id: str, current_user_id: str):
    payload = request.get_json(silent=True)
    if payload is None:
        return fail_response(message='Se requiere un cuerpo JSON válido', error_code='invalid_payload', status_code=400)

    try:
        data = user_service.add_caregiver_patient_note(patient_id, current_user_id, payload)
        return success_response(data=data, message='Nota registrada correctamente', status_code=201)
    except PermissionError as exc:
        return fail_response(message=str(exc), error_code='forbidden', status_code=403)
    except ValueError as exc:
        message = str(exc)
        if 'evento' in message.lower() and 'verifica' in message.lower():
            return fail_response(message=message, error_code='validation_error', status_code=400)
        if 'formato' in message.lower():
            return fail_response(message=message, error_code='validation_error', status_code=400)
        if 'no se pudo' in message.lower():
            return fail_response(message=message, error_code='validation_error', status_code=400)
        return fail_response(message=message, error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al crear nota para cuidador', extra={'trace_id': g.trace_id, 'patient_id': patient_id, 'user_id': current_user_id})
        return error_response(message='Error interno al crear nota del paciente', error_code='internal_error', status_code=500)


@user_bp.route('/caregiver/metrics', methods=['GET'])
@require_user_token
def caregiver_metrics(current_user_id: str):
    try:
        data = user_service.get_caregiver_metrics(current_user_id)
        return success_response(data=data, message='Métricas del cuidador recuperadas correctamente')
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al obtener métricas del cuidador', extra={'trace_id': g.trace_id, 'user_id': current_user_id})
        return error_response(message='Error interno al obtener métricas del cuidador', error_code='internal_error', status_code=500)


@user_bp.route('/users/me/push-devices', methods=['GET'])
@require_user_token
def list_push_devices(current_user_id: str):
    try:
        data = user_service.list_push_devices(current_user_id)
        current_app.logger.info('Push devices listados', extra={'trace_id': g.trace_id, 'user_id': current_user_id, 'count': data.get('count', 0)})
        return success_response(data=data, message='Dispositivos push recuperados correctamente')
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al listar dispositivos push', extra={'trace_id': g.trace_id, 'user_id': current_user_id})
        return error_response(message='Error interno al listar dispositivos push', error_code='internal_error', status_code=500)


@user_bp.route('/users/me/push-devices', methods=['POST'])
@require_user_token
def register_push_device(current_user_id: str):
    payload = request.get_json(silent=True)
    if payload is None:
        return fail_response(message='Se requiere un cuerpo JSON válido', error_code='invalid_payload', status_code=400)

    try:
        data = user_service.register_push_device(current_user_id, payload)
        current_app.logger.info('Push device registrado', extra={'trace_id': g.trace_id, 'user_id': current_user_id})
        return success_response(data=data, message='Dispositivo push registrado correctamente', status_code=201)
    except ValueError as exc:
        message = str(exc)
        if 'no encontrado' in message.lower():
            return fail_response(message=message, error_code='not_found', status_code=404)
        return fail_response(message=message, error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al registrar dispositivo push', extra={'trace_id': g.trace_id, 'user_id': current_user_id})
        return error_response(message='Error interno al registrar dispositivo push', error_code='internal_error', status_code=500)


@user_bp.route('/users/me/push-devices/<string:device_id>', methods=['PATCH'])
@require_user_token
def update_push_device(device_id: str, current_user_id: str):
    payload = request.get_json(silent=True)
    if payload is None:
        return fail_response(message='Se requiere un cuerpo JSON válido', error_code='invalid_payload', status_code=400)

    try:
        data = user_service.update_push_device(current_user_id, device_id, payload)
        current_app.logger.info('Push device actualizado', extra={'trace_id': g.trace_id, 'user_id': current_user_id, 'push_device_id': device_id})
        return success_response(data=data, message='Dispositivo push actualizado correctamente')
    except ValueError as exc:
        message = str(exc)
        if 'no encontrado' in message.lower():
            return fail_response(message=message, error_code='not_found', status_code=404)
        return fail_response(message=message, error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al actualizar dispositivo push', extra={'trace_id': g.trace_id, 'user_id': current_user_id, 'push_device_id': device_id})
        return error_response(message='Error interno al actualizar dispositivo push', error_code='internal_error', status_code=500)


@user_bp.route('/users/me/push-devices/<string:device_id>', methods=['DELETE'])
@require_user_token
def delete_push_device(device_id: str, current_user_id: str):
    try:
        user_service.delete_push_device(current_user_id, device_id)
        current_app.logger.info('Push device eliminado', extra={'trace_id': g.trace_id, 'user_id': current_user_id, 'push_device_id': device_id})
        return success_response(data={}, message='Dispositivo push eliminado correctamente')
    except ValueError as exc:
        message = str(exc)
        if 'no encontrado' in message.lower():
            return fail_response(message=message, error_code='not_found', status_code=404)
        return fail_response(message=message, error_code='validation_error', status_code=400)
    except Exception:  # pragma: no cover - defensivo
        current_app.logger.exception('Error al eliminar dispositivo push', extra={'trace_id': g.trace_id, 'user_id': current_user_id, 'push_device_id': device_id})
        return error_response(message='Error interno al eliminar dispositivo push', error_code='internal_error', status_code=500)
