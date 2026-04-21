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

    def update(self, db: Session, *, db_obj: Invoice, obj_in: InvoiceUpdate | dict) -> Invoice:
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        # 金额或税率变更时重新计算税额
        if "amount" in update_data or "tax_rate" in update_data:
            amount = getattr(db_obj, "amount", Decimal("0")) or Decimal("0")
            tax_rate = getattr(db_obj, "tax_rate", Decimal("0.06")) or Decimal("0.06")
            db_obj.tax_amount = (amount * tax_rate / (Decimal("1") + tax_rate)).quantize(
                Decimal("0.01")
            )
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
        query = db.query(Invoice).filter(Invoice.is_deleted == False)
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
            .filter(Invoice.is_deleted == False)
            .filter(Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.SENT]))
            .scalar()
        )
        return Decimal(str(result))

    def get_sums_by_contract_ids(
        self, db: Session, *, contract_ids: list[int]
    ) -> dict[int, Decimal]:
        results = (
            db.query(Invoice.contract_id, func.coalesce(func.sum(Invoice.amount), 0).label("total"))
            .filter(Invoice.contract_id.in_(contract_ids))
            .filter(Invoice.is_deleted == False)
            .filter(Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.SENT]))
            .group_by(Invoice.contract_id)
            .all()
        )
        return {r.contract_id: Decimal(str(r.total)) for r in results}


crud_invoice = CRUDInvoice(Invoice)
