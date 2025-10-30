import os
import time
from typing import Optional

import redis

RATE_LIMIT = int(os.getenv("RATE_LIMIT", "60"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client: Optional[redis.Redis] = None


def get_client() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL)
    return redis_client


def check_rate_limit(client_ip: str, endpoint: str) -> bool:
    if RATE_LIMIT <= 0:
        return True
    key = f"rate:{client_ip}:{endpoint}:{int(time.time() // 60)}"
    client = get_client()
    current = client.incr(key)
    if current == 1:
        client.expire(key, 120)
    return current <= RATE_LIMIT
