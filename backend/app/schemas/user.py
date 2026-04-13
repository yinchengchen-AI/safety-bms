from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
import re


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


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
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role_ids: List[int] = []
    department_id: Optional[int] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须同时包含字母和数字")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role_ids: Optional[List[int]] = None
    department_id: Optional[int] = None


class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    avatar_url: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    roles: List[RoleOut] = []
    permissions: List[str] = []
    department_id: Optional[int] = None

    model_config = {"from_attributes": True}


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
