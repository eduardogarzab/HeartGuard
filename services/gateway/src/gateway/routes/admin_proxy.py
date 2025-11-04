"""Proxy para rutas de administración hacia Admin Service."""
from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, Response, current_app, request

from ..services.admin_client import AdminClient, AdminClientError

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _get_admin_client() -> AdminClient:
    """Obtiene instancia del cliente de administración."""
    return AdminClient(
        base_url=current_app.config["ADMIN_SERVICE_URL"],
        timeout=current_app.config["GATEWAY_SERVICE_TIMEOUT"],
    )


def _proxy_request(path: str, method: str = "GET") -> Response:
    """
    Realiza proxy de la petición al admin-service.
    
    Args:
        path: Ruta relativa dentro del admin service
        method: Método HTTP (GET, POST, PATCH, DELETE, etc.)
    
    Returns:
        Response con el contenido del admin-service
    """
    # Reenviar headers importantes (especialmente Authorization)
    headers = {}
    if "Authorization" in request.headers:
        headers["Authorization"] = request.headers["Authorization"]
    if "Content-Type" in request.headers:
        headers["Content-Type"] = request.headers["Content-Type"]
    
    # Obtener datos del request
    json_data = None
    raw_data = None
    if method in {"POST", "PATCH", "PUT"}:
        if request.is_json:
            json_data = request.get_json()
        elif request.data:
            raw_data = request.get_data()
    
    # Query params
    params = request.args.to_dict() if request.args else None
    
    try:
        client = _get_admin_client()
        resp = client.proxy_request(
            method=method,
            path=path,
            headers=headers,
            json=json_data,
            data=raw_data,
            params=params,
        )
        
        # Crear respuesta con el mismo status y contenido
        return Response(
            response=resp.content,
            status=resp.status_code,
            headers=dict(resp.headers),
        )
    
    except AdminClientError as e:
        return Response(
            f'<?xml version="1.0"?><response><error><code>{e.error}</code>'
            f'<message>{e.message}</message></error></response>',
            status=e.status_code,
            mimetype="application/xml",
        )
    except Exception as e:
        current_app.logger.error(f"Error en proxy admin: {e}")
        return Response(
            '<?xml version="1.0"?><response><error><code>internal_error</code>'
            '<message>Error interno del gateway</message></error></response>',
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            mimetype="application/xml",
        )


# Rutas de organizaciones
@bp.route("/organizations/", methods=["GET"])
def list_organizations():
    """Lista organizaciones del usuario autenticado."""
    return _proxy_request("/admin/organizations/", "GET")


@bp.route("/organizations/<org_id>", methods=["GET"])
def get_organization(org_id: str):
    """Detalle de una organización."""
    return _proxy_request(f"/admin/organizations/{org_id}", "GET")


@bp.route("/organizations/<org_id>/dashboard", methods=["GET"])
def organization_dashboard(org_id: str):
    """Dashboard de la organización."""
    return _proxy_request(f"/admin/organizations/{org_id}/dashboard", "GET")


# Rutas de staff
@bp.route("/organizations/<org_id>/staff/", methods=["GET"])
def list_staff(org_id: str):
    """Lista miembros del staff."""
    return _proxy_request(f"/admin/organizations/{org_id}/staff/", "GET")


@bp.route("/organizations/<org_id>/staff/invitations", methods=["GET", "POST"])
def staff_invitations(org_id: str):
    """Gestión de invitaciones."""
    return _proxy_request(f"/admin/organizations/{org_id}/staff/invitations", request.method)


@bp.route("/organizations/<org_id>/staff/<user_id>", methods=["PATCH", "DELETE"])
def manage_staff_member(org_id: str, user_id: str):
    """Actualizar o eliminar miembro del staff."""
    return _proxy_request(f"/admin/organizations/{org_id}/staff/{user_id}", request.method)


# Rutas de pacientes
@bp.route("/organizations/<org_id>/patients/", methods=["GET", "POST"])
def patients(org_id: str):
    """Lista o crea pacientes."""
    return _proxy_request(f"/admin/organizations/{org_id}/patients/", request.method)


@bp.route("/organizations/<org_id>/patients/<patient_id>", methods=["GET", "PATCH", "DELETE"])
def patient_detail(org_id: str, patient_id: str):
    """Gestión de un paciente específico."""
    return _proxy_request(f"/admin/organizations/{org_id}/patients/{patient_id}", request.method)


# Rutas de care teams
@bp.route("/organizations/<org_id>/care-teams/", methods=["GET", "POST"])
def care_teams(org_id: str):
    """Lista o crea equipos de cuidado."""
    return _proxy_request(f"/admin/organizations/{org_id}/care-teams/", request.method)


@bp.route("/organizations/<org_id>/care-teams/<team_id>", methods=["GET", "PATCH", "DELETE"])
def care_team_detail(org_id: str, team_id: str):
    """Gestión de un equipo específico."""
    return _proxy_request(f"/admin/organizations/{org_id}/care-teams/{team_id}", request.method)


@bp.route("/organizations/<org_id>/care-teams/<team_id>/members", methods=["GET", "POST"])
def care_team_members(org_id: str, team_id: str):
    """Gestión de miembros del equipo."""
    return _proxy_request(f"/admin/organizations/{org_id}/care-teams/{team_id}/members", request.method)


@bp.route("/organizations/<org_id>/care-teams/<team_id>/members/<user_id>", methods=["PATCH", "DELETE"])
def care_team_member_detail(org_id: str, team_id: str, user_id: str):
    """Gestión de un miembro específico."""
    return _proxy_request(f"/admin/organizations/{org_id}/care-teams/{team_id}/members/{user_id}", request.method)


@bp.route("/organizations/<org_id>/care-teams/<team_id>/patients", methods=["GET", "POST"])
def care_team_patients(org_id: str, team_id: str):
    """Gestión de pacientes en el equipo."""
    return _proxy_request(f"/admin/organizations/{org_id}/care-teams/{team_id}/patients", request.method)


@bp.route("/organizations/<org_id>/care-teams/<team_id>/patients/<patient_id>", methods=["DELETE"])
def care_team_patient_detail(org_id: str, team_id: str, patient_id: str):
    """Remover paciente del equipo."""
    return _proxy_request(f"/admin/organizations/{org_id}/care-teams/{team_id}/patients/{patient_id}", request.method)


# Rutas de cuidadores
@bp.route("/organizations/<org_id>/caregivers/relationship-types", methods=["GET"])
def caregiver_relationship_types(org_id: str):
    """Lista tipos de relación de cuidadores."""
    return _proxy_request(f"/admin/organizations/{org_id}/caregivers/relationship-types", "GET")


@bp.route("/organizations/<org_id>/caregivers/assignments", methods=["GET", "POST"])
def caregiver_assignments(org_id: str):
    """Gestión de asignaciones de cuidadores."""
    return _proxy_request(f"/admin/organizations/{org_id}/caregivers/assignments", request.method)


@bp.route("/organizations/<org_id>/caregivers/assignments/<patient_id>/<caregiver_id>", methods=["PATCH", "DELETE"])
def caregiver_assignment_detail(org_id: str, patient_id: str, caregiver_id: str):
    """Gestión de una asignación específica."""
    return _proxy_request(f"/admin/organizations/{org_id}/caregivers/assignments/{patient_id}/{caregiver_id}", request.method)


# Rutas de alertas
@bp.route("/organizations/<org_id>/alerts/", methods=["GET"])
def alerts(org_id: str):
    """Lista alertas de la organización."""
    return _proxy_request(f"/admin/organizations/{org_id}/alerts/", "GET")


@bp.route("/organizations/<org_id>/alerts/<alert_id>", methods=["GET"])
def alert_detail(org_id: str, alert_id: str):
    """Detalle de una alerta."""
    return _proxy_request(f"/admin/organizations/{org_id}/alerts/{alert_id}", "GET")


@bp.route("/organizations/<org_id>/alerts/<alert_id>/ack", methods=["POST"])
def alert_ack(org_id: str, alert_id: str):
    """Acusar alerta."""
    return _proxy_request(f"/admin/organizations/{org_id}/alerts/{alert_id}/ack", "POST")


@bp.route("/organizations/<org_id>/alerts/<alert_id>/resolve", methods=["POST"])
def alert_resolve(org_id: str, alert_id: str):
    """Resolver alerta."""
    return _proxy_request(f"/admin/organizations/{org_id}/alerts/{alert_id}/resolve", "POST")
