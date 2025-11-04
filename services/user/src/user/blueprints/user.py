"""Blueprint principal del User Service"""
from __future__ import annotations

import uuid

from flask import Blueprint, current_app, g, request

from ..middleware.auth_middleware import require_user_token
from ..services.user_service import UserService
from ..utils.response_builder import error_response, fail_response, success_response

user_bp = Blueprint('user', __name__)
user_service = UserService()


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
