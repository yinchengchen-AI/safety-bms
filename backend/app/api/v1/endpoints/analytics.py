from collections import defaultdict
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, extract, func
from sqlalchemy.orm import Session, joinedload

from app.core.constants import (
    ContractStatus,
    InvoiceStatus,
    PermissionCode,
    ServiceOrderStatus,
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
from app.schemas.analytics import (
    AnalyticsDrilldownItemOut,
    AnalyticsDrilldownOut,
    AnalyticsOverviewOut,
    CustomerGrowthItemOut,
    CustomerIndustryDistributionItemOut,
    CustomerInsightsOut,
    CustomerRegionDistributionItemOut,
    CustomerStatusDistributionItemOut,
    PerformanceRankingItemOut,
    PerformanceRankingOut,
    ReceivableAgingBucketOut,
    ReceivableAgingOut,
    RevenueTrendItemOut,
    RevenueTrendOut,
    RiskContractOut,
    ServiceEfficiencyOut,
    ServiceEfficiencyTrendItemOut,
    ServiceTypeDistributionItemOut,
)
from app.utils.data_scope import apply_data_scope
from app.utils.enum_format import enum_value
from app.utils.excel_export import export_excel_response
from app.utils.export_mappings import (
    ANALYTICS_CATEGORY_MAP,
    CONTRACT_STATUS_MAP,
    CUSTOMER_STATUS_MAP,
    INVOICE_STATUS_MAP,
    SERVICE_ORDER_STATUS_MAP,
    map_value,
)

router = APIRouter(prefix="/analytics", tags=["统计分析"])


def _to_float(value: Decimal | float | int | str | None) -> float:
    return float(value) if value is not None else 0.0


def _to_int(value: Decimal | float | int | None) -> int:
    return int(value) if value is not None else 0


def _contract_total_amount(contract: Contract) -> float:
    return float(getattr(contract, "total_amount", 0) or 0)


def _invoice_metric_date_expr():
    return func.coalesce(Invoice.invoice_date, func.date(Invoice.created_at))


def _period_key(year: Decimal | float | int | None, month: Decimal | float | int | None) -> str:
    return f"{_to_int(year):04d}-{_to_int(month):02d}"


def _apply_contract_filters(
    query,
    current_user: User,
    date_from: date | None,
    date_to: date | None,
    service_type: int | None,
):
    query = query.filter(
        Contract.is_deleted == False,
        Contract.sign_date.isnot(None),
        Contract.status.in_(
            [ContractStatus.ACTIVE, ContractStatus.SIGNED, ContractStatus.COMPLETED]
        ),
    )
    if date_from:
        query = query.filter(Contract.sign_date >= date_from)
    if date_to:
        query = query.filter(Contract.sign_date <= date_to)
    if service_type:
        query = query.filter(Contract.service_type == service_type)
    return apply_data_scope(query, Contract, current_user)


def _apply_invoice_filters(
    query,
    current_user: User,
    date_from: date | None,
    date_to: date | None,
    service_type: int | None,
):
    invoice_metric_date = _invoice_metric_date_expr()
    query = query.filter(Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.SENT]))
    if service_type:
        query = query.join(Contract, Invoice.contract_id == Contract.id).filter(
            Contract.service_type == service_type
        )
    if date_from:
        query = query.filter(invoice_metric_date >= date_from)
    if date_to:
        query = query.filter(invoice_metric_date <= date_to)
    return apply_data_scope(query, Invoice, current_user)


def _apply_payment_filters(
    query,
    current_user: User,
    date_from: date | None,
    date_to: date | None,
    service_type: int | None,
):
    if service_type:
        query = query.join(Contract, Payment.contract_id == Contract.id).filter(
            Contract.service_type == service_type
        )
    if date_from:
        query = query.filter(Payment.payment_date >= date_from)
    if date_to:
        query = query.filter(Payment.payment_date <= date_to)
    return apply_data_scope(query, Payment, current_user)


def _contract_ids_for_filters(
    db: Session,
    current_user: User,
    date_from: date | None,
    date_to: date | None,
    service_type: int | None,
) -> list[int]:
    query = db.query(Contract.id)
    query = _apply_contract_filters(query, current_user, date_from, date_to, service_type)
    return [item[0] for item in query.all()]


def _month_range(period: str) -> tuple[date, date]:
    year_str, month_str = period.split("-")
    year = int(year_str)
    month = int(month_str)
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1).fromordinal(date(year + 1, 1, 1).toordinal() - 1)
    else:
        end = date(year, month + 1, 1).fromordinal(date(year, month + 1, 1).toordinal() - 1)
    return start, end


def _build_drilldown_rows(
    db: Session,
    current_user: User,
    source: str,
    period: str | None,
    series_type: str | None,
    group_value: str | None,
    date_from: date | None,
    date_to: date | None,
    service_type: int | None,
) -> list[AnalyticsDrilldownItemOut]:
    if period:
        date_from, date_to = _month_range(period)

    if source == "revenue":
        if series_type == "签约额":
            query = db.query(Contract)
            query = _apply_contract_filters(query, current_user, date_from, date_to, service_type)
            items = (
                query.options(joinedload(Contract.customer))
                .order_by(Contract.sign_date.desc(), Contract.created_at.desc())
                .all()
            )
            return [
                AnalyticsDrilldownItemOut(
                    id=item.id,
                    category="contract",
                    primary_label=item.contract_no,
                    secondary_label=item.customer.name if item.customer else item.title,
                    amount=round(_contract_total_amount(item), 2),
                    date_label=item.sign_date.isoformat() if item.sign_date else None,
                    status=enum_value(item.status),
                    extra=item.title,
                )
                for item in items
            ]

        if series_type == "开票额":
            query = db.query(Invoice)
            query = _apply_invoice_filters(query, current_user, date_from, date_to, service_type)
            items = (
                query.options(joinedload(Invoice.contract).joinedload(Contract.customer))
                .order_by(Invoice.created_at.desc())
                .all()
            )
            return [
                AnalyticsDrilldownItemOut(
                    id=item.id,
                    category="invoice",
                    primary_label=item.invoice_no,
                    secondary_label=(
                        item.contract.customer.name
                        if item.contract and item.contract.customer
                        else item.contract.contract_no if item.contract else None
                    ),
                    amount=round(_to_float(item.amount), 2),
                    date_label=(
                        item.invoice_date.isoformat()
                        if item.invoice_date
                        else item.created_at.date().isoformat() if item.created_at else None
                    ),
                    status=enum_value(item.status),
                    extra=item.contract.contract_no if item.contract else None,
                )
                for item in items
            ]

        query = db.query(Payment)
        query = _apply_payment_filters(query, current_user, date_from, date_to, service_type)
        items = (
            query.options(joinedload(Payment.contract).joinedload(Contract.customer))
            .order_by(Payment.payment_date.desc(), Payment.created_at.desc())
            .all()
        )
        return [
            AnalyticsDrilldownItemOut(
                id=item.id,
                category="payment",
                primary_label=item.payment_no,
                secondary_label=(
                    item.contract.customer.name
                    if item.contract and item.contract.customer
                    else item.contract.contract_no if item.contract else None
                ),
                amount=round(_to_float(item.amount), 2),
                date_label=item.payment_date.isoformat() if item.payment_date else None,
                status="received",
                extra=item.contract.contract_no if item.contract else None,
            )
            for item in items
        ]

    if source == "performance" and group_value:
        signed_query = db.query(Contract)
        signed_query = _apply_contract_filters(
            signed_query, current_user, date_from, date_to, service_type
        )
        signed_items = (
            signed_query.filter(Contract.created_by == int(group_value))
            .options(joinedload(Contract.customer))
            .order_by(Contract.sign_date.desc(), Contract.created_at.desc())
            .all()
        )
        return [
            AnalyticsDrilldownItemOut(
                id=item.id,
                category="contract",
                primary_label=item.contract_no,
                secondary_label=item.customer.name if item.customer else item.title,
                amount=round(_contract_total_amount(item), 2),
                date_label=item.sign_date.isoformat() if item.sign_date else None,
                status=enum_value(item.status),
                extra=item.title,
            )
            for item in signed_items
        ]

    if source == "aging":
        all_items = _build_drilldown_rows(
            db,
            current_user,
            source="aging-risk",
            period=None,
            series_type=None,
            group_value=None,
            date_from=date_from,
            date_to=date_to,
            service_type=service_type,
        )
        if not group_value:
            return all_items
        if group_value == "90+":
            return [item for item in all_items if item.extra == "90+"]
        start_day, end_day = map(int, group_value.split("-"))
        return [
            item
            for item in all_items
            if item.status is not None and start_day <= int(item.status) <= end_day
        ]

    if source == "aging-risk":
        contract_query = db.query(Contract)
        contract_query = _apply_contract_filters(
            contract_query, current_user, date_from, date_to, service_type
        )
        contracts = contract_query.options(joinedload(Contract.customer)).all()
        contract_ids = [contract.id for contract in contracts]
        payment_map: dict[int, float] = {}
        if contract_ids:
            payment_results = (
                db.query(
                    Payment.contract_id,
                    func.coalesce(func.sum(Payment.amount), 0).label("total"),
                )
                .filter(Payment.contract_id.in_(contract_ids))
                .group_by(Payment.contract_id)
                .all()
            )
            payment_map = {item.contract_id: _to_float(item.total) for item in payment_results}
        today = date.today()
        result: list[AnalyticsDrilldownItemOut] = []
        for contract in contracts:
            end_date = getattr(contract, "end_date", None)
            if end_date is None or end_date >= today:
                continue
            receivable_amount = round(
                _contract_total_amount(contract) - payment_map.get(contract.id, 0.0), 2
            )
            if receivable_amount <= 0:
                continue
            overdue_days = (today - end_date).days
            bucket = "90+"
            if overdue_days <= 30:
                bucket = "0-30"
            elif overdue_days <= 60:
                bucket = "31-60"
            elif overdue_days <= 90:
                bucket = "61-90"
            result.append(
                AnalyticsDrilldownItemOut(
                    id=contract.id,
                    category="contract",
                    primary_label=contract.contract_no,
                    secondary_label=contract.customer.name if contract.customer else contract.title,
                    amount=receivable_amount,
                    date_label=end_date.isoformat(),
                    status=str(overdue_days),
                    extra=bucket,
                )
            )
        return sorted(result, key=lambda item: int(item.status or "0"), reverse=True)

    if source == "customer-industry" and group_value:
        query = db.query(Customer).filter(Customer.is_deleted == False)
        if date_from:
            query = query.filter(func.date(Customer.created_at) >= date_from)
        if date_to:
            query = query.filter(func.date(Customer.created_at) <= date_to)
        query = apply_data_scope(query, Customer, current_user)
        industry = None if group_value == "未填写" else group_value
        if industry is None:
            query = query.filter(Customer.industry.is_(None))
        else:
            query = query.filter(Customer.industry == industry)
        items = query.order_by(Customer.created_at.desc()).all()
        return [
            AnalyticsDrilldownItemOut(
                id=item.id,
                category="customer",
                primary_label=item.name,
                secondary_label=item.contact_name,
                amount=None,
                date_label=item.created_at.date().isoformat() if item.created_at else None,
                status=enum_value(item.status),
                extra=item.industry,
            )
            for item in items
        ]

    if source == "customer-status" and group_value:
        query = db.query(Customer).filter(
            Customer.is_deleted == False, Customer.status == group_value
        )
        if date_from:
            query = query.filter(func.date(Customer.created_at) >= date_from)
        if date_to:
            query = query.filter(func.date(Customer.created_at) <= date_to)
        query = apply_data_scope(query, Customer, current_user)
        items = query.order_by(Customer.created_at.desc()).all()
        return [
            AnalyticsDrilldownItemOut(
                id=item.id,
                category="customer",
                primary_label=item.name,
                secondary_label=item.contact_name,
                amount=None,
                date_label=item.created_at.date().isoformat() if item.created_at else None,
                status=enum_value(item.status),
                extra=item.industry,
            )
            for item in items
        ]

    if source == "customer-region" and group_value:
        query = db.query(Customer).filter(Customer.is_deleted == False)
        if date_from:
            query = query.filter(func.date(Customer.created_at) >= date_from)
        if date_to:
            query = query.filter(func.date(Customer.created_at) <= date_to)
        query = apply_data_scope(query, Customer, current_user)
        if group_value == "未填写":
            query = query.filter(Customer.city.is_(None))
        else:
            query = query.filter(
                func.coalesce(Customer.city, "") + func.coalesce(Customer.district, "")
                == group_value
            )
        items = query.order_by(Customer.created_at.desc()).all()
        return [
            AnalyticsDrilldownItemOut(
                id=item.id,
                category="customer",
                primary_label=item.name,
                secondary_label=item.contact_name,
                amount=None,
                date_label=item.created_at.date().isoformat() if item.created_at else None,
                status=enum_value(item.status),
                extra="".join(
                    [p for p in [item.province, item.city, item.district, item.street] if p]
                ),
            )
            for item in items
        ]

    if source == "service-type" and group_value:
        query = db.query(ServiceOrder)
        if date_from:
            query = query.filter(func.date(ServiceOrder.created_at) >= date_from)
        if date_to:
            query = query.filter(func.date(ServiceOrder.created_at) <= date_to)
        query = query.filter(ServiceOrder.service_type == group_value)
        query = apply_data_scope(query, ServiceOrder, current_user)
        items = (
            query.options(
                joinedload(ServiceOrder.contract).joinedload(Contract.customer),
                joinedload(ServiceOrder.assignee),
            )
            .order_by(ServiceOrder.created_at.desc())
            .all()
        )
        return [
            AnalyticsDrilldownItemOut(
                id=item.id,
                category="service",
                primary_label=item.order_no,
                secondary_label=(
                    item.contract.customer.name
                    if item.contract and item.contract.customer
                    else item.title
                ),
                amount=None,
                date_label=item.created_at.date().isoformat() if item.created_at else None,
                status=enum_value(item.status),
                extra=item.assignee.full_name if item.assignee else item.title,
            )
            for item in items
        ]

    return []


@router.get("/overview", response_model=AnalyticsOverviewOut)
def get_analytics_overview(
    date_from: date | None = None,
    date_to: date | None = None,
    service_type: int | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.ANALYTICS_READ.value)),
    db: Session = Depends(get_db),
):
    signed_query = db.query(func.coalesce(func.sum(Contract.total_amount), 0))
    signed_query = _apply_contract_filters(
        signed_query, current_user, date_from, date_to, service_type
    )
    signed_amount = _to_float(signed_query.scalar())

    invoice_query = db.query(func.coalesce(func.sum(Invoice.amount), 0))
    invoice_query = _apply_invoice_filters(
        invoice_query, current_user, date_from, date_to, service_type
    )
    invoiced_amount = _to_float(invoice_query.scalar())

    payment_query = db.query(func.coalesce(func.sum(Payment.amount), 0))
    payment_query = _apply_payment_filters(
        payment_query, current_user, date_from, date_to, service_type
    )
    received_amount = _to_float(payment_query.scalar())

    contract_ids = _contract_ids_for_filters(db, current_user, date_from, date_to, service_type)
    received_by_contract = {}
    if contract_ids:
        results = (
            db.query(
                Payment.contract_id,
                func.coalesce(func.sum(Payment.amount), 0).label("total"),
            )
            .filter(Payment.contract_id.in_(contract_ids))
            .group_by(Payment.contract_id)
            .all()
        )
        received_by_contract = {item.contract_id: _to_float(item.total) for item in results}

    overdue_contract_count = 0
    receivable_balance = 0.0
    if contract_ids:
        contracts = db.query(Contract).filter(Contract.id.in_(contract_ids)).all()
        today = date.today()
        for contract in contracts:
            receivable_amount = _contract_total_amount(contract) - received_by_contract.get(
                contract.id, 0.0
            )
            if receivable_amount <= 0:
                continue
            receivable_balance += receivable_amount
            end_date = getattr(contract, "end_date", None)
            if end_date is not None and end_date < today:
                overdue_contract_count += 1

    collection_rate = (
        round((received_amount / signed_amount) * 100, 2) if signed_amount > 0 else 0.0
    )

    return AnalyticsOverviewOut(
        signed_amount=round(signed_amount, 2),
        invoiced_amount=round(invoiced_amount, 2),
        received_amount=round(received_amount, 2),
        collection_rate=collection_rate,
        receivable_balance=round(receivable_balance, 2),
        overdue_contract_count=overdue_contract_count,
    )


@router.get("/revenue-trend", response_model=RevenueTrendOut)
def get_revenue_trend(
    date_from: date | None = None,
    date_to: date | None = None,
    service_type: int | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.ANALYTICS_READ.value)),
    db: Session = Depends(get_db),
):
    invoice_metric_date = _invoice_metric_date_expr()
    trend_map: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "signed_amount": 0.0,
            "invoiced_amount": 0.0,
            "received_amount": 0.0,
        }
    )

    signed_query = db.query(
        extract("year", Contract.sign_date).label("year"),
        extract("month", Contract.sign_date).label("month"),
        func.coalesce(func.sum(Contract.total_amount), 0).label("total"),
    )
    signed_query = _apply_contract_filters(
        signed_query, current_user, date_from, date_to, service_type
    )
    signed_results = (
        signed_query.group_by(
            extract("year", Contract.sign_date),
            extract("month", Contract.sign_date),
        )
        .order_by(
            extract("year", Contract.sign_date),
            extract("month", Contract.sign_date),
        )
        .all()
    )
    for item in signed_results:
        key = _period_key(item.year, item.month)
        trend_map[key]["signed_amount"] = _to_float(item.total)

    invoice_query = db.query(
        extract("year", invoice_metric_date).label("year"),
        extract("month", invoice_metric_date).label("month"),
        func.coalesce(func.sum(Invoice.amount), 0).label("total"),
    )
    invoice_query = _apply_invoice_filters(
        invoice_query, current_user, date_from, date_to, service_type
    )
    invoice_results = (
        invoice_query.group_by(
            extract("year", invoice_metric_date),
            extract("month", invoice_metric_date),
        )
        .order_by(
            extract("year", invoice_metric_date),
            extract("month", invoice_metric_date),
        )
        .all()
    )
    for item in invoice_results:
        key = _period_key(item.year, item.month)
        trend_map[key]["invoiced_amount"] = _to_float(item.total)

    payment_query = db.query(
        extract("year", Payment.payment_date).label("year"),
        extract("month", Payment.payment_date).label("month"),
        func.coalesce(func.sum(Payment.amount), 0).label("total"),
    )
    payment_query = _apply_payment_filters(
        payment_query, current_user, date_from, date_to, service_type
    )
    payment_results = (
        payment_query.group_by(
            extract("year", Payment.payment_date),
            extract("month", Payment.payment_date),
        )
        .order_by(
            extract("year", Payment.payment_date),
            extract("month", Payment.payment_date),
        )
        .all()
    )
    for item in payment_results:
        key = _period_key(item.year, item.month)
        trend_map[key]["received_amount"] = _to_float(item.total)

    items = [
        RevenueTrendItemOut(
            period=period,
            signed_amount=round(values["signed_amount"], 2),
            invoiced_amount=round(values["invoiced_amount"], 2),
            received_amount=round(values["received_amount"], 2),
            receivable_balance=round(values["signed_amount"] - values["received_amount"], 2),
        )
        for period, values in sorted(trend_map.items())
    ]
    return RevenueTrendOut(items=items)


@router.get("/performance-ranking", response_model=PerformanceRankingOut)
def get_performance_ranking(
    date_from: date | None = None,
    date_to: date | None = None,
    service_type: int | None = None,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_permissions(PermissionCode.ANALYTICS_READ.value)),
    db: Session = Depends(get_db),
):
    ranking_map: dict[int, PerformanceRankingItemOut] = {}

    signed_query = db.query(
        User.id.label("user_id"),
        User.full_name.label("full_name"),
        func.coalesce(func.sum(Contract.total_amount), 0).label("total"),
    ).join(User, Contract.created_by == User.id)
    signed_query = _apply_contract_filters(
        signed_query, current_user, date_from, date_to, service_type
    )
    signed_results = signed_query.group_by(User.id, User.full_name).all()
    for item in signed_results:
        if item.user_id is None:
            continue
        ranking_map[int(item.user_id)] = PerformanceRankingItemOut(
            user_id=int(item.user_id),
            full_name=item.full_name or "未命名用户",
            signed_amount=round(_to_float(item.total), 2),
            invoiced_amount=0.0,
            received_amount=0.0,
        )

    invoice_query = (
        db.query(
            User.id.label("user_id"),
            User.full_name.label("full_name"),
            func.coalesce(func.sum(Invoice.amount), 0).label("total"),
        )
        .select_from(Invoice)
        .join(User, Invoice.applied_by == User.id)
    )
    invoice_query = _apply_invoice_filters(
        invoice_query, current_user, date_from, date_to, service_type
    )
    invoice_results = invoice_query.group_by(User.id, User.full_name).all()
    for item in invoice_results:
        if item.user_id is None:
            continue
        user_id = int(item.user_id)
        if user_id not in ranking_map:
            ranking_map[user_id] = PerformanceRankingItemOut(
                user_id=user_id,
                full_name=item.full_name or "未命名用户",
                signed_amount=0.0,
                invoiced_amount=0.0,
                received_amount=0.0,
            )
        ranking_map[user_id].invoiced_amount = round(_to_float(item.total), 2)

    payment_query = (
        db.query(
            User.id.label("user_id"),
            User.full_name.label("full_name"),
            func.coalesce(func.sum(Payment.amount), 0).label("total"),
        )
        .select_from(Payment)
        .join(User, Payment.created_by == User.id)
    )
    payment_query = _apply_payment_filters(
        payment_query, current_user, date_from, date_to, service_type
    )
    payment_results = payment_query.group_by(User.id, User.full_name).all()
    for item in payment_results:
        if item.user_id is None:
            continue
        user_id = int(item.user_id)
        if user_id not in ranking_map:
            ranking_map[user_id] = PerformanceRankingItemOut(
                user_id=user_id,
                full_name=item.full_name or "未命名用户",
                signed_amount=0.0,
                invoiced_amount=0.0,
                received_amount=0.0,
            )
        ranking_map[user_id].received_amount = round(_to_float(item.total), 2)

    items = sorted(
        ranking_map.values(),
        key=lambda item: (
            item.signed_amount,
            item.invoiced_amount,
            item.received_amount,
        ),
        reverse=True,
    )[:limit]
    return PerformanceRankingOut(items=items)


@router.get("/receivable-aging", response_model=ReceivableAgingOut)
def get_receivable_aging(
    date_from: date | None = None,
    date_to: date | None = None,
    service_type: int | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.ANALYTICS_READ.value)),
    db: Session = Depends(get_db),
):
    contract_query = db.query(Contract)
    contract_query = _apply_contract_filters(
        contract_query, current_user, date_from, date_to, service_type
    )
    contracts = contract_query.all()
    contract_ids = [contract.id for contract in contracts]

    payment_map: dict[int, float] = {}
    if contract_ids:
        payment_results = (
            db.query(
                Payment.contract_id,
                func.coalesce(func.sum(Payment.amount), 0).label("total"),
            )
            .filter(Payment.contract_id.in_(contract_ids))
            .group_by(Payment.contract_id)
            .all()
        )
        payment_map = {item.contract_id: _to_float(item.total) for item in payment_results}

    bucket_map = {
        "0-30": {"contract_count": 0, "amount": 0.0},
        "31-60": {"contract_count": 0, "amount": 0.0},
        "61-90": {"contract_count": 0, "amount": 0.0},
        "90+": {"contract_count": 0, "amount": 0.0},
    }
    risk_contracts: list[RiskContractOut] = []
    today = date.today()

    for contract in contracts:
        if not contract.end_date or contract.end_date >= today:
            continue
        receivable_amount = round(
            _to_float(contract.total_amount) - payment_map.get(contract.id, 0.0), 2
        )
        if receivable_amount <= 0:
            continue
        overdue_days = (today - contract.end_date).days
        if overdue_days <= 30:
            bucket = "0-30"
        elif overdue_days <= 60:
            bucket = "31-60"
        elif overdue_days <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"
        bucket_map[bucket]["contract_count"] += 1
        bucket_map[bucket]["amount"] += receivable_amount
        risk_contracts.append(
            RiskContractOut(
                contract_id=contract.id,
                contract_no=contract.contract_no,
                customer_name=contract.customer.name if contract.customer else None,
                end_date=contract.end_date,
                receivable_amount=receivable_amount,
                overdue_days=overdue_days,
            )
        )

    buckets = [
        ReceivableAgingBucketOut(
            range=key,
            contract_count=value["contract_count"],
            amount=round(value["amount"], 2),
        )
        for key, value in bucket_map.items()
    ]
    risk_contracts.sort(key=lambda item: item.overdue_days, reverse=True)
    return ReceivableAgingOut(buckets=buckets, risk_contracts=risk_contracts)


@router.get("/customer-insights", response_model=CustomerInsightsOut)
def get_customer_insights(
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.ANALYTICS_READ.value)),
    db: Session = Depends(get_db),
):
    growth_query = db.query(
        extract("year", Customer.created_at).label("year"),
        extract("month", Customer.created_at).label("month"),
        func.count(Customer.id).label("count"),
    ).filter(Customer.is_deleted == False)
    if date_from:
        growth_query = growth_query.filter(func.date(Customer.created_at) >= date_from)
    if date_to:
        growth_query = growth_query.filter(func.date(Customer.created_at) <= date_to)
    growth_query = apply_data_scope(growth_query, Customer, current_user)
    growth_results = (
        growth_query.group_by(
            extract("year", Customer.created_at),
            extract("month", Customer.created_at),
        )
        .order_by(
            extract("year", Customer.created_at),
            extract("month", Customer.created_at),
        )
        .all()
    )

    industry_query = db.query(
        func.coalesce(Customer.industry, "未填写").label("industry"),
        func.count(Customer.id).label("count"),
    ).filter(Customer.is_deleted == False)
    if date_from:
        industry_query = industry_query.filter(func.date(Customer.created_at) >= date_from)
    if date_to:
        industry_query = industry_query.filter(func.date(Customer.created_at) <= date_to)
    industry_query = apply_data_scope(industry_query, Customer, current_user)
    industry_results = industry_query.group_by(func.coalesce(Customer.industry, "未填写")).all()

    status_query = db.query(
        Customer.status.label("status"),
        func.count(Customer.id).label("count"),
    ).filter(Customer.is_deleted == False)
    if date_from:
        status_query = status_query.filter(func.date(Customer.created_at) >= date_from)
    if date_to:
        status_query = status_query.filter(func.date(Customer.created_at) <= date_to)
    status_query = apply_data_scope(status_query, Customer, current_user)
    status_results = status_query.group_by(Customer.status).all()

    region_expr = func.coalesce(
        func.nullif(
            func.trim(func.coalesce(Customer.city, "") + func.coalesce(Customer.district, "")),
            "",
        ),
        "未填写",
    )
    region_query = db.query(
        region_expr.label("region"),
        func.count(Customer.id).label("count"),
    ).filter(Customer.is_deleted == False)
    if date_from:
        region_query = region_query.filter(func.date(Customer.created_at) >= date_from)
    if date_to:
        region_query = region_query.filter(func.date(Customer.created_at) <= date_to)
    region_query = apply_data_scope(region_query, Customer, current_user)
    region_results = region_query.group_by(region_expr).all()

    return CustomerInsightsOut(
        growth_trend=[
            CustomerGrowthItemOut(
                period=_period_key(item.year, item.month), new_customers=int(item.count)
            )
            for item in growth_results
        ],
        industry_distribution=[
            CustomerIndustryDistributionItemOut(industry=str(item.industry), count=int(item.count))
            for item in industry_results
        ],
        status_distribution=[
            CustomerStatusDistributionItemOut(status=enum_value(item.status), count=int(item.count))
            for item in status_results
        ],
        region_distribution=[
            CustomerRegionDistributionItemOut(region=str(item.region), count=int(item.count))
            for item in region_results
        ],
    )


@router.get("/service-efficiency", response_model=ServiceEfficiencyOut)
def get_service_efficiency(
    date_from: date | None = None,
    date_to: date | None = None,
    service_type: int | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.ANALYTICS_READ.value)),
    db: Session = Depends(get_db),
):
    today = date.today()
    trend_query = db.query(
        extract("year", ServiceOrder.created_at).label("year"),
        extract("month", ServiceOrder.created_at).label("month"),
        func.count(ServiceOrder.id).label("new_orders"),
        func.sum(
            case(
                (
                    ServiceOrder.status.in_(
                        [ServiceOrderStatus.COMPLETED, ServiceOrderStatus.ACCEPTED]
                    ),
                    1,
                ),
                else_=0,
            )
        ).label("completed_orders"),
        func.sum(
            case(
                (
                    and_(
                        ServiceOrder.planned_end.isnot(None),
                        ServiceOrder.actual_end.isnot(None),
                        ServiceOrder.actual_end <= ServiceOrder.planned_end,
                    ),
                    1,
                ),
                else_=0,
            )
        ).label("on_time_orders"),
        func.sum(
            case(
                (
                    and_(
                        ServiceOrder.planned_end.isnot(None),
                        ServiceOrder.planned_end < today,
                        ~ServiceOrder.status.in_(
                            [ServiceOrderStatus.COMPLETED, ServiceOrderStatus.ACCEPTED]
                        ),
                    ),
                    1,
                ),
                else_=0,
            )
        ).label("overdue_orders"),
    )
    if date_from:
        trend_query = trend_query.filter(func.date(ServiceOrder.created_at) >= date_from)
    if date_to:
        trend_query = trend_query.filter(func.date(ServiceOrder.created_at) <= date_to)
    if service_type:
        trend_query = trend_query.filter(ServiceOrder.service_type == service_type)
    trend_query = apply_data_scope(trend_query, ServiceOrder, current_user)
    trend_results = (
        trend_query.group_by(
            extract("year", ServiceOrder.created_at),
            extract("month", ServiceOrder.created_at),
        )
        .order_by(
            extract("year", ServiceOrder.created_at),
            extract("month", ServiceOrder.created_at),
        )
        .all()
    )

    dist_query = db.query(
        ServiceTypeModel.code.label("service_type"),
        func.count(ServiceOrder.id).label("order_count"),
    ).join(ServiceOrder, ServiceOrder.service_type == ServiceTypeModel.id)
    if date_from:
        dist_query = dist_query.filter(func.date(ServiceOrder.created_at) >= date_from)
    if date_to:
        dist_query = dist_query.filter(func.date(ServiceOrder.created_at) <= date_to)
    if service_type:
        dist_query = dist_query.filter(ServiceOrder.service_type == service_type)
    dist_query = apply_data_scope(dist_query, ServiceOrder, current_user)
    dist_results = dist_query.group_by(ServiceTypeModel.code).all()

    trend_items: list[ServiceEfficiencyTrendItemOut] = []
    for item in trend_results:
        completed_orders = int(item.completed_orders or 0)
        on_time_orders = int(item.on_time_orders or 0)
        on_time_rate = (
            round((on_time_orders / completed_orders) * 100, 2) if completed_orders > 0 else 0.0
        )
        trend_items.append(
            ServiceEfficiencyTrendItemOut(
                period=_period_key(item.year, item.month),
                new_orders=int(item.new_orders or 0),
                completed_orders=completed_orders,
                on_time_rate=on_time_rate,
                overdue_orders=int(item.overdue_orders or 0),
            )
        )

    return ServiceEfficiencyOut(
        trend=trend_items,
        service_type_distribution=[
            ServiceTypeDistributionItemOut(
                service_type=item.service_type or "",
                order_count=int(item.order_count or 0),
            )
            for item in dist_results
        ],
    )


@router.get("/drilldown", response_model=AnalyticsDrilldownOut)
def get_analytics_drilldown(
    source: str,
    period: str | None = None,
    series_type: str | None = None,
    group_value: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    service_type: int | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.ANALYTICS_READ.value)),
    db: Session = Depends(get_db),
):
    items = _build_drilldown_rows(
        db=db,
        current_user=current_user,
        source=source,
        period=period,
        series_type=series_type,
        group_value=group_value,
        date_from=date_from,
        date_to=date_to,
        service_type=service_type,
    )
    return AnalyticsDrilldownOut(total=len(items), items=items)


@router.get("/export")
def export_analytics_drilldown(
    source: str,
    period: str | None = None,
    series_type: str | None = None,
    group_value: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    service_type: int | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.ANALYTICS_READ.value)),
    db: Session = Depends(get_db),
):
    items = _build_drilldown_rows(
        db=db,
        current_user=current_user,
        source=source,
        period=period,
        series_type=series_type,
        group_value=group_value,
        date_from=date_from,
        date_to=date_to,
        service_type=service_type,
    )

    def _map_drilldown_status(category: str, status: str | None) -> str:
        if not status:
            return ""
        if category == "contract":
            return map_value(status, CONTRACT_STATUS_MAP)
        if category == "invoice":
            return map_value(status, INVOICE_STATUS_MAP)
        if category == "customer":
            return map_value(status, CUSTOMER_STATUS_MAP)
        if category == "service":
            return map_value(status, SERVICE_ORDER_STATUS_MAP)
        return status

    headers = ["类别", "主标签", "次标签", "金额", "日期", "状态", "附加信息"]
    rows = [
        [
            map_value(item.category, ANALYTICS_CATEGORY_MAP),
            item.primary_label,
            item.secondary_label or "",
            item.amount if item.amount is not None else "",
            item.date_label or "",
            _map_drilldown_status(item.category, item.status),
            item.extra or "",
        ]
        for item in items
    ]
    return export_excel_response("analytics_drilldown.xlsx", headers, rows)
