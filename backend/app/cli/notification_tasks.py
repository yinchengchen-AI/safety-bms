"""
系统通知定时任务 CLI
用法：
    PYTHONPATH=. python app/cli/notification_tasks.py
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session, joinedload

from app.db.session import SessionLocal
from app.db.base_all import Base  # noqa: F401
from app.core.constants import ContractStatus
from app.models.contract import Contract
from app.services.payment_service import payment_service
from app.services.notification_service import notification_service


def notify_expiring_contracts(db: Session, days_before: int = 7) -> int:
    """提醒即将到期的合同应收（每天只提醒恰好 N 天后到期的合同，避免重复）"""
    target_date = date.today() + timedelta(days=days_before)
    contracts = (
        db.query(Contract)
        .options(joinedload(Contract.customer))
        .filter(
            Contract.is_deleted == False,
            Contract.status.in_([ContractStatus.ACTIVE, ContractStatus.SIGNED]),
            Contract.end_date == target_date,
        )
        .all()
    )
    count = 0
    for contract in contracts:
        receivable = payment_service.get_contract_receivable(db, contract_id=contract.id)
        if receivable.receivable_amount > 0 and contract.created_by is not None:
            total_str = format(contract.total_amount, ".2f") if contract.total_amount is not None else "0.00"
            received_str = format(receivable.received_amount, ".2f")
            receivable_str = format(receivable.receivable_amount, ".2f")
            customer_name = contract.customer.name if contract.customer else ""
            customer_line = f"客户：{customer_name}\n" if customer_name else ""
            notification_service.create(
                db,
                user_id=contract.created_by,
                title="合同即将到期应收提醒",
                content=(
                    f"合同 {contract.title}（{contract.contract_no}）将于 {contract.end_date} 到期。\n"
                    f"{customer_line}"
                    f"合同总金额：{total_str} 元，已收款：{received_str} 元，"
                    f"应收余额：{receivable_str} 元，请及时跟进回款。"
                ),
            )
            count += 1
    return count


def notify_overdue_contracts(db: Session) -> int:
    """提醒逾期应收合同"""
    contracts = (
        db.query(Contract)
        .options(joinedload(Contract.customer))
        .filter(
            Contract.is_deleted == False,
            Contract.status.in_([ContractStatus.ACTIVE, ContractStatus.SIGNED]),
            Contract.end_date < date.today(),
        )
        .all()
    )
    count = 0
    for contract in contracts:
        receivable = payment_service.get_contract_receivable(db, contract_id=contract.id)
        if receivable.receivable_amount > 0 and contract.created_by is not None:
            total_str = format(contract.total_amount, ".2f") if contract.total_amount is not None else "0.00"
            received_str = format(receivable.received_amount, ".2f")
            receivable_str = format(receivable.receivable_amount, ".2f")
            customer_name = contract.customer.name if contract.customer else ""
            customer_line = f"客户：{customer_name}\n" if customer_name else ""
            notification_service.create(
                db,
                user_id=contract.created_by,
                title="逾期应收提醒",
                content=(
                    f"合同 {contract.title}（{contract.contract_no}）已逾期（结束日期 {contract.end_date}）。\n"
                    f"{customer_line}"
                    f"合同总金额：{total_str} 元，已收款：{received_str} 元，"
                    f"应收余额：{receivable_str} 元，请尽快催收。"
                ),
            )
            count += 1
    return count


def main():
    db = SessionLocal()
    try:
        expiring_count = notify_expiring_contracts(db, days_before=7)
        overdue_count = notify_overdue_contracts(db)
        print(f"✅ 发送即将到期提醒 {expiring_count} 条")
        print(f"✅ 发送逾期应收提醒 {overdue_count} 条")
    finally:
        db.close()


if __name__ == "__main__":
    main()
