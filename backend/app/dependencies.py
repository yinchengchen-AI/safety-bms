from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from app.db.session import get_db
from app.core.security import decode_token
from app.crud.user import crud_user
from app.models.user import User
from app.services.auth_service import auth_service

security = HTTPBearer(auto_error=False)


def get_token_from_request(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """优先从 Cookie 获取 token，fallback 到 Authorization Header"""
    token = request.cookies.get("access_token")
    if token:
        return token
    if credentials and credentials.credentials:
        return credentials.credentials
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少认证凭证")


def get_current_user(
    token: str = Depends(get_token_from_request),
    db: Session = Depends(get_db),
) -> User:
    if auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token已失效，请重新登录")

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的Token类型")
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证凭证")

    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def get_current_user_permissions(current_user: User = Depends(get_current_user)) -> List[str]:
    """获取当前用户的全部权限码列表"""
    if current_user.is_superuser:
        from app.core.constants import PermissionCode
        return [p.value for p in PermissionCode]
    codes = set()
    for role in current_user.roles:
        for perm in role.permissions:
            codes.add(perm.code)
    return list(codes)


def require_permissions(*permission_codes: str):
    """权限码守卫工厂函数"""
    def checker(
        current_user: User = Depends(get_current_user),
        permissions: List[str] = Depends(get_current_user_permissions),
    ) -> User:
        if current_user.is_superuser:
            return current_user
        if not permission_codes:
            return current_user
        missing = [code for code in permission_codes if code not in permissions]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return current_user
    return checker


def require_roles(*role_names: str):
    """角色守卫工厂函数"""
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user
        user_roles = {r.name.lower() for r in current_user.roles}
        required = {r.lower() for r in role_names}
        if not user_roles & required:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="角色权限不足")
        return current_user
    return checker
