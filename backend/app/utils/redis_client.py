import threading

import redis

from app.config import settings

_redis_pool: redis.ConnectionPool | None = None
_redis_client: redis.Redis | None = None
_lock = threading.Lock()


def get_redis_client() -> redis.Redis:
    """延迟初始化 Redis 客户端"""
    global _redis_pool, _redis_client
    if _redis_client is None:
        with _lock:
            if _redis_client is None:
                _redis_pool = redis.ConnectionPool.from_url(
                    settings.REDIS_URL, decode_responses=False
                )
                _redis_client = redis.Redis(connection_pool=_redis_pool)
    return _redis_client
