from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.db.session import get_db
from app.dependencies import get_current_user, require_permissions
from app.models.user import User
from app.models.customer import Customer
from app.models.contract import Contract
from app.models.service import ServiceOrder
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.core.constants import ContractStatus, ServiceOrderStatus, InvoiceStatus, PermissionCode
from app.utils.data_scope import apply_data_scope
from app.crud.payment import crud_payment

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@router.get("/stats")
def get_stats(
    current_user: User = Depends(require_permissions(PermissionCode.DASHBOARD_READ.value)),
    db: Session = Depends(get_db),
):
    today = date.today()
    current_year = today.year
    current_month = today.month

    # 合同状态分布
    contract_query = (
        db.query(Contract.status, func.count(Contract.id))
        .filter(Contract.is_deleted == False)
        .group_by(Contract.status)
    )
    contract_query = apply_data_scope(contract_query, Contract, current_user)
    contract_status_dist = contract_query.all()

    # 服务工单状态分布
    service_query = (
        db.query(ServiceOrder.status, func.count(ServiceOrder.id))
        .group_by(ServiceOrder.status)
    )
    service_query = apply_data_scope(service_query, ServiceOrder, current_user)
    service_status_dist = service_query.all()

    # 本月开票金额
    invoice_query = (
        db.query(func.coalesce(func.sum(Invoice.amount), 0))
        .filter(
            func.extract("year", Invoice.created_at) == current_year,
            func.extract("month", Invoice.created_at) == current_month,
        )
    )
    invoice_query = apply_data_scope(invoice_query, Invoice, current_user)
    monthly_invoice_amount = invoice_query.scalar()

    # 本月收款金额
    payment_query = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(
            func.extract("year", Payment.payment_date) == current_year,
            func.extract("month", Payment.payment_date) == current_month,
        )
    )
    payment_query = apply_data_scope(payment_query, Payment, current_user)
    monthly_payment_amount = payment_query.scalar()

    # 总应收余额
    total_contract_query = db.query(func.coalesce(func.sum(Contract.total_amount), 0)).filter(
        Contract.is_deleted == False, Contract.status == ContractStatus.ACTIVE
    )
    total_contract_query = apply_data_scope(total_contract_query, Contract, current_user)
    total_contract_amount = total_contract_query.scalar()

    total_received_query = db.query(func.coalesce(func.sum(Payment.amount), 0))
    total_received_query = apply_data_scope(total_received_query, Payment, current_user)
    total_received = total_received_query.scalar()

    # 月度开票趋势（带 data_scope 过滤）
    monthly_invoice_query = (
        db.query(
            extract("month", Invoice.created_at).label("month"),
            func.sum(Invoice.amount).label("total"),
        )
        .filter(extract("year", Invoice.created_at) == current_year)
        .group_by(extract("month", Invoice.created_at))
        .order_by(extract("month", Invoice.created_at))
    )
    monthly_invoice_query = apply_data_scope(monthly_invoice_query, Invoice, current_user)
    monthly_invoice_results = monthly_invoice_query.all()
    monthly_invoices = [{"month": int(r.month), "total": float(r.total or 0)} for r in monthly_invoice_results]

    # 月度收款趋势（带 data_scope 过滤）
    monthly_payment_query = (
        db.query(
            extract("month", Payment.payment_date).label("month"),
            func.sum(Payment.amount).label("total"),
        )
        .filter(extract("year", Payment.payment_date) == current_year)
        .group_by(extract("month", Payment.payment_date))
        .order_by(extract("month", Payment.payment_date))
    )
    monthly_payment_query = apply_data_scope(monthly_payment_query, Payment, current_user)
    monthly_payment_results = monthly_payment_query.all()
    monthly_payments = [{"month": int(r.month), "total": float(r.total or 0)} for r in monthly_payment_results]

    # 逾期合同数及列表
    overdue_query = (
        db.query(Contract)
        .filter(
            Contract.is_deleted == False,
            Contract.status == ContractStatus.ACTIVE,
            Contract.end_date < today,
        )
    )
    overdue_query = apply_data_scope(overdue_query, Contract, current_user)
    overdue_contracts_db = overdue_query.all()

    contract_ids = [c.id for c in overdue_contracts_db]
    payment_sums = crud_payment.get_sums_by_contract_ids(db, contract_ids=contract_ids) if contract_ids else {}

    overdue_contracts = []
    for c in overdue_contracts_db:
        received = payment_sums.get(c.id, 0)
        receivable = float(c.total_amount) - float(received)
        if receivable > 0:
            overdue_contracts.append({
                "id": c.id,
                "contract_id": c.id,
                "contract_no": c.contract_no,
                "customer_name": c.customer.name if c.customer else None,
                "end_date": c.end_date.isoformat() if c.end_date else None,
                "total_amount": float(c.total_amount),
                "received_amount": float(received),
                "receivable_amount": receivable,
                "is_overdue": True,
            })

    overdue_count = len(overdue_contracts)

    # 1. 客户增长趋势（按月统计本年新增客户数）
    customer_growth_query = (
        db.query(
            extract("month", Customer.created_at).label("month"),
            func.count(Customer.id).label("count"),
        )
        .filter(extract("year", Customer.created_at) == current_year)
        .group_by(extract("month", Customer.created_at))
        .order_by(extract("month", Customer.created_at))
    )
    customer_growth_query = apply_data_scope(customer_growth_query, Customer, current_user)
    customer_growth_results = customer_growth_query.all()
    customer_growth_trend = [
        {"month": int(r.month), "count": int(r.count)} for r in customer_growth_results
    ]

    # 2. 合同金额按服务类型分布
    contract_amount_by_service_query = (
        db.query(
            Contract.service_type.label("service_type"),
            func.coalesce(func.sum(Contract.total_amount), 0).label("total_amount"),
        )
        .filter(Contract.is_deleted == False)
        .group_by(Contract.service_type)
    )
    contract_amount_by_service_query = apply_data_scope(contract_amount_by_service_query, Contract, current_user)
    contract_amount_by_service_results = contract_amount_by_service_query.all()
    contract_amount_by_service_type = [
        {"service_type": str(r.service_type), "total_amount": float(r.total_amount or 0)}
        for r in contract_amount_by_service_results
    ]

    # 3. 员工业绩排行 TOP5（按 Contract.created_by 分组）
    top_performers_query = (
        db.query(
            User.id.label("user_id"),
            User.full_name.label("full_name"),
            func.coalesce(func.sum(Contract.total_amount), 0).label("total_amount"),
        )
        .join(Contract, Contract.created_by == User.id)
        .filter(Contract.is_deleted == False)
        .group_by(User.id, User.full_name)
        .order_by(func.sum(Contract.total_amount).desc())
        .limit(5)
    )
    top_performers_results = top_performers_query.all()
    top_performers = [
        {
            "user_id": int(r.user_id),
            "full_name": str(r.full_name) if r.full_name else None,
            "total_amount": float(r.total_amount or 0),
        }
        for r in top_performers_results
    ]

    # 4. 本月新增服务工单数
    monthly_new_service_orders_query = (
        db.query(func.count(ServiceOrder.id))
        .filter(
            func.extract("year", ServiceOrder.created_at) == current_year,
            func.extract("month", ServiceOrder.created_at) == current_month,
        )
    )
    monthly_new_service_orders_query = apply_data_scope(monthly_new_service_orders_query, ServiceOrder, current_user)
    monthly_new_service_orders = monthly_new_service_orders_query.scalar() or 0

    return {
        "contract_status_distribution": [
            {"status": str(s), "count": c} for s, c in contract_status_dist
        ],
        "service_status_distribution": [
            {"status": str(s), "count": c} for s, c in service_status_dist
        ],
        "monthly_invoice_amount": float(monthly_invoice_amount),
        "monthly_payment_amount": float(monthly_payment_amount),
        "total_receivable": float(total_contract_amount) - float(total_received),
        "overdue_contract_count": overdue_count,
        "monthly_invoice_trend": monthly_invoices,
        "monthly_payment_trend": monthly_payments,
        "overdue_contracts": overdue_contracts,
        "customer_growth_trend": customer_growth_trend,
        "contract_amount_by_service_type": contract_amount_by_service_type,
        "top_performers": top_performers,
        "monthly_new_service_orders": int(monthly_new_service_orders),
    }
