from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ServiceTypeBase(BaseModel):
    code: str
    name: str
    default_price: Decimal | None = None
    standard_duration_days: int | None = None
    qualification_requirements: str | None = None
    default_contract_template_id: int | None = None
    is_active: bool = True


class ServiceTypeCreate(ServiceTypeBase):
    pass


class ServiceTypeUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    default_price: Decimal | None = None
    standard_duration_days: int | None = None
    qualification_requirements: str | None = None
    default_contract_template_id: int | None = None
    is_active: bool | None = None


class ServiceTypeOut(ServiceTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
