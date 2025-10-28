import logging
from functools import lru_cache

import redis
from redis.exceptions import RedisError

from config import settings

_logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_redis() -> redis.Redis:
    """Devuelve un cliente Redis compartido usando la URL configurada."""
    client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        client.ping()
    except RedisError as exc:  # pragma: no cover - solo en entorno sin Redis
        _logger.warning("Redis ping failed: %s", exc)
    return client
