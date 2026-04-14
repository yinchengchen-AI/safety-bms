from typing import Optional
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal

from app.core.constants import InvoiceType, InvoiceStatus


class InvoiceBase(BaseModel):
    invoice_no: str
    contract_id: int
    invoice_type: InvoiceType
    amount: Decimal
    tax_rate: Decimal = Decimal("0.06")
    invoice_title: Optional[str] = None
    tax_number: Optional[str] = None
    remark: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None
    invoice_date: Optional[date] = None
    actual_invoice_no: Optional[str] = None
    file_url: Optional[str] = None
    remark: Optional[str] = None


class InvoiceOut(InvoiceBase):
    id: int
    status: InvoiceStatus
    tax_amount: Optional[Decimal] = None
    invoice_date: Optional[date] = None
    actual_invoice_no: Optional[str] = None
    file_url: Optional[str] = None
    applied_by: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceListOut(BaseModel):
    id: int
    invoice_no: str
    contract_id: int
    customer_name: Optional[str] = None
    invoice_type: InvoiceType
    status: InvoiceStatus
    amount: Decimal
    tax_rate: Decimal
    invoice_date: Optional[date] = None
    remark: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
