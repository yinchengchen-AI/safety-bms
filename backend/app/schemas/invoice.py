from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.constants import InvoiceStatus, InvoiceType


class InvoiceBase(BaseModel):
    invoice_no: str
    contract_id: int
    invoice_type: InvoiceType
    amount: Decimal
    tax_rate: Decimal = Decimal("0.06")
    invoice_title: str | None = None
    tax_number: str | None = None
    remark: str | None = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    status: InvoiceStatus | None = None
    invoice_date: date | None = None
    actual_invoice_no: str | None = None
    file_url: str | None = None
    remark: str | None = None


class InvoiceOut(InvoiceBase):
    id: int
    status: InvoiceStatus
    tax_amount: Decimal | None = None
    invoice_date: date | None = None
    actual_invoice_no: str | None = None
    file_url: str | None = None
    applied_by: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceListOut(BaseModel):
    id: int
    invoice_no: str
    contract_id: int
    customer_name: str | None = None
    invoice_type: InvoiceType
    status: InvoiceStatus
    amount: Decimal
    tax_rate: Decimal
    invoice_date: date | None = None
    remark: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceAuditRequest(BaseModel):
    action: str = Field(..., description="审核动作: approve 或 reject")
    remark: str | None = Field(None, description="审核备注")
    invoice_date: date | None = Field(None, description="开票日期（通过时必填）")
    actual_invoice_no: str | None = Field(None, description="实际发票号（通过时必填）")
