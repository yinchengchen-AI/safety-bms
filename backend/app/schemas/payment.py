from typing import Optional
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal

from app.core.constants import PaymentMethod


class PaymentBase(BaseModel):
    payment_no: str
    contract_id: int
    invoice_id: Optional[int] = None
    amount: Decimal
    payment_method: PaymentMethod
    payment_date: date
    bank_account: Optional[str] = None
    transaction_ref: Optional[str] = None
    remark: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    payment_date: Optional[date] = None
    bank_account: Optional[str] = None
    transaction_ref: Optional[str] = None
    file_url: Optional[str] = None
    remark: Optional[str] = None


class PaymentOut(PaymentBase):
    id: int
    file_url: Optional[str] = None
    is_overdue: bool = False
    created_by: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentListOut(BaseModel):
    id: int
    payment_no: str
    contract_id: int
    contract_no: Optional[str] = None
    invoice_id: Optional[int] = None
    customer_name: Optional[str] = None
    amount: Decimal
    payment_method: PaymentMethod
    payment_date: date
    is_overdue: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ContractReceivable(BaseModel):
    """合同应收款信息"""
    contract_id: int
    contract_no: str
    total_amount: Decimal
    received_amount: Decimal
    receivable_amount: Decimal
    is_overdue: bool
