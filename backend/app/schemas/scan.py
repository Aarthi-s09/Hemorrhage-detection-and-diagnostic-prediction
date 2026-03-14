"""
Scan Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.scan import ScanStatus, HemorrhageType, SeverityLevel


class ScanBase(BaseModel):
    """Base scan schema"""
    patient_id: int
    scan_type: str = "CT Head"
    notes: Optional[str] = None


class ScanCreate(ScanBase):
    """Scan creation schema - used with file upload"""
    pass


class ScanUpdate(BaseModel):
    """Scan update schema"""
    notes: Optional[str] = None
    status: Optional[ScanStatus] = None


class ScanAnalysisResult(BaseModel):
    """ML analysis result schema"""
    has_hemorrhage: bool
    hemorrhage_type: HemorrhageType
    confidence_score: float = Field(..., ge=0, le=1)
    spread_ratio: float = Field(..., ge=0, le=100)
    severity_level: SeverityLevel
    slice_predictions: Optional[List[Dict[str, Any]]] = None
    affected_regions: Optional[List[str]] = None
    heatmap_path: Optional[str] = None


class ScanResponse(BaseModel):
    """Scan response schema"""
    id: int
    scan_id: str
    patient_id: int
    uploaded_by: int
    scan_date: datetime
    scan_type: str
    num_slices: Optional[int]
    slice_thickness: Optional[float]
    notes: Optional[str]
    file_path: str
    processed_path: Optional[str]
    heatmap_path: Optional[str]
    status: ScanStatus
    has_hemorrhage: int
    hemorrhage_type: HemorrhageType
    confidence_score: Optional[float]
    spread_ratio: Optional[float]
    severity_level: SeverityLevel
    severity_text: str = None
    slice_predictions: Optional[List[Dict[str, Any]]]
    affected_regions: Optional[List[str]]
    created_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    """List of scans response"""
    scans: list[ScanResponse]
    total: int
    page: int
    size: int


class ScanDetailResponse(ScanResponse):
    """Detailed scan response with patient info"""
    patient_name: Optional[str] = None
    patient_hospital_id: Optional[str] = None
    uploader_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class SliceViewerData(BaseModel):
    """Data for CT slice viewer"""
    scan_id: str
    total_slices: int
    slice_urls: List[str]
    heatmap_urls: Optional[List[str]] = None
    annotations: Optional[List[Dict[str, Any]]] = None
