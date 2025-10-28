from flask import Blueprint
from flask_jwt_extended import get_jwt_identity, jwt_required

from repository import get_membership, get_org_by_id, list_orgs_for_user
from responses import err, ok

bp = Blueprint("orgs", __name__, url_prefix="/v1/orgs")


@bp.get("/me")
@jwt_required()
def my_orgs():
    ident = get_jwt_identity()
    if not isinstance(ident, dict) or "user_id" not in ident:
        return err("Identidad inválida", code="identity_invalid", status=401)
    orgs = list_orgs_for_user(ident["user_id"])
    return ok({"organizations": orgs})


@bp.get("")
@jwt_required()
def list_orgs():
    return my_orgs()


@bp.get("/<org_id>")
@jwt_required()
def org_detail(org_id):
    ident = get_jwt_identity()
    if not isinstance(ident, dict) or "user_id" not in ident:
        return err("Identidad inválida", code="identity_invalid", status=401)
    membership = get_membership(ident["user_id"], org_id)
    if not membership:
        return err("No perteneces a esta organización", code="forbidden", status=403)
    org = get_org_by_id(org_id)
    if not org:
        return err("Organización no encontrada", code="not_found", status=404)
    return ok({"organization": org, "membership": membership})
