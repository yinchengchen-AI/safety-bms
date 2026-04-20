from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationService:
    def create(
        self,
        db: Session,
        *,
        user_id: int,
        title: str,
        content: str,
        notification_type: str = "business",
    ) -> Notification:
        obj = Notification(
            user_id=user_id, title=title, content=content, notification_type=notification_type
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj


notification_service = NotificationService()
