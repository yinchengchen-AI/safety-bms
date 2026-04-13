from datetime import datetime, timezone
from typing import Optional
from hashlib import sha256
from sqlalchemy.orm import Session
from jose import JWTError

from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.exceptions import BusinessError
from app.crud.user import crud_user
from app.models.user import User
from app.utils.redis_client import get_redis_client
from app.config import settings

TOKEN_BLACKLIST_PREFIX = "token:blacklist:"
REFRESH_TOKEN_PREFIX = "token:refresh:"


def _token_blacklist_key(token: str) -> str:
    return f"{TOKEN_BLACKLIST_PREFIX}{sha256(token.encode()).hexdigest()}"


class AuthService:
    def login(self, db: Session, *, username: str, password: str) -> dict:
        user = crud_user.authenticate(db, username=username, password=password)
        if not user:
            raise BusinessError("用户名或密码错误", status_code=401)
        if not user.is_active:
            raise BusinessError("账号已被禁用", status_code=403)

        role_names = [r.name for r in user.roles]
        access_token = create_access_token(
            subject=user.id,
            extra_data={"roles": role_names, "username": user.username},
        )
        refresh_token = create_refresh_token(subject=user.id)

        # 缓存 refresh token
        get_redis_client().setex(
            f"{REFRESH_TOKEN_PREFIX}{user.id}",
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            refresh_token,
        )

        # 更新最后登录时间
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def logout(self, *, token: str) -> None:
        """将 access token 加入黑名单"""
        try:
            payload = decode_token(token)
            exp = payload.get("exp", 0)
            ttl = max(0, int(exp - datetime.now(timezone.utc).timestamp()))
            if ttl > 0:
                get_redis_client().setex(_token_blacklist_key(token), ttl, "1")
        except JWTError:
            pass  # 无效token直接忽略

    def is_token_blacklisted(self, token: str) -> bool:
        return get_redis_client().exists(_token_blacklist_key(token)) > 0

    def refresh_access_token(self, db: Session, *, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise BusinessError("无效的刷新Token", status_code=401)
            user_id = int(payload["sub"])
        except JWTError:
            raise BusinessError("无效的刷新Token", status_code=401)

        cached = get_redis_client().get(f"{REFRESH_TOKEN_PREFIX}{user_id}")
        if not cached or cached.decode() != refresh_token:
            raise BusinessError("刷新Token已失效，请重新登录", status_code=401)

        user = crud_user.get(db, id=user_id)
        if not user or not user.is_active:
            raise BusinessError("用户不存在或已被禁用", status_code=401)

        role_names = [r.name for r in user.roles]
        new_access_token = create_access_token(
            subject=user.id,
            extra_data={"roles": role_names, "username": user.username},
        )
        return {"access_token": new_access_token, "token_type": "bearer"}


auth_service = AuthService()
