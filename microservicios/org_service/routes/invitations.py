import uuid

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from config import settings
from repository import (
    accept_invitation,
    create_invitation,
    fetch_invitation_by_token,
    is_org_admin,
    list_invitations,
)
from responses import err, ok

bp = Blueprint("invitations", __name__, url_prefix="/v1/invitations")

@bp.post("")
@jwt_required()
def send_invitation():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    org_id = data.get("org_id")
    role_code = (data.get("role_code") or "").strip().lower() or None

    if not email or not org_id:
        return err("Faltan parámetros: email y org_id", status=422)

    ident = get_jwt_identity()
    if not isinstance(ident, dict) or "user_id" not in ident:
        return err("Identidad inválida", code="identity_invalid", status=401)
    # Verificar que el usuario sea admin de ESA organización
    if not is_org_admin(ident["user_id"], org_id):
        return err("No tienes permisos para invitar en esta organización",
                   code="forbidden", status=403)

    token = str(uuid.uuid4())
    effective_role = role_code or settings.DEFAULT_INVITATION_ROLE
    try:
        invitation_id = create_invitation(org_id, email, ident["user_id"], token, role_code=effective_role)
    except ValueError as exc:
        if str(exc) == "unknown_role":
            return err("Rol de organización inválido", code="invalid_role", status=422)
        raise
    return ok(
        {
            "id": invitation_id,
            "email": email,
            "org_id": org_id,
            "token": token,
            "role_code": effective_role,
        },
        status=201,
    )


@bp.get("/org/<org_id>")
@jwt_required()
def get_invitations(org_id):
    ident = get_jwt_identity()
    if not isinstance(ident, dict) or "user_id" not in ident:
        return err("Identidad inválida", code="identity_invalid", status=401)
    if not is_org_admin(ident["user_id"], org_id):
        return err("No tienes permisos para ver invitaciones de esta organización",
                   code="forbidden", status=403)
    invitations = list_invitations(org_id)
    return ok({"invitations": invitations})

@bp.post("/<token>/accept")
@jwt_required()
def accept(token):
    ident = get_jwt_identity()
    if not isinstance(ident, dict) or "user_id" not in ident:
        return err("Identidad inválida", code="identity_invalid", status=401)
    inv = fetch_invitation_by_token(token)
    if not inv:
        return err("Invitación no encontrada", code="not_found", status=404)
    if inv["status"] != "pending":
        return err("La invitación no está disponible (usada, revocada o expirada)",
                   code="conflict", status=409)
    # Validar email si la invitación tiene destinatario definido
    if inv.get("email") and ident.get("email") and inv["email"].lower() != ident["email"].lower():
        return err("Esta invitación pertenece a otro correo", code="forbidden", status=403)

    try:
        membership = accept_invitation(token, ident["user_id"])
    except ValueError:
        return err("No fue posible aceptar la invitación", code="accept_failed", status=409)
    return ok(
        {
            "organization": {
                "id": membership["org_id"],
                "name": membership["org_name"],
                "role_code": membership["role_code"],
            },
            "user_id": ident["user_id"],
        },
        status=200,
    )
