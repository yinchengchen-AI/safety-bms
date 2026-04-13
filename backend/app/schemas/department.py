from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None


class DepartmentOut(DepartmentBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DepartmentTreeOut(DepartmentOut):
    children: List["DepartmentTreeOut"] = []

    model_config = {"from_attributes": True}
