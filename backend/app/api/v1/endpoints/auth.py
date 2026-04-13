from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserLogin, UserOut
from app.schemas.common import Token, ResponseMsg
from app.services.auth_service import auth_service, REFRESH_TOKEN_PREFIX
from app.dependencies import get_current_user, get_token_from_request, get_current_user_permissions
from app.models.user import User
from app.config import settings
from app.core.rate_limit import rate_limit
from app.utils.redis_client import get_redis_client
from app.core.exceptions import BusinessError
from app.crud.user import crud_user

router = APIRouter(prefix="/auth", tags=["认证"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str | None = None) -> None:
    """设置 httpOnly、Secure、SameSite=Strict Cookie"""
    cookie_kwargs = {
        "httponly": True,
        "secure": False if settings.DEBUG else True,
        "samesite": "lax" if settings.DEBUG else "strict",
        "max_age": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    response.set_cookie(key="access_token", value=access_token, **cookie_kwargs)
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False if settings.DEBUG else True,
            samesite="lax" if settings.DEBUG else "strict",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        )


@router.post("/login", response_model=Token)
def login(
    body: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit),
):
    result = auth_service.login(db, username=body.username, password=body.password)
    _set_auth_cookies(response, result["access_token"], result.get("refresh_token"))
    return result


@router.post("/logout", response_model=ResponseMsg)
def logout(
    response: Response,
    token: str = Depends(get_token_from_request),
    _: User = Depends(get_current_user),
):
    auth_service.logout(token=token)
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "已成功退出登录"}


@router.post("/refresh", response_model=dict)
def refresh_token(
    body: dict,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit),
):
    refresh_token = body.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="缺少 refresh_token")
    result = auth_service.refresh_access_token(db, refresh_token=refresh_token)
    _set_auth_cookies(response, result["access_token"])
    return result


@router.get("/me", response_model=UserOut)
def get_me(
    current_user: User = Depends(get_current_user),
    permissions: list[str] = Depends(get_current_user_permissions),
):
    data = UserOut.model_validate(current_user)
    result = data.model_dump()
    result["permissions"] = permissions
    return result


@router.post("/force-relogin/{user_id}", response_model=dict)
def force_relogin(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """强制指定用户重新登录（仅 superuser 可用）：删除 Redis 中的 refresh_token。"""
    if not current_user.is_superuser:
        raise BusinessError("权限不足", status_code=403)
    target_user = crud_user.get(db, id=user_id)
    if not target_user:
        raise BusinessError("用户不存在", status_code=404)
    # 删除 refresh token
    get_redis_client().delete(f"{REFRESH_TOKEN_PREFIX}{user_id}")
    return {"message": "已强制用户重新登录"}
