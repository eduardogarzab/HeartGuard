import logging
from datetime import datetime, timezone

from redis.exceptions import RedisError

from config import settings
from redis_client import get_redis

_logger = logging.getLogger(__name__)


def _key(token_type: str, jti: str) -> str:
    token_type = token_type or "unknown"
    return f"{settings.REDIS_PREFIX}:revoked:{token_type}:{jti}"


def revoke_token(jti: str, token_type: str, expires_at: int) -> None:
    """Marca un token como revocado utilizando TTL hasta su expiración."""
    if not jti or not expires_at:
        return
    ttl = int(expires_at - datetime.now(timezone.utc).timestamp())
    ttl = max(ttl, 1)
    try:
        get_redis().setex(_key(token_type, jti), ttl, "1")
    except RedisError as exc:  # pragma: no cover - dependencia externa
        _logger.error("Redis revoke failed for %s: %s", jti, exc)


def is_token_revoked(jwt_payload: dict) -> bool:
    jti = jwt_payload.get("jti")
    token_type = jwt_payload.get("type")
    if not jti:
        return True
    try:
        return bool(get_redis().exists(_key(token_type, jti)))
    except RedisError as exc:  # pragma: no cover - dependencia externa
        _logger.error("Redis check failed for %s: %s", jti, exc)
        return False
