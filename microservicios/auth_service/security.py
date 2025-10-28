from datetime import datetime, timedelta, timezone
from passlib.hash import bcrypt
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jwt, get_jwt_identity
)
from config import settings

def hash_password(plain: str) -> str:
    return bcrypt.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.verify(plain, hashed)
    except Exception:
        return False

def make_tokens(identity_payload: dict):
    access = create_access_token(
        identity=identity_payload,
        additional_claims={"type": "access"},
        expires_delta=timedelta(minutes=settings.ACCESS_TTL_MIN)
    )
    refresh = create_refresh_token(
        identity=identity_payload,
        additional_claims={"type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TTL_DAYS)
    )
    return access, refresh

def now_utc():
    return datetime.now(timezone.utc)

def require_org_match(token_org_id: str, requested_org_id: str) -> bool:
    if not requested_org_id:
        return True
    return str(token_org_id or "") == str(requested_org_id)
