"""
User Model - For radiologists and doctors
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    RADIOLOGIST = "radiologist"
    DOCTOR = "doctor"
    ADMIN = "admin"


class User(Base):
    """User model for authentication and role management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.RADIOLOGIST, nullable=False)
    specialty = Column(String(100), nullable=True)  # For doctors
    department = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    uploaded_scans = relationship("Scan", back_populates="uploaded_by_user", foreign_keys="Scan.uploaded_by")
    assigned_reports = relationship("Report", back_populates="assigned_doctor", foreign_keys="Report.doctor_id")
    created_reports = relationship("Report", back_populates="created_by_user", foreign_keys="Report.created_by")
    notifications = relationship("Notification", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"
