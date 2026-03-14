"""
Patient API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.patient import Patient, Priority
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.schemas.patient import (
    PatientCreate, PatientUpdate, PatientResponse, 
    PatientListResponse, PatientSearchResponse
)
from app.utils.security import get_current_active_user
from app.models.user import User, UserRole


router = APIRouter()


def patient_to_response(patient: Patient) -> dict:
    """Convert patient model to response dict with created_by info"""
    data = {
        "id": patient.id,
        "patient_id": patient.patient_id,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "date_of_birth": patient.date_of_birth,
        "gender": patient.gender,
        "phone": patient.phone,
        "email": patient.email,
        "address": patient.address,
        "medical_history": patient.medical_history,
        "emergency_contact": patient.emergency_contact,
        "emergency_phone": patient.emergency_phone,
        "priority": patient.priority,
        "full_name": patient.full_name,
        "age": patient.age,
        "created_by_id": patient.created_by_id,
        "created_by_name": patient.created_by.full_name if patient.created_by else None,
        "created_by_role": patient.created_by.role.value if patient.created_by else None,
        "assigned_radiologist_id": patient.assigned_radiologist_id,
        "assigned_radiologist_name": patient.assigned_radiologist.full_name if patient.assigned_radiologist else None,
        "created_at": patient.created_at,
        "updated_at": patient.updated_at,
    }
    return data


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new patient - Only doctors can add patients"""
    # Only doctors can create patients
    if current_user.role != UserRole.DOCTOR and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can add patients"
        )
    
    # Check if patient ID already exists
    existing = db.query(Patient).filter(Patient.patient_id == patient_data.patient_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient ID already exists"
        )
    
    patient_dict = patient_data.model_dump()
    patient_dict["created_by_id"] = current_user.id
    
    patient = Patient(**patient_dict)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    # If doctor creates patient, notify radiologists
    if current_user.role == UserRole.DOCTOR:
        # Map priority
        priority_map = {
            Priority.LOW: NotificationPriority.LOW,
            Priority.NORMAL: NotificationPriority.NORMAL,
            Priority.HIGH: NotificationPriority.HIGH,
            Priority.URGENT: NotificationPriority.CRITICAL,
        }
        notif_priority = priority_map.get(patient.priority, NotificationPriority.NORMAL)
        
        # If assigned to specific radiologist, notify them
        if patient.assigned_radiologist_id:
            notification = Notification(
                user_id=patient.assigned_radiologist_id,
                type=NotificationType.NEW_PATIENT,
                title=f"New Patient Assignment ({patient.priority.value.upper()})",
                message=f"Dr. {current_user.full_name} assigned patient {patient.full_name} to you.",
                priority=notif_priority,
                patient_id=patient.id,
            )
            db.add(notification)
        else:
            # Notify all radiologists
            radiologists = db.query(User).filter(User.role == UserRole.RADIOLOGIST, User.is_active == True).all()
            for rad in radiologists:
                notification = Notification(
                    user_id=rad.id,
                    type=NotificationType.NEW_PATIENT,
                    title=f"New Patient Added ({patient.priority.value.upper()})",
                    message=f"Dr. {current_user.full_name} added patient {patient.full_name}.",
                    priority=notif_priority,
                    patient_id=patient.id,
                )
                db.add(notification)
        db.commit()
    
    return patient_to_response(patient)


@router.get("/", response_model=PatientListResponse)
async def get_patients(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of patients with pagination and search"""
    query = db.query(Patient)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Patient.first_name.ilike(search_pattern)) |
            (Patient.last_name.ilike(search_pattern)) |
            (Patient.patient_id.ilike(search_pattern))
        )
    
    # Order by priority (urgent first) then by created_at
    total = query.count()
    skip = (page - 1) * size
    patients = query.order_by(Patient.priority.desc(), Patient.created_at.desc()).offset(skip).limit(size).all()
    
    return PatientListResponse(
        patients=[patient_to_response(p) for p in patients],
        total=total,
        page=page,
        size=size
    )


@router.get("/search", response_model=list[PatientSearchResponse])
async def search_patients(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Quick search patients for dropdown/autocomplete"""
    search_pattern = f"%{q}%"
    patients = db.query(Patient).filter(
        (Patient.first_name.ilike(search_pattern)) |
        (Patient.last_name.ilike(search_pattern)) |
        (Patient.patient_id.ilike(search_pattern))
    ).limit(limit).all()
    
    results = []
    for p in patients:
        results.append(PatientSearchResponse(
            id=p.id,
            patient_id=p.patient_id,
            full_name=f"{p.first_name} {p.last_name}",
            date_of_birth=p.date_of_birth
        ))
    return results


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get patient by ID"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return patient_to_response(patient)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update patient information"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    for field, value in patient_update.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a patient"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Check if patient has scans
    if patient.scans:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete patient with existing scans"
        )
    
    db.delete(patient)
    db.commit()
