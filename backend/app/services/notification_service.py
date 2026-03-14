"""
Notification Service - Handle alerts and notifications
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.scan import Scan
from app.models.report import Report
from app.schemas.notification import NotificationCreate


class NotificationService:
    """Service for notification operations"""
    
    @staticmethod
    def create_notification(db: Session, notification_data: NotificationCreate) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=notification_data.user_id,
            title=notification_data.title,
            message=notification_data.message,
            type=notification_data.type,
            priority=notification_data.priority,
            scan_id=notification_data.scan_id,
            report_id=notification_data.report_id
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    @staticmethod
    def create_scan_complete_notification(db: Session, scan: Scan, user_id: int) -> Notification:
        """Create notification for completed scan"""
        priority = NotificationPriority.CRITICAL if scan.spread_ratio and scan.spread_ratio >= 70 else NotificationPriority.MEDIUM
        
        message = f"CT scan {scan.scan_id} analysis complete. "
        if scan.has_hemorrhage:
            message += f"Hemorrhage detected with {scan.spread_ratio:.1f}% spread ratio."
        else:
            message += "No hemorrhage detected."
        
        notification = Notification(
            user_id=user_id,
            title="Scan Analysis Complete",
            message=message,
            type=NotificationType.SCAN_COMPLETE,
            priority=priority,
            scan_id=scan.id
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    @staticmethod
    def create_critical_alert(db: Session, scan: Scan, doctor_id: int) -> Notification:
        """Create critical alert for severe hemorrhage"""
        notification = Notification(
            user_id=doctor_id,
            title="⚠️ CRITICAL: Severe Hemorrhage Detected",
            message=f"Urgent attention required. Patient scan {scan.scan_id} shows severe hemorrhage with {scan.spread_ratio:.1f}% spread ratio. Immediate review recommended.",
            type=NotificationType.CRITICAL_ALERT,
            priority=NotificationPriority.CRITICAL,
            scan_id=scan.id
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    @staticmethod
    def create_report_ready_notification(db: Session, report: Report, user_id: int) -> Notification:
        """Create notification when report is ready"""
        notification = Notification(
            user_id=user_id,
            title="Report Ready for Review",
            message=f"Report {report.report_id} is ready for verification.",
            type=NotificationType.REPORT_READY,
            priority=NotificationPriority.MEDIUM,
            report_id=report.id
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    @staticmethod
    def create_report_sent_notification(db: Session, report: Report, doctor_id: int) -> Notification:
        """Create notification when report is sent to doctor"""
        priority = NotificationPriority.CRITICAL if report.is_critical else NotificationPriority.MEDIUM
        
        notification = Notification(
            user_id=doctor_id,
            title="New Medical Report Received",
            message=f"You have received a new report {report.report_id}. {'CRITICAL CASE - Immediate attention required.' if report.is_critical else 'Please review at your earliest convenience.'}",
            type=NotificationType.REPORT_SENT,
            priority=priority,
            report_id=report.id
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications for a user"""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """Get count of unread notifications"""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
    
    @staticmethod
    def mark_as_read(db: Session, notification_ids: List[int], user_id: int) -> int:
        """Mark notifications as read"""
        updated = db.query(Notification).filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == user_id
        ).update(
            {"is_read": True, "read_at": datetime.utcnow()},
            synchronize_session=False
        )
        db.commit()
        return updated
    
    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """Mark all user notifications as read"""
        updated = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update(
            {"is_read": True, "read_at": datetime.utcnow()},
            synchronize_session=False
        )
        db.commit()
        return updated
    
    @staticmethod
    def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        deleted = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).delete()
        db.commit()
        return deleted > 0
    
    @staticmethod
    def get_critical_notifications(db: Session, user_id: int) -> List[Notification]:
        """Get unread critical notifications"""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.priority == NotificationPriority.CRITICAL,
            Notification.is_read == False
        ).order_by(Notification.created_at.desc()).all()
