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


@bp.route("/organizations/<org_id>/dashboard/", methods=["GET"])
def organization_dashboard(org_id: str):
    """Dashboard de la organización."""
    return _proxy_request(f"/admin/organizations/{org_id}/dashboard/", "GET")


# Rutas de staff
@bp.route("/organizations/<org_id>/staff/", methods=["GET"])
def list_staff(org_id: str):
    """Lista miembros del staff."""
    return _proxy_request(f"/admin/organizations/{org_id}/staff/", "GET")


@bp.route("/organizations/<org_id>/staff/invitations", methods=["GET", "POST"])
def staff_invitations(org_id: str):
    """Gestión de invitaciones."""
    return _proxy_request(f"/admin/organizations/{org_id}/staff/invitations", request.method)


@bp.route("/organizations/<org_id>/staff/invitations/<invitation_id>", methods=["DELETE"])
def revoke_staff_invitation(org_id: str, invitation_id: str):
    """Revocar una invitación específica."""
    return _proxy_request(f"/admin/organizations/{org_id}/staff/invitations/{invitation_id}", request.method)


@bp.route("/organizations/<org_id>/staff/members/<user_id>", methods=["PATCH", "DELETE"])
def manage_staff_member(org_id: str, user_id: str):
    """Actualizar o eliminar miembro del staff."""
    return _proxy_request(f"/admin/organizations/{org_id}/staff/members/{user_id}", request.method)


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


@bp.route("/organizations/<org_id>/care-teams/member-roles", methods=["GET"])
def care_team_member_roles(org_id: str):
    """Lista roles disponibles para miembros de un equipo de cuidado."""
    return _proxy_request(f"/admin/organizations/{org_id}/care-teams/member-roles", "GET")


@bp.route("/organizations/<org_id>/care-teams/<care_team_id>", methods=["GET", "PATCH", "DELETE"])
def care_team_detail(org_id: str, care_team_id: str):
    """Gestión de un equipo específico."""
    return _proxy_request(f"/admin/organizations/{org_id}/care-teams/{care_team_id}", request.method)


@bp.route("/organizations/<org_id>/care-teams/<care_team_id>/members", methods=["GET", "POST"])
def care_team_members(org_id: str, care_team_id: str):
    """Gestión de miembros del equipo."""
    return _proxy_request(f"/admin/organizations/{org_id}/care-teams/{care_team_id}/members", request.method)


@bp.route("/organizations/<org_id>/care-teams/<care_team_id>/members/<user_id>", methods=["PATCH", "DELETE"])
def care_team_member_detail(org_id: str, care_team_id: str, user_id: str):
    """Gestión de un miembro específico."""
    return _proxy_request(f"/admin/organizations/{org_id}/care-teams/{care_team_id}/members/{user_id}", request.method)


@bp.route("/organizations/<org_id>/care-teams/<care_team_id>/patients", methods=["GET", "POST"])
def care_team_patients(org_id: str, care_team_id: str):
    """Gestión de pacientes en el equipo."""
    return _proxy_request(f"/admin/organizations/{org_id}/care-teams/{care_team_id}/patients", request.method)


@bp.route("/organizations/<org_id>/care-teams/<care_team_id>/patients/<patient_id>", methods=["DELETE"])
def care_team_patient_detail(org_id: str, care_team_id: str, patient_id: str):
    """Remover paciente del equipo."""
    return _proxy_request(f"/admin/organizations/{org_id}/care-teams/{care_team_id}/patients/{patient_id}", request.method)


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
@bp.route("/organizations/<org_id>/alerts/", methods=["GET", "POST"])
def alerts(org_id: str):
    """Lista o crea alertas de la organización."""
    return _proxy_request(f"/admin/organizations/{org_id}/alerts/", request.method)


@bp.route("/organizations/<org_id>/alerts/<alert_id>", methods=["GET", "PATCH", "DELETE"])
def alert_detail(org_id: str, alert_id: str):
    """Detalle de una alerta."""
    return _proxy_request(f"/admin/organizations/{org_id}/alerts/{alert_id}", request.method)


@bp.route("/organizations/<org_id>/alerts/<alert_id>/ack", methods=["POST"])
def alert_ack(org_id: str, alert_id: str):
    """Acusar alerta."""
    return _proxy_request(f"/admin/organizations/{org_id}/alerts/{alert_id}/ack", "POST")


@bp.route("/organizations/<org_id>/alerts/<alert_id>/resolve", methods=["POST"])
def alert_resolve(org_id: str, alert_id: str):
    """Resolver alerta."""
    return _proxy_request(f"/admin/organizations/{org_id}/alerts/{alert_id}/resolve", "POST")


# Rutas de dispositivos
@bp.route("/organizations/<org_id>/devices/", methods=["GET", "POST"])
def devices(org_id: str):
    """Lista o crea dispositivos."""
    return _proxy_request(f"/admin/organizations/{org_id}/devices/", request.method)


@bp.route("/organizations/<org_id>/devices/<device_id>", methods=["GET", "PATCH", "DELETE"])
def device_detail(org_id: str, device_id: str):
    """Gestión de un dispositivo específico."""
    return _proxy_request(f"/admin/organizations/{org_id}/devices/{device_id}", request.method)


# Rutas de push devices
@bp.route("/organizations/<org_id>/push-devices/", methods=["GET"])
def push_devices(org_id: str):
    """Lista push devices."""
    return _proxy_request(f"/admin/organizations/{org_id}/push-devices/", "GET")


@bp.route("/organizations/<org_id>/push-devices/<push_device_id>", methods=["PATCH", "DELETE"])
def push_device_detail(org_id: str, push_device_id: str):
    """Gestión de un push device específico."""
    return _proxy_request(f"/admin/organizations/{org_id}/push-devices/{push_device_id}", request.method)


# Rutas de ground truth
@bp.route("/organizations/<org_id>/patients/<patient_id>/ground-truth", methods=["GET", "POST"])
def patient_ground_truth(org_id: str, patient_id: str):
    """Gestión de ground truth labels de un paciente."""
    return _proxy_request(f"/admin/organizations/{org_id}/patients/{patient_id}/ground-truth", request.method)


@bp.route("/organizations/<org_id>/patients/<patient_id>/ground-truth/<label_id>", methods=["GET", "PATCH", "DELETE"])
def patient_ground_truth_detail(org_id: str, patient_id: str, label_id: str):
    """Gestión de un ground truth label específico."""
    return _proxy_request(f"/admin/organizations/{org_id}/patients/{patient_id}/ground-truth/{label_id}", request.method)


# Rutas de ubicaciones de pacientes
@bp.route("/organizations/<org_id>/patients/<patient_id>/locations", methods=["GET", "POST"])
def patient_locations(org_id: str, patient_id: str):
    """Gestión de ubicaciones de un paciente."""
    return _proxy_request(f"/admin/organizations/{org_id}/patients/{patient_id}/locations", request.method)


@bp.route("/organizations/<org_id>/patients/<patient_id>/locations/<location_id>", methods=["DELETE"])
def patient_location_detail(org_id: str, patient_id: str, location_id: str):
    """Eliminar una ubicación específica."""
    return _proxy_request(f"/admin/organizations/{org_id}/patients/{patient_id}/locations/{location_id}", request.method)
