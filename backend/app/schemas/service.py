from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.core.constants import ServiceOrderStatus


class ServiceItemBase(BaseModel):
    name: str
    description: str | None = None
    quantity: Decimal = Decimal("1")
    unit: str = "次"
    remark: str | None = None


class ServiceItemCreate(ServiceItemBase):
    pass


class ServiceItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    remark: str | None = None


class ServiceItemOut(ServiceItemBase):
    id: int
    order_id: int

    model_config = {"from_attributes": True}


class ServiceReportOut(BaseModel):
    id: int
    order_id: int
    file_name: str
    file_url: str
    file_size: int | None = None
    remark: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ServiceOrderBase(BaseModel):
    order_no: str
    contract_id: int
    title: str
    service_type: int
    assignee_id: int | None = None
    planned_start: date | None = None
    planned_end: date | None = None
    remark: str | None = None


class ServiceOrderCreate(ServiceOrderBase):
    items: list[ServiceItemCreate] = []


class ServiceOrderUpdate(BaseModel):
    title: str | None = None
    assignee_id: int | None = None
    planned_start: date | None = None
    planned_end: date | None = None
    actual_start: date | None = None
    actual_end: date | None = None
    remark: str | None = None


class ServiceOrderStatusUpdate(BaseModel):
    status: ServiceOrderStatus


class ServiceOrderOut(ServiceOrderBase):
    id: int
    status: ServiceOrderStatus
    actual_start: date | None = None
    actual_end: date | None = None
    created_at: datetime
    customer_name: str | None = None
    assignee_name: str | None = None
    items: list[ServiceItemOut] = []
    reports: list[ServiceReportOut] = []
    service_type_id: int
    service_type_name: str | None = None
    service_type_code: str | None = None

    model_config = {"from_attributes": True}


class ServiceOrderListOut(BaseModel):
    id: int
    order_no: str
    title: str
    contract_id: int
    customer_name: str | None = None
    service_type: int
    service_type_id: int
    service_type_name: str | None = None
    service_type_code: str | None = None
    status: ServiceOrderStatus
    assignee_id: int | None = None
    assignee_name: str | None = None
    planned_start: date | None = None
    planned_end: date | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
