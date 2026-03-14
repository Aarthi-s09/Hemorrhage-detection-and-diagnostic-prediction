"""
Patient Model - Patient information
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum as SQLEnum, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class Gender(str, enum.Enum):
    """Patient gender enumeration"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Priority(str, enum.Enum):
    """Priority level for patient cases"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Patient(Base):
    """Patient model for storing patient information"""
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), unique=True, index=True, nullable=False)  # Hospital ID
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(SQLEnum(Gender), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    emergency_contact = Column(String(255), nullable=True)
    emergency_phone = Column(String(20), nullable=True)
    priority = Column(SQLEnum(Priority), default=Priority.NORMAL)  # Priority level
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who added this patient
    assigned_radiologist_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Assigned radiologist
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scans = relationship("Scan", back_populates="patient")
    reports = relationship("Report", back_populates="patient")
    created_by = relationship("User", foreign_keys=[created_by_id], backref="created_patients")
    assigned_radiologist = relationship("User", foreign_keys=[assigned_radiologist_id], backref="assigned_patients")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = datetime.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    def __repr__(self):
        return f"<Patient {self.patient_id}: {self.full_name}>"
