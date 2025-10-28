from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from responses import ok, err
from repository import (
    fetch_primary_org_for_user,
    fetch_user_by_email,
    insert_refresh_token,
    revoke_refresh_token,
    is_refresh_token_active,
)
from security import verify_password, make_tokens, now_utc
from datetime import timedelta
import hashlib
from config import settings
from token_store import revoke_token

bp = Blueprint("auth", __name__, url_prefix="/v1/auth")

def _hash_for_store(token: str) -> str:
    # Guardar solo hash del refresh token (no en claro)
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _current_refresh_token() -> str:
    header = request.headers.get("Authorization", "")
    if not header:
        return ""
    parts = header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return ""

@bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    org_id = request.headers.get("X-Org-ID") or payload.get("org_id") or settings.DEFAULT_ORG_ID

    user = fetch_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        return err("Credenciales inválidas", code="invalid_credentials", status=401)

    if not org_id:
        org_id = fetch_primary_org_for_user(user["id"]) or ""

    identity = {
        "user_id": user["id"],
        "email": user["email"],
        "org_id": org_id,   # org seleccionada en el contexto del cliente
        "global_role": "user"  # opcional: puedes calcularlo con fetch_user_roles si quieres
    }
    access, refresh = make_tokens(identity)

    # Guardar el refresh token hash con expiración
    refresh_exp = now_utc() + timedelta(days=settings.REFRESH_TTL_DAYS)
    insert_refresh_token(user["id"], _hash_for_store(refresh), refresh_exp)

    return ok({
        "access_token": access,
        "refresh_token": refresh,
        "user": {"id": user["id"], "email": user["email"], "name": user["name"], "org_id": org_id}
    })

@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    user_id = identity.get("user_id") if isinstance(identity, dict) else None
    raw_refresh = _current_refresh_token()
    if not raw_refresh:
        return err("Falta refresh token", status=401)
    refresh_hash = _hash_for_store(raw_refresh)
    if not user_id or not is_refresh_token_active(user_id, refresh_hash):
        return err("Refresh token revocado", code="refresh_revoked", status=401)
    # (Opcional) Validar el refresh en BD si quieres bloqueo inmediato por revocación granural.
    access, _ = make_tokens(identity)
    return ok({"access_token": access})

@bp.post("/logout")
@jwt_required(refresh=True)
def logout():
    identity = get_jwt_identity()
    claims = get_jwt()
    user_id = identity.get("user_id") if isinstance(identity, dict) else None
    if not user_id:
        return err("Identidad inválida para revocar token", status=401)
    payload = request.get_json(silent=True) or {}
    refresh_token = payload.get("refresh_token") or _current_refresh_token()
    if not refresh_token:
        return err("Falta refresh_token para revocar", status=400)
    refresh_hash = _hash_for_store(refresh_token)
    if user_id:
        revoke_refresh_token(user_id, refresh_hash)
    revoke_token(claims.get("jti"), claims.get("type"), claims.get("exp"))
    return ok({"message": "Refresh token revocado"})
