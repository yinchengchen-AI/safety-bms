from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.common import PageResponse, ResponseMsg
from app.schemas.notification import NotificationOut
from app.utils.pagination import make_page_response

router = APIRouter(prefix="/notifications", tags=["通知中心"])


@router.get("", response_model=PageResponse[NotificationOut])
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    is_read: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    total = query.count()
    items = query.order_by(Notification.created_at.desc()).offset(skip).limit(page_size).all()
    return make_page_response(total, items, page, page_size)


@router.post("/{notification_id}/read", response_model=ResponseMsg)
def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )
    if notification:
        notification.is_read = True
        db.commit()
    return {"message": "标记已读成功"}


@router.post("/read-all", response_model=ResponseMsg)
def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"message": "全部标为已读"}


@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .count()
    )
    return {"count": count}


@router.delete("/clear-all", response_model=ResponseMsg)
def clear_all_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
    ).delete(synchronize_session=False)
    db.commit()
    return {"message": "全部清空成功"}


@router.delete("/{notification_id}", response_model=ResponseMsg)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )
    if notification:
        db.delete(notification)
        db.commit()
    return {"message": "删除成功"}
