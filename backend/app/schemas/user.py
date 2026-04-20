import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


def _presign_avatar_url(v: str | None) -> str | None:
    if isinstance(v, str) and v and not v.startswith("http"):
        try:
            from app.services.minio_service import minio_service

            return minio_service.get_presigned_url(v)
        except Exception:
            return v
    return v


class RoleBase(BaseModel):
    name: str
    description: str | None = None


class RoleCreate(RoleBase):
    pass


class RoleOut(RoleBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PermissionOut(BaseModel):
    id: int
    code: str
    name: str
    module: str

    model_config = {"from_attributes": True}


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None
    phone: str | None = None


class UserCreate(UserBase):
    password: str
    role_ids: list[int] = []
    department_id: int | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须同时包含字母和数字")
        return v


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None
    role_ids: list[int] | None = None
    department_id: int | None = None


class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    avatar_url: str | None = None
    last_login_at: datetime | None = None
    created_at: datetime
    roles: list[RoleOut] = []
    permissions: list[str] = []
    department_id: int | None = None

    model_config = {"from_attributes": True}

    @field_validator("avatar_url", mode="before")
    @classmethod
    def presign_avatar_url(cls, v):
        return _presign_avatar_url(v)


class UserLogin(BaseModel):
    username: str
    password: str


class PasswordChange(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须同时包含字母和数字")
        return v


class PasswordReset(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须同时包含字母和数字")
        return v
