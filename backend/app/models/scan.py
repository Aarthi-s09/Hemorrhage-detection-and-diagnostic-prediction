"""
Scan Model - CT Scan information and analysis results
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class ScanStatus(str, enum.Enum):
    """Scan processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class HemorrhageType(str, enum.Enum):
    """Type of hemorrhage detected"""
    NONE = "none"
    EPIDURAL = "epidural"
    SUBDURAL = "subdural"
    SUBARACHNOID = "subarachnoid"
    INTRAPARENCHYMAL = "intraparenchymal"
    INTRAVENTRICULAR = "intraventricular"
    MULTIPLE = "multiple"


class SeverityLevel(str, enum.Enum):
    """Severity level based on spread ratio"""
    NONE = "none"
    MILD = "mild"  # 0-30%
    MODERATE = "moderate"  # 30-70%
    SEVERE = "severe"  # 70-100%


class Scan(Base):
    """CT Scan model with analysis results"""
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Scan metadata
    scan_date = Column(DateTime, default=datetime.utcnow)
    scan_type = Column(String(50), default="CT Head")
    num_slices = Column(Integer, nullable=True)
    slice_thickness = Column(Float, nullable=True)  # in mm
    notes = Column(Text, nullable=True)
    
    # File paths
    file_path = Column(String(500), nullable=False)  # Original scan
    processed_path = Column(String(500), nullable=True)  # Processed images
    heatmap_path = Column(String(500), nullable=True)  # GradCAM heatmap
    
    # Analysis Results
    status = Column(SQLEnum(ScanStatus), default=ScanStatus.PENDING)
    has_hemorrhage = Column(Integer, default=0)  # 0: No, 1: Yes
    hemorrhage_type = Column(SQLEnum(HemorrhageType), default=HemorrhageType.NONE)
    confidence_score = Column(Float, nullable=True)  # 0-1 confidence
    spread_ratio = Column(Float, nullable=True)  # 0-100% severity
    severity_level = Column(SQLEnum(SeverityLevel), default=SeverityLevel.NONE)
    
    # Detailed predictions per slice
    slice_predictions = Column(JSON, nullable=True)  # List of predictions per slice
    affected_regions = Column(JSON, nullable=True)  # Detected affected regions
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="scans")
    uploaded_by_user = relationship("User", back_populates="uploaded_scans", foreign_keys=[uploaded_by])
    report = relationship("Report", back_populates="scan", uselist=False)
    
    @property
    def severity_text(self):
        if self.spread_ratio is None:
            return "Unknown"
        if self.spread_ratio < 30:
            return "Mild (Standard Review)"
        elif self.spread_ratio < 70:
            return "Moderate (Priority Review)"
        else:
            return "Severe (Immediate Alert Required)"
    
    def __repr__(self):
        return f"<Scan {self.scan_id}: {self.status.value}>"
