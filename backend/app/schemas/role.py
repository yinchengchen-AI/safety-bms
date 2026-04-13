from typing import List, Optional
from pydantic import BaseModel, field_validator
from datetime import datetime


class PermissionBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PermissionOut(PermissionBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    data_scope: Optional[str] = "SELF"

    @field_validator("data_scope", mode="before")
    @classmethod
    def _upper_data_scope(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class RoleCreate(RoleBase):
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    data_scope: Optional[str] = None
    permission_ids: Optional[List[int]] = None

    @field_validator("data_scope", mode="before")
    @classmethod
    def _upper_data_scope(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class RoleOut(RoleBase):
    id: int
    created_at: datetime
    permissions: List[PermissionOut] = []

    model_config = {"from_attributes": True}
