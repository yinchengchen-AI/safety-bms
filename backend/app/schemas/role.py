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


class RoleOut(RoleBase):
    id: int
    created_at: datetime
    permissions: list[PermissionOut] = []

    model_config = {"from_attributes": True}
