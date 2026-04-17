from datetime import date
from decimal import Decimal
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel


class ReportMetaOut(BaseModel):
    id: str
    name: str
    description: str
    supported_filters: List[str]


class ReportPageOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list


# 合同执行情况表
class ContractExecutionRowOut(BaseModel):
    contract_id: int
    contract_no: str
    contract_title: str
    customer_name: Optional[str]
    sign_date: Optional[date]
    total_amount: float
    invoiced_amount: float
    received_amount: float
    receivable_balance: float
    status: str
    service_type: Optional[int]


# 服务订单完成情况表
class ServiceOrderCompletionRowOut(BaseModel):
    order_id: int
    order_no: str
    title: str
    customer_name: Optional[str]
    contract_no: Optional[str]
    planned_start: Optional[date]
    planned_end: Optional[date]
    actual_start: Optional[date]
    actual_end: Optional[date]
    status: str
    on_time: Optional[bool]
    assignee_name: Optional[str]


# 客户回款分析表
class CustomerPaymentAnalysisRowOut(BaseModel):
    customer_id: int
    customer_name: str
    contract_count: int
    total_contract_amount: float
    total_invoiced_amount: float
    total_received_amount: float
    collection_rate: float


# 发票开具明细表
class InvoiceDetailRowOut(BaseModel):
    invoice_id: int
    invoice_no: str
    contract_no: Optional[str]
    customer_name: Optional[str]
    invoice_type: str
    amount: float
    status: str
    invoice_date: Optional[date]
    applied_by_name: Optional[str]


# 收款明细表
class PaymentDetailRowOut(BaseModel):
    payment_id: int
    payment_no: str
    contract_no: Optional[str]
    customer_name: Optional[str]
    payment_method: str
    amount: float
    payment_date: Optional[date]
    created_by_name: Optional[str]


# 客户台账汇总表
class CustomerLedgerSummaryRowOut(BaseModel):
    customer_id: int
    customer_name: str
    industry: Optional[str]
    contact_name: Optional[str]
    contact_phone: Optional[str]
    contract_count: int
    total_contract_amount: float
    total_invoiced_amount: float
    total_received_amount: float
    status: str
