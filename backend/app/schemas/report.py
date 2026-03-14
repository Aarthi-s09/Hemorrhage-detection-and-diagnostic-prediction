"""
Report Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.report import ReportStatus


class ReportBase(BaseModel):
    """Base report schema"""
    title: str = Field(..., min_length=5, max_length=255)
    findings: str
    radiologist_notes: Optional[str] = None
    recommendations: Optional[str] = None
    conclusion: Optional[str] = None


class ReportCreate(ReportBase):
    """Report creation schema"""
    scan_id: int
    doctor_id: Optional[int] = None


class ReportUpdate(BaseModel):
    """Report update schema"""
    title: Optional[str] = None
    findings: Optional[str] = None
    radiologist_notes: Optional[str] = None
    recommendations: Optional[str] = None
    conclusion: Optional[str] = None
    doctor_id: Optional[int] = None


class ReportVerify(BaseModel):
    """Report verification by radiologist"""
    is_verified: bool = True
    radiologist_notes: Optional[str] = None


class ReportSend(BaseModel):
    """Send report to doctor"""
    doctor_id: int
    additional_notes: Optional[str] = None


class ReportResponse(ReportBase):
    """Report response schema"""
    id: int
    report_id: str
    scan_id: int
    created_by: int
    doctor_id: Optional[int]
    severity_score: Optional[float]
    is_critical: bool
    status: ReportStatus
    is_verified: bool
    verified_at: Optional[datetime]
    sent_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    pdf_path: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReportDetailResponse(ReportResponse):
    """Detailed report with related info"""
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    creator_name: Optional[str] = None
    doctor_name: Optional[str] = None
    scan_info: Optional[dict] = None
    
    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """List of reports"""
    reports: list[ReportResponse]
    total: int
    page: int
    size: int


class ReportPDFResponse(BaseModel):
    """PDF generation response"""
    report_id: str
    pdf_url: str
    generated_at: datetime
