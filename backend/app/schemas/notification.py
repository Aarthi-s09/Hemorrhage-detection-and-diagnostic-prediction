"""
Notification Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.notification import NotificationType, NotificationPriority


class NotificationCreate(BaseModel):
    """Notification creation schema"""
    user_id: int
    title: str
    message: str
    type: NotificationType = NotificationType.GENERAL
    priority: NotificationPriority = NotificationPriority.MEDIUM
    scan_id: Optional[int] = None
    report_id: Optional[int] = None


class NotificationResponse(BaseModel):
    """Notification response schema"""
    id: int
    user_id: int
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority
    scan_id: Optional[int]
    report_id: Optional[int]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """List of notifications"""
    notifications: list[NotificationResponse]
    total: int
    unread_count: int


class NotificationMarkRead(BaseModel):
    """Mark notifications as read"""
    notification_ids: list[int]


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str  # notification, alert, update
    data: dict
    timestamp: datetime = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)
