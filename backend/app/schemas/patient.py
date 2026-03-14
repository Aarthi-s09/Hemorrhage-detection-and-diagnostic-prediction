"""
Patient Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime
from app.models.patient import Gender, Priority


class PatientBase(BaseModel):
    """Base patient schema"""
    patient_id: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Gender
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    medical_history: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    priority: Optional[Priority] = Priority.NORMAL


class PatientCreate(PatientBase):
    """Patient creation schema"""
    assigned_radiologist_id: Optional[int] = None


class PatientUpdate(BaseModel):
    """Patient update schema"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    medical_history: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    priority: Optional[Priority] = None
    assigned_radiologist_id: Optional[int] = None


class CreatedByInfo(BaseModel):
    """Info about who created the record"""
    id: int
    full_name: str
    role: str
    
    class Config:
        from_attributes = True


class PatientResponse(PatientBase):
    """Patient response schema"""
    id: int
    full_name: str = None
    age: Optional[int] = None
    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    created_by_role: Optional[str] = None
    assigned_radiologist_id: Optional[int] = None
    assigned_radiologist_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PatientListResponse(BaseModel):
    """List of patients response"""
    patients: list[PatientResponse]
    total: int
    page: int
    size: int


class PatientSearchResponse(BaseModel):
    """Patient search result"""
    id: int
    patient_id: str
    full_name: str
    date_of_birth: date
    
    class Config:
        from_attributes = True
