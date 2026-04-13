from decimal import Decimal
from sqlalchemy.orm import Session

from app.crud.invoice import crud_invoice
from app.crud.contract import crud_contract
from app.core.exceptions import InvoiceAmountExceededError, NotFoundError, ContractStatusError
from app.core.constants import ContractStatus
from app.schemas.invoice import InvoiceCreate
from app.models.invoice import Invoice
from app.models.contract import Contract


class InvoiceService:
    def create_invoice(self, db: Session, *, obj_in: InvoiceCreate, applied_by: int) -> Invoice:
        # 1. 检查合同是否存在且生效（加锁防止竞态）
        contract = (
            db.query(Contract)
            .filter(Contract.id == obj_in.contract_id)
            .with_for_update()
            .first()
        )
        if not contract:
            raise NotFoundError("合同")
        if contract.status != ContractStatus.ACTIVE:
            raise ContractStatusError("只有生效状态的合同才能开票")

        # 2. 校验开票金额不超可开票余额
        already_invoiced = crud_invoice.get_sum_by_contract(db, contract_id=contract.id)
        available = Decimal(str(contract.total_amount)) - already_invoiced
        if obj_in.amount > available:
            raise InvoiceAmountExceededError(
                available=float(available),
                requested=float(obj_in.amount),
            )

        return crud_invoice.create(db, obj_in=obj_in, applied_by=applied_by)


invoice_service = InvoiceService()
