import logging
import socket
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.session import SessionLocal
from app.models.contract import Contract, ContractStatus
from app.models.notification import Notification
from app.models.service import ServiceOrder, ServiceOrderStatus
from app.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None

# Redis 分布式锁配置
_SCHEDULER_LOCK_KEY = "safety_bms:scheduler_lock"
_SCHEDULER_LOCK_TTL = 60  # 锁过期时间（秒），应大于调度器心跳间隔


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    return _scheduler


def _acquire_scheduler_lock() -> bool:
    """通过 Redis 获取调度器启动锁，防止多实例重复启动调度任务。"""
    try:
        redis_client = get_redis_client()
        host_id = socket.gethostname()
        # NX: 仅在 key 不存在时设置；EX: 设置过期时间
        acquired = redis_client.set(
            _SCHEDULER_LOCK_KEY,
            host_id,
            nx=True,
            ex=_SCHEDULER_LOCK_TTL,
        )
        return bool(acquired)
    except Exception:
        logger.exception("获取调度器 Redis 锁失败，当前实例将不启动调度器")
        return False


def _renew_scheduler_lock() -> None:
    """续期调度器锁，应在主调度任务中定期调用。"""
    try:
        redis_client = get_redis_client()
        host_id = socket.gethostname()
        # 只有当当前主机持有锁时才续期
        current = redis_client.get(_SCHEDULER_LOCK_KEY)
        if current and current.decode() == host_id:
            redis_client.expire(_SCHEDULER_LOCK_KEY, _SCHEDULER_LOCK_TTL)
    except Exception:
        logger.exception("续期调度器 Redis 锁失败")


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


def _wrap_with_lock_renewal(fn):
    """包装任务函数，执行前续期分布式锁。"""

    def wrapper():
        _renew_scheduler_lock()
        fn()

    return wrapper


def start_scheduler() -> None:
    scheduler = get_scheduler()
    if scheduler.running:
        return

    if not _acquire_scheduler_lock():
        logger.info("未获取到调度器分布式锁，当前实例不启动定时任务（其他实例已持有锁）")
        return

    # 每天上午9点检查合同到期
    scheduler.add_job(
        _wrap_with_lock_renewal(_check_contract_expiry),
        trigger=CronTrigger(hour=9, minute=0),
        id="check_contract_expiry",
        replace_existing=True,
    )
    # 每天凌晨1点自动状态迁移 signed → executing
    scheduler.add_job(
        _wrap_with_lock_renewal(_auto_transition_contracts),
        trigger=CronTrigger(hour=1, minute=0),
        id="auto_transition_contracts",
        replace_existing=True,
    )
    # 每天上午8点检查服务工单到期
    scheduler.add_job(
        _wrap_with_lock_renewal(_check_service_order_deadline),
        trigger=CronTrigger(hour=8, minute=0),
        id="check_service_order_deadline",
        replace_existing=True,
    )
    # 每 30 秒续期一次锁，确保持有锁的实例存活
    scheduler.add_job(
        _renew_scheduler_lock,
        trigger="interval",
        seconds=30,
        id="scheduler_lock_renewal",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("定时任务调度器已启动（已获取分布式锁）")


def shutdown_scheduler() -> None:
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已停止")
    try:
        redis_client = get_redis_client()
        host_id = socket.gethostname()
        current = redis_client.get(_SCHEDULER_LOCK_KEY)
        if current and current.decode() == host_id:
            redis_client.delete(_SCHEDULER_LOCK_KEY)
            logger.info("调度器分布式锁已释放")
    except Exception:
        logger.exception("释放调度器分布式锁失败")
