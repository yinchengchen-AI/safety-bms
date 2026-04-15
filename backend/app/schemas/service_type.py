from typing import Optional
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime


class ServiceTypeBase(BaseModel):
    code: str
    name: str
    default_price: Optional[Decimal] = None
    standard_duration_days: Optional[int] = None
    qualification_requirements: Optional[str] = None
    default_contract_template_id: Optional[int] = None
    is_active: bool = True


class ServiceTypeCreate(ServiceTypeBase):
    pass


class ServiceTypeUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    default_price: Optional[Decimal] = None
    standard_duration_days: Optional[int] = None
    qualification_requirements: Optional[str] = None
    default_contract_template_id: Optional[int] = None
    is_active: Optional[bool] = None


class ServiceTypeOut(ServiceTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
