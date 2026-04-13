import logging
import redis
from fastapi import Request, HTTPException
from app.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)


def rate_limit(request: Request, max_requests: int = 5, window: int = 60):
    """基于 Redis 的固定窗口限流（用于登录、刷新等敏感接口）"""
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{client_ip}:{request.url.path}"
    try:
        current = get_redis_client().get(key)
        if current is not None and int(current) >= max_requests:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
        pipe = get_redis_client().pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        pipe.execute()
    except HTTPException:
        raise
    except redis.RedisError as e:
        logger.warning("Rate limiter degraded due to Redis error: %s", e)
        # Redis 不可用时降级为不限流，避免阻断正常业务
        pass
    except Exception:
        # 其他未知异常同样降级
        pass
