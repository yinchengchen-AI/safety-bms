"""
统计分析统一口径过滤器。
所有 dashboard、analytics、导出等统计逻辑都应使用这些函数，确保口径一致。
"""

from sqlalchemy.orm import Query

from app.core.constants import ContractStatus, InvoiceStatus
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.models.payment import Payment


def filter_signed_contracts(query: Query) -> Query:
    """
    签约额口径：已签订 / 履行中 / 已完成，且未软删除，且 sign_date 不为空。
    适用于所有"签约额"统计场景。
    """
    return query.filter(
        Contract.is_deleted == False,
        Contract.sign_date.isnot(None),
        Contract.status.in_(
            [ContractStatus.SIGNED, ContractStatus.EXECUTING, ContractStatus.COMPLETED]
        ),
    )


def filter_valid_invoices(query: Query) -> Query:
    """
    开票额口径：已开票 / 已寄出，且未软删除。
    适用于所有"开票额"统计场景。
    """
    return query.filter(
        Invoice.is_deleted == False,
        Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.SENT]),
    )


def filter_valid_payments(query: Query) -> Query:
    """
    收款额口径：收款记录未软删除，且关联合同满足签约口径。
    适用于所有"收款额"统计场景。
    """
    return (
        query.join(Contract, Payment.contract_id == Contract.id)
        .filter(Payment.is_deleted == False)
        .filter(
            Contract.is_deleted == False,
            Contract.sign_date.isnot(None),
            Contract.status.in_(
                [ContractStatus.SIGNED, ContractStatus.EXECUTING, ContractStatus.COMPLETED]
            ),
        )
    )
