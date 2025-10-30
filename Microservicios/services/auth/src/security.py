import os
import uuid
from datetime import datetime, timedelta

import jwt
from passlib.context import CryptContext

JWT_SECRET = os.getenv("auth_JWT_SECRET", "super-secret")
JWT_EXPIRES_IN = int(os.getenv("auth_JWT_EXPIRES_IN", "3600"))
REFRESH_TOKEN_TTL = int(os.getenv("auth_REFRESH_TOKEN_TTL", "1209600"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def _base_claims(user):
    return {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "org_id": user.organization_id,
        "iat": datetime.utcnow()
    }


def generate_access_token(user):
    claims = _base_claims(user)
    jti = str(uuid.uuid4())
    claims.update({
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRES_IN),
        "jti": jti
    })
    token = jwt.encode(claims, JWT_SECRET, algorithm="HS256")
    return token, jti


def generate_refresh_token(user):
    jti = str(uuid.uuid4())
    payload = {
        "sub": user.id,
        "type": "refresh",
        "jti": jti,
        "exp": datetime.utcnow() + timedelta(seconds=REFRESH_TOKEN_TTL)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token, jti


def decode_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
