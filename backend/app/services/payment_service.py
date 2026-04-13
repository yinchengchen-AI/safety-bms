from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.crud.payment import crud_payment
from app.core.exceptions import NotFoundError, PaymentAmountExceededError
from app.schemas.payment import PaymentCreate, ContractReceivable
from app.models.payment import Payment
from app.models.contract import Contract


class PaymentService:
    def create_payment(self, db: Session, *, obj_in: PaymentCreate, created_by: int) -> Payment:
        contract = (
            db.query(Contract)
            .filter(Contract.id == obj_in.contract_id)
            .with_for_update()
            .first()
        )
        if not contract:
            raise NotFoundError("合同")

        received = crud_payment.get_sum_by_contract(db, contract_id=contract.id)
        if received + obj_in.amount > contract.total_amount:
            available = contract.total_amount - received
            raise PaymentAmountExceededError(
                available=float(available),
                requested=float(obj_in.amount),
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
            contract.end_date is not None
            and contract.end_date < date.today()
            and receivable > 0
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
        from app.core.constants import ContractStatus
        contracts = (
            db.query(Contract)
            .filter(
                Contract.is_deleted == False,
                Contract.status == ContractStatus.ACTIVE,
                Contract.end_date < date.today(),
            )
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
