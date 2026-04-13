from datetime import datetime
from typing import List
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    is_read: bool
    notification_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListOut(BaseModel):
    items: List[NotificationOut]
