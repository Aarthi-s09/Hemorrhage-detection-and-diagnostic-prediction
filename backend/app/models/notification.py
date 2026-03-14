"""
Notification Model - Real-time alerts and notifications
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class NotificationType(str, enum.Enum):
    """Type of notification"""
    NEW_PATIENT = "new_patient"
    SCAN_COMPLETE = "scan_complete"
    REPORT_READY = "report_ready"
    CRITICAL_ALERT = "critical_alert"
    REPORT_SENT = "report_sent"
    REPORT_APPROVED = "report_approved"
    GENERAL = "general"


class NotificationPriority(str, enum.Enum):
    """Notification priority level"""
    LOW = "low"
    NORMAL = "normal"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Notification(Base):
    """Notification model for alerts and messages"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(SQLEnum(NotificationType), default=NotificationType.GENERAL)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # Reference to related entities
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<Notification {self.id}: {self.type.value} for User {self.user_id}>"
