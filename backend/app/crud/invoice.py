from typing import List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate
from app.core.constants import InvoiceStatus


class CRUDInvoice(CRUDBase[Invoice, InvoiceCreate, InvoiceUpdate]):
    def create(self, db: Session, *, obj_in: InvoiceCreate, applied_by: int | None = None) -> Invoice:
        data = obj_in.model_dump()
        # 自动计算税额
        tax_amount = (data["amount"] * data["tax_rate"]).quantize(Decimal("0.01"))
        db_obj = Invoice(**data, tax_amount=tax_amount, applied_by=applied_by)
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
        status: Optional[InvoiceStatus] = None,
    ) -> Tuple[int, List[Invoice]]:
        query = db.query(Invoice)
        if contract_id:
            query = query.filter(Invoice.contract_id == contract_id)
        if status:
            query = query.filter(Invoice.status == status)
        total = query.count()
        items = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
        return total, items

    def get_sum_by_contract(self, db: Session, *, contract_id: int) -> Decimal:
        result = (
            db.query(func.coalesce(func.sum(Invoice.amount), 0))
            .filter(Invoice.contract_id == contract_id)
            .scalar()
        )
        return Decimal(str(result))


crud_invoice = CRUDInvoice(Invoice)
