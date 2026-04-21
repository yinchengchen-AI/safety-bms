import logging
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.session import SessionLocal
from app.models.contract import Contract, ContractStatus
from app.models.notification import Notification
from app.models.service import ServiceOrder, ServiceOrderStatus

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    return _scheduler


def _check_contract_expiry() -> None:
    db = SessionLocal()
    try:
        today = datetime.now(UTC).date()
        upcoming = today + timedelta(days=7)

        # 即将到期的合同（结束日期在未来7天内，且状态为履行中）
        contracts = (
            db.query(Contract)
            .filter(
                Contract.is_deleted == False,
                Contract.status == ContractStatus.EXECUTING,
                Contract.end_date <= upcoming,
                Contract.end_date >= today,
            )
            .all()
        )
        for contract in contracts:
            existing = (
                db.query(Notification)
                .filter(
                    Notification.title == "合同即将到期",
                    Notification.content.contains(contract.contract_no),
                    Notification.created_at >= datetime.now(UTC) - timedelta(days=1),
                )
                .first()
            )
            if existing:
                continue
            days_left = (contract.end_date - today).days
            notification = Notification(
                user_id=contract.created_by,
                title="合同即将到期",
                content=(
                    f"您的合同 {contract.title}（{contract.contract_no}）"
                    f"还有 {days_left} 天即将到期，请及时处理续签或结清事宜。"
                ),
            )
            db.add(notification)
            logger.info(f"合同到期提醒已发送: {contract.contract_no}, 剩余 {days_left} 天")
        db.commit()
    except Exception:
        logger.exception("合同到期检查任务异常")
    finally:
        db.close()


def _auto_transition_contracts() -> None:
    db = SessionLocal()
    try:
        today = datetime.now(UTC).date()

        # signed → executing: 签订日期已到
        contracts = (
            db.query(Contract)
            .filter(
                Contract.is_deleted == False,
                Contract.status == ContractStatus.SIGNED,
                Contract.sign_date <= today,
            )
            .all()
        )
        for contract in contracts:
            contract.status = ContractStatus.EXECUTING
            logger.info(f"自动状态迁移: {contract.contract_no} signed → executing")

        if contracts:
            db.commit()
    except Exception:
        logger.exception("合同自动状态迁移任务异常")
    finally:
        db.close()


def _check_service_order_deadline() -> None:
    db = SessionLocal()
    try:
        today = datetime.now(UTC).date()
        upcoming = today + timedelta(days=3)

        orders = (
            db.query(ServiceOrder)
            .filter(
                ServiceOrder.is_deleted == False,
                ServiceOrder.status.in_(
                    [
                        ServiceOrderStatus.PENDING,
                        ServiceOrderStatus.IN_PROGRESS,
                    ]
                ),
                ServiceOrder.scheduled_date <= upcoming,
                ServiceOrder.scheduled_date >= today,
            )
            .all()
        )
        for order in orders:
            existing = (
                db.query(Notification)
                .filter(
                    Notification.title == "服务工单即将到期",
                    Notification.content.contains(order.order_no),
                    Notification.created_at >= datetime.now(UTC) - timedelta(days=1),
                )
                .first()
            )
            if existing:
                continue
            days_left = (order.scheduled_date - today).days
            notification = Notification(
                user_id=order.created_by,
                title="服务工单即将到期",
                content=(
                    f"您的服务工单 {order.order_no} "
                    f"还有 {days_left} 天即将到期，请及时安排服务。"
                ),
            )
            db.add(notification)
            logger.info(f"服务工单到期提醒已发送: {order.order_no}, 剩余 {days_left} 天")
        db.commit()
    except Exception:
        logger.exception("服务工单到期检查任务异常")
    finally:
        db.close()


def start_scheduler() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        # 每天上午9点检查合同到期
        scheduler.add_job(
            _check_contract_expiry,
            trigger=CronTrigger(hour=9, minute=0),
            id="check_contract_expiry",
            replace_existing=True,
        )
        # 每天凌晨1点自动状态迁移 signed → executing
        scheduler.add_job(
            _auto_transition_contracts,
            trigger=CronTrigger(hour=1, minute=0),
            id="auto_transition_contracts",
            replace_existing=True,
        )
        # 每天上午8点检查服务工单到期
        scheduler.add_job(
            _check_service_order_deadline,
            trigger=CronTrigger(hour=8, minute=0),
            id="check_service_order_deadline",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("定时任务调度器已启动")


def shutdown_scheduler() -> None:
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已停止")
