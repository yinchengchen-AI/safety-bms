from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.constants import ContractStatus, InvoiceStatus
from app.core.exceptions import (
    BusinessError,
    ContractStatusError,
    InvoiceAmountExceededError,
    NotFoundError,
)
from app.crud.invoice import crud_invoice
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceAuditRequest, InvoiceCreate
from app.services.contract_amount_service import get_available_invoice_amount


def _decimal_attr(obj: object, field: str) -> Decimal:
    return Decimal(str(getattr(obj, field, 0) or 0))


def _int_attr(obj: object, field: str) -> int:
    return int(getattr(obj, field))


class InvoiceService:
    def create_invoice(self, db: Session, *, obj_in: InvoiceCreate, applied_by: int) -> Invoice:
        # 1. 检查合同是否存在且生效（加锁防止竞态）
        contract = (
            db.query(Contract)
            .filter(Contract.id == obj_in.contract_id, Contract.is_deleted == False)
            .with_for_update()
            .first()
        )
        if not contract:
            raise NotFoundError("合同")
        if getattr(contract, "status", None) not in {
            ContractStatus.SIGNED,
            ContractStatus.EXECUTING,
            ContractStatus.COMPLETED,
        }:
            raise ContractStatusError("只有已签订或履行中的合同才能开票")

        # 2. 对已有发票加锁，防止并发超开
        db.query(Invoice).filter(
            Invoice.contract_id == _int_attr(contract, "id")
        ).with_for_update().all()

        # 3. 校验开票金额不超可开票余额
        contract_id = _int_attr(contract, "id")
        available = get_available_invoice_amount(db, contract_id=contract_id)
        if obj_in.amount > available:
            raise InvoiceAmountExceededError(
                available=available,
                requested=obj_in.amount,
            )

        return crud_invoice.create(db, obj_in=obj_in, applied_by=applied_by)

    def audit_invoice(self, db: Session, *, invoice_id: int, body: InvoiceAuditRequest) -> Invoice:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).with_for_update().first()
        if invoice is None:
            raise NotFoundError("发票")
        invoice_status = getattr(invoice, "status", None)
        if invoice_status != InvoiceStatus.APPLYING:
            raise BusinessError("只有申请中的发票才能审核")

        if body.action == "approve":
            if not body.invoice_date:
                raise BusinessError("审核通过时必须填写开票日期")
            if not body.actual_invoice_no:
                raise BusinessError("审核通过时必须填写发票号")

            contract = (
                db.query(Contract)
                .filter(Contract.id == _int_attr(invoice, "contract_id"))
                .with_for_update()
                .first()
            )
            if not contract:
                raise NotFoundError("合同")

            contract_id = _int_attr(contract, "id")
            db.query(Invoice).filter(Invoice.contract_id == contract_id).with_for_update().all()

            available = get_available_invoice_amount(db, contract_id=contract_id)
            invoice_amount = _decimal_attr(invoice, "amount")
            if invoice_amount > available:
                raise InvoiceAmountExceededError(available=available, requested=invoice_amount)

            return crud_invoice.update(
                db,
                db_obj=invoice,
                obj_in={
                    "status": InvoiceStatus.ISSUED,
                    "invoice_date": body.invoice_date,
                    "actual_invoice_no": body.actual_invoice_no,
                    "remark": body.remark,
                },
            )

        if body.action == "reject":
            if not body.remark:
                raise BusinessError("驳回时必须填写驳回原因")
            return crud_invoice.update(
                db,
                db_obj=invoice,
                obj_in={
                    "status": InvoiceStatus.REJECTED,
                    "remark": body.remark,
                },
            )

        raise BusinessError("无效的审核动作，仅支持 approve 或 reject")


invoice_service = InvoiceService()
