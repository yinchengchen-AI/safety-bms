from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.constants import (
    PermissionCode,
)
from app.db.session import get_db
from app.dependencies import require_permissions
from app.models.contract import Contract
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.service import ServiceOrder
from app.models.service_type import ServiceType as ServiceTypeModel
from app.models.user import User
from app.schemas.reports import (
    ContractExecutionRowOut,
    CustomerLedgerSummaryRowOut,
    CustomerPaymentAnalysisRowOut,
    InvoiceDetailRowOut,
    PaymentDetailRowOut,
    ReportMetaOut,
    ReportPageOut,
    ServiceOrderCompletionRowOut,
)
from app.utils.data_scope import apply_data_scope
from app.utils.enum_format import enum_value
from app.utils.excel_export import export_excel_response
from app.utils.export_mappings import (
    CONTRACT_STATUS_MAP,
    CUSTOMER_STATUS_MAP,
    INVOICE_STATUS_MAP,
    INVOICE_TYPE_MAP,
    PAYMENT_METHOD_MAP,
    SERVICE_ORDER_STATUS_MAP,
    map_value,
)
from app.utils.pagination import make_page_response

router = APIRouter(prefix="/reports", tags=["报表中心"])

REPORTS_META = [
    {
        "id": "contract-execution",
        "name": "合同执行情况表",
        "description": "展示合同的签约额、已开票、已收款及应收余额",
        "supported_filters": ["date_range", "service_type", "status"],
    },
    {
        "id": "service-order-completion",
        "name": "服务订单完成情况表",
        "description": "展示服务订单的计划/实际日期、完成状态及按期情况",
        "supported_filters": ["date_range", "service_type", "status"],
    },
    {
        "id": "customer-payment-analysis",
        "name": "客户回款分析表",
        "description": "按客户汇总合同金额、开票金额、收款金额及回款率",
        "supported_filters": ["date_range"],
    },
    {
        "id": "invoice-detail",
        "name": "发票开具明细表",
        "description": "展示发票开具的明细记录",
        "supported_filters": ["date_range", "status"],
    },
    {
        "id": "payment-detail",
        "name": "收款明细表",
        "description": "展示收款记录的明细",
        "supported_filters": ["date_range", "payment_method"],
    },
    {
        "id": "customer-ledger-summary",
        "name": "客户台账汇总表",
        "description": "展示客户档案及关联的合同、金额汇总",
        "supported_filters": ["date_range", "status"],
    },
]


def _to_float(value) -> float:
    return float(value) if value is not None else 0.0


def _to_int(value) -> int:
    return int(value) if value is not None else 0


@router.get("", response_model=list[ReportMetaOut])
def list_reports(
    _current_user: User = Depends(require_permissions(PermissionCode.REPORT_READ)),
):
    return [ReportMetaOut(**meta) for meta in REPORTS_META]


@router.get("/contract-execution", response_model=ReportPageOut)
def contract_execution_report(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    service_type: int | None = None,
    status: str | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.REPORT_READ)),
    db: Session = Depends(get_db),
):
    invoiced_sub = (
        db.query(Invoice.contract_id, func.coalesce(func.sum(Invoice.amount), 0).label("total"))
        .group_by(Invoice.contract_id)
        .subquery()
    )
    received_sub = (
        db.query(Payment.contract_id, func.coalesce(func.sum(Payment.amount), 0).label("total"))
        .group_by(Payment.contract_id)
        .subquery()
    )

    query = (
        db.query(
            Contract,
            func.coalesce(invoiced_sub.c.total, 0).label("invoiced_amount"),
            func.coalesce(received_sub.c.total, 0).label("received_amount"),
        )
        .outerjoin(invoiced_sub, Contract.id == invoiced_sub.c.contract_id)
        .outerjoin(received_sub, Contract.id == received_sub.c.contract_id)
        .filter(Contract.is_deleted == False)
    )

    if date_from:
        query = query.filter(Contract.sign_date >= date_from)
    if date_to:
        query = query.filter(Contract.sign_date <= date_to)
    if service_type:
        query = query.filter(Contract.service_type == service_type)
    if status:
        query = query.filter(Contract.status == status)

    query = apply_data_scope(query, Contract, current_user)
    total = query.count()

    results = (
        query.options(joinedload(Contract.customer))
        .order_by(Contract.sign_date.desc(), Contract.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for contract, invoiced, received in results:
        total_amount = float(getattr(contract, "total_amount", 0) or 0)
        items.append(
            ContractExecutionRowOut(
                contract_id=contract.id,
                contract_no=contract.contract_no,
                contract_title=contract.title,
                customer_name=contract.customer.name if contract.customer else None,
                sign_date=contract.sign_date,
                total_amount=round(total_amount, 2),
                invoiced_amount=round(_to_float(invoiced), 2),
                received_amount=round(_to_float(received), 2),
                receivable_balance=round(total_amount - _to_float(received), 2),
                status=enum_value(contract.status),
                service_type=contract.service_type,
            )
        )

    return make_page_response(total, items, page, page_size)


@router.get("/service-order-completion", response_model=ReportPageOut)
def service_order_completion_report(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    service_type: int | None = None,
    status: str | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.REPORT_READ)),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            ServiceOrder,
            Customer.name.label("customer_name"),
            Contract.contract_no.label("contract_no"),
            User.full_name.label("assignee_name"),
            ServiceTypeModel.code.label("service_type"),
        )
        .join(Contract, ServiceOrder.contract_id == Contract.id)
        .outerjoin(Customer, Contract.customer_id == Customer.id)
        .outerjoin(User, ServiceOrder.assignee_id == User.id)
        .outerjoin(ServiceTypeModel, ServiceOrder.service_type == ServiceTypeModel.id)
        .filter(Contract.is_deleted == False)
    )

    if date_from:
        query = query.filter(func.date(ServiceOrder.created_at) >= date_from)
    if date_to:
        query = query.filter(func.date(ServiceOrder.created_at) <= date_to)
    if service_type:
        query = query.filter(ServiceOrder.service_type == service_type)
    if status:
        query = query.filter(ServiceOrder.status == status)

    query = apply_data_scope(query, ServiceOrder, current_user)
    total = query.count()

    results = (
        query.order_by(ServiceOrder.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for order, customer_name, contract_no, assignee_name, _service_type_code in results:
        on_time = None
        if order.actual_end and order.planned_end:
            on_time = order.actual_end <= order.planned_end
        items.append(
            ServiceOrderCompletionRowOut(
                order_id=order.id,
                order_no=order.order_no,
                title=order.title,
                customer_name=customer_name,
                contract_no=contract_no,
                planned_start=order.planned_start,
                planned_end=order.planned_end,
                actual_start=order.actual_start,
                actual_end=order.actual_end,
                status=enum_value(order.status),
                on_time=on_time,
                assignee_name=assignee_name,
            )
        )

    return make_page_response(total, items, page, page_size)


@router.get("/customer-payment-analysis", response_model=ReportPageOut)
def customer_payment_analysis_report(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.REPORT_READ)),
    db: Session = Depends(get_db),
):
    contract_sub = (
        db.query(
            Contract.customer_id,
            func.count(Contract.id).label("contract_count"),
            func.coalesce(func.sum(Contract.total_amount), 0).label("total_contract_amount"),
        )
        .filter(Contract.is_deleted == False)
        .group_by(Contract.customer_id)
        .subquery()
    )

    invoice_sub = (
        db.query(Contract.customer_id, func.coalesce(func.sum(Invoice.amount), 0).label("total"))
        .join(Invoice, Invoice.contract_id == Contract.id)
        .filter(Contract.is_deleted == False)
        .group_by(Contract.customer_id)
        .subquery()
    )

    payment_sub = (
        db.query(Contract.customer_id, func.coalesce(func.sum(Payment.amount), 0).label("total"))
        .join(Payment, Payment.contract_id == Contract.id)
        .filter(Contract.is_deleted == False)
        .group_by(Contract.customer_id)
        .subquery()
    )

    query = (
        db.query(
            Customer,
            func.coalesce(contract_sub.c.contract_count, 0).label("contract_count"),
            func.coalesce(contract_sub.c.total_contract_amount, 0).label("total_contract_amount"),
            func.coalesce(invoice_sub.c.total, 0).label("total_invoiced"),
            func.coalesce(payment_sub.c.total, 0).label("total_received"),
        )
        .outerjoin(contract_sub, Customer.id == contract_sub.c.customer_id)
        .outerjoin(invoice_sub, Customer.id == invoice_sub.c.customer_id)
        .outerjoin(payment_sub, Customer.id == payment_sub.c.customer_id)
        .filter(Customer.is_deleted == False)
    )

    if date_from:
        query = query.filter(func.date(Customer.created_at) >= date_from)
    if date_to:
        query = query.filter(func.date(Customer.created_at) <= date_to)

    query = apply_data_scope(query, Customer, current_user)
    total = query.count()

    results = (
        query.order_by(Customer.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for customer, contract_count, total_contract, total_invoiced, total_received in results:
        total_contract_f = _to_float(total_contract)
        total_received_f = _to_float(total_received)
        collection_rate = (
            round((total_received_f / total_contract_f) * 100, 2) if total_contract_f > 0 else 0.0
        )
        items.append(
            CustomerPaymentAnalysisRowOut(
                customer_id=customer.id,
                customer_name=customer.name,
                contract_count=_to_int(contract_count),
                total_contract_amount=round(total_contract_f, 2),
                total_invoiced_amount=round(_to_float(total_invoiced), 2),
                total_received_amount=round(total_received_f, 2),
                collection_rate=collection_rate,
            )
        )

    return make_page_response(total, items, page, page_size)


@router.get("/invoice-detail", response_model=ReportPageOut)
def invoice_detail_report(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.REPORT_READ)),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            Invoice,
            Contract.contract_no.label("contract_no"),
            Customer.name.label("customer_name"),
            User.full_name.label("applied_by_name"),
        )
        .join(Contract, Invoice.contract_id == Contract.id)
        .outerjoin(Customer, Contract.customer_id == Customer.id)
        .outerjoin(User, Invoice.applied_by == User.id)
        .filter(Contract.is_deleted == False)
    )

    if date_from:
        query = query.filter(Invoice.invoice_date >= date_from)
    if date_to:
        query = query.filter(Invoice.invoice_date <= date_to)
    if status:
        query = query.filter(Invoice.status == status)

    query = apply_data_scope(query, Invoice, current_user)
    total = query.count()

    results = (
        query.order_by(Invoice.invoice_date.desc(), Invoice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for invoice, contract_no, customer_name, applied_by_name in results:
        items.append(
            InvoiceDetailRowOut(
                invoice_id=invoice.id,
                invoice_no=invoice.invoice_no,
                contract_no=contract_no,
                customer_name=customer_name,
                invoice_type=enum_value(invoice.invoice_type),
                amount=round(_to_float(invoice.amount), 2),
                status=enum_value(invoice.status),
                invoice_date=invoice.invoice_date,
                applied_by_name=applied_by_name,
            )
        )

    return make_page_response(total, items, page, page_size)


@router.get("/payment-detail", response_model=ReportPageOut)
def payment_detail_report(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    payment_method: str | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.REPORT_READ)),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            Payment,
            Contract.contract_no.label("contract_no"),
            Customer.name.label("customer_name"),
            User.full_name.label("created_by_name"),
        )
        .join(Contract, Payment.contract_id == Contract.id)
        .outerjoin(Customer, Contract.customer_id == Customer.id)
        .outerjoin(User, Payment.created_by == User.id)
        .filter(Contract.is_deleted == False)
    )

    if date_from:
        query = query.filter(Payment.payment_date >= date_from)
    if date_to:
        query = query.filter(Payment.payment_date <= date_to)
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)

    query = apply_data_scope(query, Payment, current_user)
    total = query.count()

    results = (
        query.order_by(Payment.payment_date.desc(), Payment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for payment, contract_no, customer_name, created_by_name in results:
        items.append(
            PaymentDetailRowOut(
                payment_id=payment.id,
                payment_no=payment.payment_no,
                contract_no=contract_no,
                customer_name=customer_name,
                payment_method=enum_value(payment.payment_method),
                amount=round(_to_float(payment.amount), 2),
                payment_date=payment.payment_date,
                created_by_name=created_by_name,
            )
        )

    return make_page_response(total, items, page, page_size)


@router.get("/customer-ledger-summary", response_model=ReportPageOut)
def customer_ledger_summary_report(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.REPORT_READ)),
    db: Session = Depends(get_db),
):
    contract_sub = (
        db.query(
            Contract.customer_id,
            func.count(Contract.id).label("contract_count"),
            func.coalesce(func.sum(Contract.total_amount), 0).label("total_contract_amount"),
        )
        .filter(Contract.is_deleted == False)
        .group_by(Contract.customer_id)
        .subquery()
    )

    invoice_sub = (
        db.query(Contract.customer_id, func.coalesce(func.sum(Invoice.amount), 0).label("total"))
        .join(Invoice, Invoice.contract_id == Contract.id)
        .filter(Contract.is_deleted == False)
        .group_by(Contract.customer_id)
        .subquery()
    )

    payment_sub = (
        db.query(Contract.customer_id, func.coalesce(func.sum(Payment.amount), 0).label("total"))
        .join(Payment, Payment.contract_id == Contract.id)
        .filter(Contract.is_deleted == False)
        .group_by(Contract.customer_id)
        .subquery()
    )

    query = (
        db.query(
            Customer,
            func.coalesce(contract_sub.c.contract_count, 0).label("contract_count"),
            func.coalesce(contract_sub.c.total_contract_amount, 0).label("total_contract_amount"),
            func.coalesce(invoice_sub.c.total, 0).label("total_invoiced"),
            func.coalesce(payment_sub.c.total, 0).label("total_received"),
        )
        .outerjoin(contract_sub, Customer.id == contract_sub.c.customer_id)
        .outerjoin(invoice_sub, Customer.id == invoice_sub.c.customer_id)
        .outerjoin(payment_sub, Customer.id == payment_sub.c.customer_id)
        .filter(Customer.is_deleted == False)
    )

    if date_from:
        query = query.filter(func.date(Customer.created_at) >= date_from)
    if date_to:
        query = query.filter(func.date(Customer.created_at) <= date_to)
    if status:
        query = query.filter(Customer.status == status)

    query = apply_data_scope(query, Customer, current_user)
    total = query.count()

    results = (
        query.order_by(Customer.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for customer, contract_count, total_contract, total_invoiced, total_received in results:
        items.append(
            CustomerLedgerSummaryRowOut(
                customer_id=customer.id,
                customer_name=customer.name,
                industry=customer.industry,
                contact_name=customer.contact_name,
                contact_phone=customer.contact_phone,
                contract_count=_to_int(contract_count),
                total_contract_amount=round(_to_float(total_contract), 2),
                total_invoiced_amount=round(_to_float(total_invoiced), 2),
                total_received_amount=round(_to_float(total_received), 2),
                status=enum_value(customer.status),
            )
        )

    return make_page_response(total, items, page, page_size)


@router.get("/{report_id}/export")
def export_report(
    report_id: str,
    date_from: date | None = None,
    date_to: date | None = None,
    service_type: int | None = None,
    status: str | None = None,
    payment_method: str | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.REPORT_READ)),
    db: Session = Depends(get_db),
):
    if report_id == "contract-execution":
        response = contract_execution_report(
            page=1,
            page_size=10000,
            date_from=date_from,
            date_to=date_to,
            service_type=service_type,
            status=status,
            current_user=current_user,
            db=db,
        )
        headers = [
            "合同编号",
            "合同标题",
            "客户名称",
            "签订日期",
            "签约额",
            "已开票",
            "已收款",
            "应收余额",
            "状态",
            "服务类型",
        ]
        rows = [
            [
                item.contract_no,
                item.contract_title,
                item.customer_name or "",
                item.sign_date.isoformat() if item.sign_date else "",
                item.total_amount,
                item.invoiced_amount,
                item.received_amount,
                item.receivable_balance,
                map_value(item.status, CONTRACT_STATUS_MAP),
                item.service_type or "",
            ]
            for item in response["items"]
        ]
        return export_excel_response("合同执行情况表.xlsx", headers, rows)

    if report_id == "service-order-completion":
        response = service_order_completion_report(
            page=1,
            page_size=10000,
            date_from=date_from,
            date_to=date_to,
            service_type=service_type,
            status=status,
            current_user=current_user,
            db=db,
        )
        headers = [
            "订单编号",
            "标题",
            "客户名称",
            "关联合同",
            "计划开始",
            "计划结束",
            "实际开始",
            "实际结束",
            "状态",
            "是否按期",
            "负责人",
        ]
        rows = [
            [
                item.order_no,
                item.title,
                item.customer_name or "",
                item.contract_no or "",
                item.planned_start.isoformat() if item.planned_start else "",
                item.planned_end.isoformat() if item.planned_end else "",
                item.actual_start.isoformat() if item.actual_start else "",
                item.actual_end.isoformat() if item.actual_end else "",
                map_value(item.status, SERVICE_ORDER_STATUS_MAP),
                "是" if item.on_time else ("否" if item.on_time is False else ""),
                item.assignee_name or "",
            ]
            for item in response["items"]
        ]
        return export_excel_response("服务订单完成情况表.xlsx", headers, rows)

    if report_id == "customer-payment-analysis":
        response = customer_payment_analysis_report(
            page=1,
            page_size=10000,
            date_from=date_from,
            date_to=date_to,
            current_user=current_user,
            db=db,
        )
        headers = [
            "客户名称",
            "合同数量",
            "合同总额",
            "开票总额",
            "收款总额",
            "回款率(%)",
        ]
        rows = [
            [
                item.customer_name,
                item.contract_count,
                item.total_contract_amount,
                item.total_invoiced_amount,
                item.total_received_amount,
                item.collection_rate,
            ]
            for item in response["items"]
        ]
        return export_excel_response("客户回款分析表.xlsx", headers, rows)

    if report_id == "invoice-detail":
        response = invoice_detail_report(
            page=1,
            page_size=10000,
            date_from=date_from,
            date_to=date_to,
            status=status,
            current_user=current_user,
            db=db,
        )
        headers = [
            "发票编号",
            "关联合同",
            "客户名称",
            "发票类型",
            "金额",
            "状态",
            "开票日期",
            "申请人",
        ]
        rows = [
            [
                item.invoice_no,
                item.contract_no or "",
                item.customer_name or "",
                map_value(item.invoice_type, INVOICE_TYPE_MAP),
                item.amount,
                map_value(item.status, INVOICE_STATUS_MAP),
                item.invoice_date.isoformat() if item.invoice_date else "",
                item.applied_by_name or "",
            ]
            for item in response["items"]
        ]
        return export_excel_response("发票开具明细表.xlsx", headers, rows)

    if report_id == "payment-detail":
        response = payment_detail_report(
            page=1,
            page_size=10000,
            date_from=date_from,
            date_to=date_to,
            payment_method=payment_method,
            current_user=current_user,
            db=db,
        )
        headers = [
            "收款编号",
            "关联合同",
            "客户名称",
            "付款方式",
            "金额",
            "收款日期",
            "录入人",
        ]
        rows = [
            [
                item.payment_no,
                item.contract_no or "",
                item.customer_name or "",
                map_value(item.payment_method, PAYMENT_METHOD_MAP),
                item.amount,
                item.payment_date.isoformat() if item.payment_date else "",
                item.created_by_name or "",
            ]
            for item in response["items"]
        ]
        return export_excel_response("收款明细表.xlsx", headers, rows)

    if report_id == "customer-ledger-summary":
        response = customer_ledger_summary_report(
            page=1,
            page_size=10000,
            date_from=date_from,
            date_to=date_to,
            status=status,
            current_user=current_user,
            db=db,
        )
        headers = [
            "客户名称",
            "行业",
            "联系人",
            "联系电话",
            "合同数量",
            "合同总额",
            "开票总额",
            "收款总额",
            "状态",
        ]
        rows = [
            [
                item.customer_name,
                item.industry or "",
                item.contact_name or "",
                item.contact_phone or "",
                item.contract_count,
                item.total_contract_amount,
                item.total_invoiced_amount,
                item.total_received_amount,
                map_value(item.status, CUSTOMER_STATUS_MAP),
            ]
            for item in response["items"]
        ]
        return export_excel_response("客户台账汇总表.xlsx", headers, rows)

    from fastapi import HTTPException

    raise HTTPException(status_code=404, detail="报表不存在")
