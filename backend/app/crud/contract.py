from datetime import UTC
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.core.constants import ContractStatus
from app.core.exceptions import ContractStatusError
from app.crud.base import CRUDBase
from app.models.contract import Contract, ContractAttachment, ContractChange, ContractTemplate
from app.schemas.contract import ContractCreate, ContractTemplateCreate, ContractUpdate
from app.services.contract_amount_service import get_invoiced_amount, get_received_amount

ALLOWED_TRANSITIONS = {
    ContractStatus.DRAFT: {ContractStatus.SIGNED, ContractStatus.TERMINATED},
    ContractStatus.SIGNED: {ContractStatus.EXECUTING, ContractStatus.TERMINATED},
    ContractStatus.EXECUTING: {ContractStatus.COMPLETED, ContractStatus.TERMINATED},
    ContractStatus.COMPLETED: set(),
    ContractStatus.TERMINATED: set(),
}


class CRUDContract(CRUDBase[Contract, ContractCreate, ContractUpdate]):
    def create(
        self, db: Session, *, obj_in: ContractCreate, created_by: int | None = None
    ) -> Contract:
        db_obj = Contract(**obj_in.model_dump(), created_by=created_by)
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
        customer_id: int | None = None,
        status: ContractStatus | None = None,
        keyword: str | None = None,
    ) -> tuple[int, list[Contract]]:
        query = db.query(Contract).filter(Contract.is_deleted == False)
        if customer_id:
            query = query.filter(Contract.customer_id == customer_id)
        if status:
            query = query.filter(Contract.status == status)
        if keyword:
            query = query.filter(
                (Contract.title.ilike(f"%{keyword}%"))
                | (Contract.contract_no.ilike(f"%{keyword}%"))
            )
        total = query.count()
        items = (
            query.options(joinedload(Contract.customer))
            .order_by(Contract.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return total, items

    def update_status(
        self,
        db: Session,
        *,
        db_obj: Contract,
        new_status: ContractStatus,
        changed_by: int,
        remark: str = "",
    ) -> Contract:
        old_status = db_obj.status
        if new_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
            raise ContractStatusError(f"状态不允许从 {old_status.value} 变更为 {new_status.value}")
        if new_status == ContractStatus.SIGNED:
            has_signed_attachment = (
                db.query(ContractAttachment.id)
                .filter(ContractAttachment.contract_id == db_obj.id)
                .filter(ContractAttachment.file_type == "signed")
                .first()
                is not None
            )
            if not has_signed_attachment:
                raise ContractStatusError("请先上传已签合同附件")
        db_obj.status = new_status
        change = ContractChange(
            contract_id=db_obj.id,
            changed_by=changed_by,
            change_summary=f"状态变更: {old_status.value} → {new_status.value}",
            before_status=old_status.value,
            after_status=new_status.value,
            remark=remark,
        )
        db.add(change)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_invoiced_amount(self, db: Session, *, contract_id: int) -> Decimal:
        return get_invoiced_amount(db, contract_id)

    def get_received_amount(self, db: Session, *, contract_id: int) -> Decimal:
        return get_received_amount(db, contract_id)

    def soft_delete(self, db: Session, *, contract_id: int) -> None:
        from datetime import datetime

        contract = db.query(Contract).get(contract_id)
        if contract:
            contract.is_deleted = True
            contract.deleted_at = datetime.now(UTC)
            db.commit()


class CRUDContractTemplate(CRUDBase[ContractTemplate, ContractTemplateCreate, dict]):
    def create(
        self,
        db: Session,
        *,
        obj_in: ContractTemplateCreate,
        created_by: int | None = None,
    ) -> ContractTemplate:
        db_obj = ContractTemplate(**obj_in.model_dump(), created_by=created_by)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


crud_contract = CRUDContract(Contract)
crud_contract_template = CRUDContractTemplate(ContractTemplate)
