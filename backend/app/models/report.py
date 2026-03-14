"""
Report Model - Medical report generated from scan analysis
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class ReportStatus(str, enum.Enum):
    """Report workflow status"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"


class Report(Base):
    """Medical report model"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), unique=True, index=True, nullable=False)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)  # Direct patient reference
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Radiologist
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Assigned doctor
    
    # Report content
    title = Column(String(255), nullable=False)
    findings = Column(Text, nullable=False)  # AI-generated findings
    radiologist_notes = Column(Text, nullable=True)  # Additional notes
    recommendations = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)
    
    # Severity summary
    severity_score = Column(Float, nullable=True)  # 0-100
    is_critical = Column(Boolean, default=False)
    
    # Status tracking
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.DRAFT)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # PDF report
    pdf_path = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scan = relationship("Scan", back_populates="report")
    patient = relationship("Patient", back_populates="reports")
    created_by_user = relationship("User", back_populates="created_reports", foreign_keys=[created_by])
    assigned_doctor = relationship("User", back_populates="assigned_reports", foreign_keys=[doctor_id])
    
    def __repr__(self):
        return f"<Report {self.report_id}: {self.status.value}>"
