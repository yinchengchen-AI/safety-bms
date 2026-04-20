from datetime import date

from pydantic import BaseModel


class ReportMetaOut(BaseModel):
    id: str
    name: str
    description: str
    supported_filters: list[str]


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
    customer_name: str | None
    sign_date: date | None
    total_amount: float
    invoiced_amount: float
    received_amount: float
    receivable_balance: float
    status: str
    service_type: int | None


# 服务订单完成情况表
class ServiceOrderCompletionRowOut(BaseModel):
    order_id: int
    order_no: str
    title: str
    customer_name: str | None
    contract_no: str | None
    planned_start: date | None
    planned_end: date | None
    actual_start: date | None
    actual_end: date | None
    status: str
    on_time: bool | None
    assignee_name: str | None


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
    contract_no: str | None
    customer_name: str | None
    invoice_type: str
    amount: float
    status: str
    invoice_date: date | None
    applied_by_name: str | None


# 收款明细表
class PaymentDetailRowOut(BaseModel):
    payment_id: int
    payment_no: str
    contract_no: str | None
    customer_name: str | None
    payment_method: str
    amount: float
    payment_date: date | None
    created_by_name: str | None


# 客户台账汇总表
class CustomerLedgerSummaryRowOut(BaseModel):
    customer_id: int
    customer_name: str
    industry: str | None
    contact_name: str | None
    contact_phone: str | None
    contract_count: int
    total_contract_amount: float
    total_invoiced_amount: float
    total_received_amount: float
    status: str
