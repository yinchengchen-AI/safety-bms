from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.core.constants import PaymentMethod


class PaymentBase(BaseModel):
    payment_no: str
    contract_id: int
    invoice_id: int | None = None
    amount: Decimal
    payment_method: PaymentMethod
    payment_date: date
    bank_account: str | None = None
    transaction_ref: str | None = None
    remark: str | None = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    payment_date: date | None = None
    bank_account: str | None = None
    transaction_ref: str | None = None
    file_url: str | None = None
    remark: str | None = None


class PaymentOut(PaymentBase):
    id: int
    file_url: str | None = None
    is_overdue: bool = False
    created_by: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentListOut(BaseModel):
    id: int
    payment_no: str
    contract_id: int
    contract_no: str | None = None
    invoice_id: int | None = None
    customer_name: str | None = None
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
