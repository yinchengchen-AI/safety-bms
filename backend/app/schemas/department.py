from datetime import datetime

from pydantic import BaseModel


class DepartmentBase(BaseModel):
    name: str
    description: str | None = None
    parent_id: int | None = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    parent_id: int | None = None


class DepartmentOut(DepartmentBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DepartmentTreeOut(DepartmentOut):
    children: list["DepartmentTreeOut"] = []

    model_config = {"from_attributes": True}
