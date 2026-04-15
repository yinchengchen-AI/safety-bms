from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal

from app.core.constants import ServiceOrderStatus


class ServiceItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    quantity: Decimal = Decimal("1")
    unit: str = "次"
    remark: Optional[str] = None


class ServiceItemCreate(ServiceItemBase):
    pass


class ServiceItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    remark: Optional[str] = None


class ServiceItemOut(ServiceItemBase):
    id: int
    order_id: int

    model_config = {"from_attributes": True}


class ServiceReportOut(BaseModel):
    id: int
    order_id: int
    file_name: str
    file_url: str
    file_size: Optional[int] = None
    remark: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ServiceOrderBase(BaseModel):
    order_no: str
    contract_id: int
    title: str
    service_type: int
    assignee_id: Optional[int] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    remark: Optional[str] = None


class ServiceOrderCreate(ServiceOrderBase):
    items: List[ServiceItemCreate] = []


class ServiceOrderUpdate(BaseModel):
    title: Optional[str] = None
    assignee_id: Optional[int] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    remark: Optional[str] = None


class ServiceOrderStatusUpdate(BaseModel):
    status: ServiceOrderStatus


class ServiceOrderOut(ServiceOrderBase):
    id: int
    status: ServiceOrderStatus
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    created_at: datetime
    customer_name: Optional[str] = None
    assignee_name: Optional[str] = None
    items: List[ServiceItemOut] = []
    reports: List[ServiceReportOut] = []
    service_type_id: int
    service_type_name: Optional[str] = None
    service_type_code: Optional[str] = None

    model_config = {"from_attributes": True}


class ServiceOrderListOut(BaseModel):
    id: int
    order_no: str
    title: str
    contract_id: int
    customer_name: Optional[str] = None
    service_type: int
    service_type_id: int
    service_type_name: Optional[str] = None
    service_type_code: Optional[str] = None
    status: ServiceOrderStatus
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}
