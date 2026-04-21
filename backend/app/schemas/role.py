from datetime import datetime

from pydantic import BaseModel, field_validator


class PermissionBase(BaseModel):
    code: str
    name: str
    description: str | None = None


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class PermissionOut(PermissionBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleBase(BaseModel):
    name: str
    description: str | None = None
    data_scope: str | None = "SELF"

    @field_validator("data_scope", mode="before")
    @classmethod
    def _upper_data_scope(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class RoleCreate(RoleBase):
    permission_ids: list[int] = []


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    data_scope: str | None = None
    permission_ids: list[int] | None = None

    @field_validator("data_scope", mode="before")
    @classmethod
    def _upper_data_scope(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v

    @field_validator("permission_ids", mode="before")
    @classmethod
    def _clean_permission_ids(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            # 过滤 null/undefined，将字符串数字转为整数
            return [
                int(x) if isinstance(x, str) and x.strip() != "" else x
                for x in v
                if x is not None and x != ""
            ]
        return v


class RoleOut(RoleBase):
    id: int
    created_at: datetime
    permissions: list[PermissionOut] = []

    model_config = {"from_attributes": True}
