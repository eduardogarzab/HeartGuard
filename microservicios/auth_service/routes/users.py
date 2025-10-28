from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from responses import ok, err
from repository import create_user, fetch_user_by_email
from security import hash_password

bp = Blueprint("users", __name__, url_prefix="/v1/users")

@bp.post("")
def register_user():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user_status_id = data.get("user_status_id")  # pásalo desde seed (p.ej. status 'active')

    if not name or not email or not password or not user_status_id:
        return err("name, email, password, user_status_id son requeridos", status=422)

    if fetch_user_by_email(email):
        return err("Email ya registrado", code="email_taken", status=409)

    user_id = create_user(name, email, hash_password(password), user_status_id)
    return ok({"id": user_id, "email": email, "name": name}, status=201)

@bp.get("/me")
@jwt_required()
def me():
    identity = get_jwt_identity()  # dict con user_id, email, org_id, etc.
    return ok({"identity": identity})
