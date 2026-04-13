"""
权限撤销工具：当角色或用户权限变更时，强制相关用户重新登录。
"""
from app.utils.redis_client import get_redis_client
from app.services.auth_service import REFRESH_TOKEN_PREFIX


def revoke_user_refresh_tokens(user_ids: list[int]) -> None:
    """删除指定用户的 refresh_token，使其下次访问刷新接口时被迫重新登录。"""
    redis = get_redis_client()
    for uid in user_ids:
        redis.delete(f"{REFRESH_TOKEN_PREFIX}{uid}")


def revoke_all_refresh_tokens() -> None:
    """删除全部 refresh_token（慎用）。"""
    redis = get_redis_client()
    for key in redis.scan_iter(match=f"{REFRESH_TOKEN_PREFIX}*"):
        redis.delete(key)
