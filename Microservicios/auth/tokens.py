import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import jwt
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret")
JWT_EXPIRES_IN = int(os.getenv("JWT_EXPIRES_IN", "900"))
REFRESH_TOKEN_TTL = int(os.getenv("REFRESH_TOKEN_TTL", "604800"))

redis_client: Optional[redis.Redis] = None


def _get_client() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL)
    return redis_client


def generate_access_token(user_id: str, role: str, org_id: str, expires_in_s: int = JWT_EXPIRES_IN, secret: str = JWT_SECRET) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "org_id": org_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in_s)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str, secret: str = JWT_SECRET) -> dict:
    return jwt.decode(token, secret, algorithms=["HS256"])


def generate_refresh_token() -> str:
    return str(uuid4())


def store_refresh_token(token: str, user_id: str) -> None:
    client = _get_client()
    client.setex(f"refresh:{token}", REFRESH_TOKEN_TTL, value=user_id)


def revoke_refresh_token(token: str) -> None:
    client = _get_client()
    client.delete(f"refresh:{token}")


def is_refresh_token_valid(token: str) -> Optional[str]:
    client = _get_client()
    value = client.get(f"refresh:{token}")
    if value is None:
        return None
    return value.decode("utf-8")
