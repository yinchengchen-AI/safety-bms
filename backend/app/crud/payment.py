from typing import List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate


class CRUDPayment(CRUDBase[Payment, PaymentCreate, PaymentUpdate]):
    def create(self, db: Session, *, obj_in: PaymentCreate, created_by: int | None = None) -> Payment:
        db_obj = Payment(**obj_in.model_dump(), created_by=created_by)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 20,
        contract_id: Optional[int] = None,
        invoice_id: Optional[int] = None,
    ) -> Tuple[int, List[Payment]]:
        query = db.query(Payment)
        if contract_id:
            query = query.filter(Payment.contract_id == contract_id)
        if invoice_id:
            query = query.filter(Payment.invoice_id == invoice_id)
        total = query.count()
        items = query.order_by(Payment.payment_date.desc()).offset(skip).limit(limit).all()
        return total, items

    def get_sum_by_contract(self, db: Session, *, contract_id: int) -> Decimal:
        result = (
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.contract_id == contract_id)
            .scalar()
        )
        return Decimal(str(result))

    def get_sum_by_invoice(self, db: Session, *, invoice_id: int) -> Decimal:
        result = (
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.invoice_id == invoice_id)
            .scalar()
        )
        return Decimal(str(result))

    def get_sums_by_contract_ids(self, db: Session, *, contract_ids: List[int]) -> dict[int, Decimal]:
        results = (
            db.query(Payment.contract_id, func.coalesce(func.sum(Payment.amount), 0).label("total"))
            .filter(Payment.contract_id.in_(contract_ids))
            .group_by(Payment.contract_id)
            .all()
        )
        return {r.contract_id: Decimal(str(r.total)) for r in results}

    def get_monthly_stats(self, db: Session, *, year: int) -> List[dict]:
        """按月统计收款金额（用于折线图）"""
        from sqlalchemy import extract
        results = (
            db.query(
                extract("month", Payment.payment_date).label("month"),
                func.sum(Payment.amount).label("total"),
            )
            .filter(extract("year", Payment.payment_date) == year)
            .group_by(extract("month", Payment.payment_date))
            .order_by(extract("month", Payment.payment_date))
            .all()
        )
        return [{"month": int(r.month), "total": float(r.total or 0)} for r in results]


crud_payment = CRUDPayment(Payment)
