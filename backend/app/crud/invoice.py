from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.constants import InvoiceStatus
from app.crud.base import CRUDBase
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate


class CRUDInvoice(CRUDBase[Invoice, InvoiceCreate, InvoiceUpdate]):
    def create(
        self, db: Session, *, obj_in: InvoiceCreate, applied_by: int | None = None
    ) -> Invoice:
        data = obj_in.model_dump()
        # 自动计算税额
        tax_amount = (
            data["amount"] * data["tax_rate"] / (Decimal("1") + data["tax_rate"])
        ).quantize(Decimal("0.01"))
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
        contract_id: int | None = None,
        status: InvoiceStatus | None = None,
    ) -> tuple[int, list[Invoice]]:
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
            .filter(Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.SENT]))
            .scalar()
        )
        return Decimal(str(result))


crud_invoice = CRUDInvoice(Invoice)
