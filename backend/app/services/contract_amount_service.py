from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.constants import InvoiceStatus
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.models.payment import Payment


def get_invoiced_amount(db: Session, contract_id: int) -> Decimal:
    """合同已开票金额（仅统计 ISSUED/SENT 且未删除的发票）"""
    result = (
        db.query(func.coalesce(func.sum(Invoice.amount), 0))
        .filter(Invoice.contract_id == contract_id)
        .filter(Invoice.is_deleted == False)
        .filter(Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.SENT]))
        .scalar()
    )
    return Decimal(str(result))


def get_received_amount(db: Session, contract_id: int) -> Decimal:
    """合同已收款金额（仅统计未删除的收款）"""
    result = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.contract_id == contract_id)
        .filter(Payment.is_deleted == False)
        .scalar()
    )
    return Decimal(str(result))


def get_available_invoice_amount(db: Session, contract_id: int) -> Decimal:
    """合同可开票余额 = 合同总额 - 已开票金额"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        return Decimal("0")
    total = Decimal(str(getattr(contract, "total_amount", 0) or 0))
    invoiced = get_invoiced_amount(db, contract_id)
    return total - invoiced


def get_available_payment_amount(db: Session, contract_id: int) -> Decimal:
    """合同可收款余额 = 合同总额 - 已收款金额"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        return Decimal("0")
    total = Decimal(str(getattr(contract, "total_amount", 0) or 0))
    received = get_received_amount(db, contract_id)
    return total - received


def get_available_payment_for_invoice(db: Session, invoice_id: int) -> Decimal:
    """发票可收款余额 = 发票金额 - 该发票已收款金额"""
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id)
        .filter(Invoice.is_deleted == False)
        .first()
    )
    if not invoice:
        return Decimal("0")
    invoice_amount = Decimal(str(getattr(invoice, "amount", 0) or 0))
    paid = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.invoice_id == invoice_id)
        .filter(Payment.is_deleted == False)
        .scalar()
    )
    return invoice_amount - Decimal(str(paid))
