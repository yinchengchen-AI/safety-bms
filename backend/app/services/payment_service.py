from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError, NotFoundError, PaymentAmountExceededError
from app.crud.payment import crud_payment
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.payment import ContractReceivable, PaymentCreate
from app.services.contract_amount_service import (
    get_available_payment_amount,
    get_available_payment_for_invoice,
)
from app.utils.analytics_helpers import filter_signed_contracts


class PaymentService:
    def create_payment(self, db: Session, *, obj_in: PaymentCreate, created_by: int) -> Payment:
        contract = (
            db.query(Contract)
            .filter(Contract.id == obj_in.contract_id, Contract.is_deleted == False)
            .with_for_update()
            .first()
        )
        if not contract:
            raise NotFoundError("合同")

        # 对已有收款记录加锁，防止并发超收
        db.query(Payment).filter(Payment.contract_id == contract.id).with_for_update().all()

        available = get_available_payment_amount(db, contract_id=contract.id)
        if obj_in.amount > available:
            raise PaymentAmountExceededError(
                available=available,
                requested=obj_in.amount,
            )

        # 若关联了发票，校验收款不超发票金额
        if obj_in.invoice_id:
            invoice = db.query(Invoice).filter(Invoice.id == obj_in.invoice_id).first()
            if not invoice:
                raise NotFoundError("发票")
            if invoice.contract_id != contract.id:
                raise BusinessError("关联发票不属于该合同")
            available_for_invoice = get_available_payment_for_invoice(db, invoice_id=invoice.id)
            if obj_in.amount > available_for_invoice:
                raise BusinessError(
                    f"收款金额({float(obj_in.amount):.2f})超过关联发票可收余额({float(available_for_invoice):.2f})"
                )

        return crud_payment.create(db, obj_in=obj_in, created_by=created_by)

    def get_contract_receivable(self, db: Session, *, contract_id: int) -> ContractReceivable:
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise NotFoundError("合同")

        received = crud_payment.get_sum_by_contract(db, contract_id=contract_id)
        total = contract.total_amount
        receivable = total - received

        # 逾期判断：合同结束日期已过且未收齐
        is_overdue = (
            contract.end_date is not None and contract.end_date < date.today() and receivable > 0
        )

        return ContractReceivable(
            contract_id=contract.id,
            contract_no=contract.contract_no,
            total_amount=total,
            received_amount=received,
            receivable_amount=receivable,
            is_overdue=is_overdue,
        )

    def get_overdue_contracts(self, db: Session) -> list[ContractReceivable]:
        contracts = (
            filter_signed_contracts(db.query(Contract))
            .filter(Contract.end_date < date.today())
            .all()
        )
        if not contracts:
            return []

        contract_ids = [c.id for c in contracts]
        sums = crud_payment.get_sums_by_contract_ids(db, contract_ids=contract_ids)

        result = []
        for c in contracts:
            received = sums.get(c.id, Decimal("0"))
            total = c.total_amount
            if received < total:
                result.append(
                    ContractReceivable(
                        contract_id=c.id,
                        contract_no=c.contract_no,
                        total_amount=total,
                        received_amount=received,
                        receivable_amount=total - received,
                        is_overdue=True,
                    )
                )
        return result


payment_service = PaymentService()
