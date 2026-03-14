"""
CT Scan API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import os
import json

from app.database import get_db
from app.models.scan import Scan, ScanStatus, SeverityLevel
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.scan import (
    ScanResponse, ScanListResponse, ScanDetailResponse, 
    SliceViewerData, ScanAnalysisResult
)
from app.services.scan_service import ScanService
from app.services.report_service import ReportService
from app.services.notification_service import NotificationService
from app.utils.security import get_current_active_user, require_radiologist
from app.config import settings
from app.websocket import connection_manager


router = APIRouter()


async def process_scan_background(scan_id: int, db_url: str):
    """Background task to process scan with ML model"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import random
    import asyncio
    from datetime import datetime
    
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return
        
        # Update status to processing
        scan.status = ScanStatus.PROCESSING
        db.commit()
        
        # Simulate processing time (2-5 seconds)
        await asyncio.sleep(random.uniform(2, 5))
        
        # MOCK ML INFERENCE (for development - replace with real model later)
        # Generate realistic fake results
        has_hemorrhage = random.choice([True, True, False])  # 67% chance of detecting hemorrhage
        spread_ratio = random.uniform(5, 85) if has_hemorrhage else 0.0  # 5% to 85% as actual percentage
        
        results = {
            'has_hemorrhage': has_hemorrhage,
            'hemorrhage_type': random.choice(['subdural', 'epidural', 'subarachnoid', 'intraventricular']) if has_hemorrhage else None,
            'confidence': random.uniform(0.75, 0.98),
            'spread_ratio': spread_ratio,
            'slice_predictions': None,
            'affected_regions': ['frontal', 'temporal'] if has_hemorrhage else [],
            'heatmap_path': None
        }
        
        # Update scan with results
        scan.has_hemorrhage = 1 if results['has_hemorrhage'] else 0
        scan.hemorrhage_type = results['hemorrhage_type']
        scan.confidence_score = results['confidence']
        scan.spread_ratio = results['spread_ratio']
        scan.severity_level = ScanService.calculate_severity_level(results['spread_ratio'])
        scan.slice_predictions = results.get('slice_predictions')
        scan.affected_regions = results.get('affected_regions')
        scan.heatmap_path = results.get('heatmap_path')
        scan.status = ScanStatus.COMPLETED
        scan.processed_at = datetime.utcnow()
        
        db.commit()
        
        # Create auto report
        report = ReportService.create_auto_report(db, scan, scan.uploaded_by)
        
        # Send notifications
        NotificationService.create_scan_complete_notification(db, scan, scan.uploaded_by)
        
        # Send WebSocket notification
        await connection_manager.send_scan_complete(
            scan.scan_id,
            scan.has_hemorrhage == 1,
            scan.uploaded_by
        )
        
        # If severe, alert doctors
        if scan.severity_level == SeverityLevel.SEVERE:
            from app.services.auth_service import AuthService
            doctors = AuthService.get_doctors(db)
            doctor_ids = [d.id for d in doctors]
            
            patient = db.query(Patient).filter(Patient.id == scan.patient_id).first()
            patient_name = patient.full_name if patient else "Unknown"
            
            await connection_manager.send_critical_alert(
                scan.scan_id,
                patient_name,
                scan.spread_ratio,
                doctor_ids
            )
            
            # Create critical notifications for all doctors
            for doctor in doctors:
                NotificationService.create_critical_alert(db, scan, doctor.id)
        
    except Exception as e:
        scan.status = ScanStatus.FAILED
        db.commit()
        print(f"Error processing scan: {e}")
    finally:
        db.close()


@router.post("/upload", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def upload_scan(
    background_tasks: BackgroundTasks,
    patient_id: int = Form(...),
    scan_type: str = Form("CT Head"),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_radiologist)
):
    """Upload a CT scan for analysis"""
    # Validate patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Validate file size and type
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Read and save file
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE // (1024*1024)}MB"
        )
    
    scan_id = ScanService.generate_scan_id()
    file_path = ScanService.save_uploaded_file(content, file.filename, scan_id)
    
    # Create scan record
    scan = Scan(
        scan_id=scan_id,
        patient_id=patient_id,
        uploaded_by=current_user.id,
        scan_type=scan_type,
        notes=notes,
        file_path=file_path,
        status=ScanStatus.PENDING
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    # Add background task for ML processing
    background_tasks.add_task(
        process_scan_background,
        scan.id,
        str(settings.DATABASE_URL)
    )
    
    return scan


@router.get("/", response_model=ScanListResponse)
async def get_scans(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[ScanStatus] = None,
    patient_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of scans with pagination"""
    scans, total = ScanService.get_scans(
        db,
        skip=(page - 1) * size,
        limit=size,
        status=status,
        patient_id=patient_id
    )
    
    return ScanListResponse(
        scans=scans,
        total=total,
        page=page,
        size=size
    )


@router.get("/recent")
async def get_recent_scans(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get recent scans"""
    scans = ScanService.get_recent_scans(db, limit=limit)
    return scans


@router.get("/critical")
async def get_critical_scans(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get critical (severe) scans"""
    scans = ScanService.get_critical_scans(db, limit=limit)
    return scans


@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get scan details"""
    scan = ScanService.get_scan_by_id(db, scan_id)
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    # Add related info
    response = ScanDetailResponse.model_validate(scan)
    response.patient_name = scan.patient.full_name if scan.patient else None
    response.patient_hospital_id = scan.patient.patient_id if scan.patient else None
    response.uploader_name = scan.uploaded_by_user.full_name if scan.uploaded_by_user else None
    response.severity_text = scan.severity_text
    
    return response


@router.get("/{scan_id}/viewer", response_model=SliceViewerData)
async def get_scan_viewer_data(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get data for CT slice viewer"""
    scan = ScanService.get_scan_by_id(db, scan_id)
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    # Get slice URLs (simplified - in real app, would extract from DICOM)
    scan_dir = os.path.dirname(scan.file_path)
    slice_urls = []
    heatmap_urls = []
    
    # Check for processed slices
    slices_dir = os.path.join(scan_dir, "slices")
    if os.path.exists(slices_dir):
        for filename in sorted(os.listdir(slices_dir)):
            if filename.endswith(('.png', '.jpg')):
                slice_urls.append(f"/uploads/scans/{scan.scan_id}/slices/{filename}")
    else:
        # Return original file URL
        slice_urls.append(f"/uploads/scans/{scan.scan_id}/original{os.path.splitext(scan.file_path)[1]}")
    
    # Check for heatmaps
    heatmaps_dir = os.path.join(scan_dir, "heatmaps")
    if os.path.exists(heatmaps_dir):
        for filename in sorted(os.listdir(heatmaps_dir)):
            if filename.endswith(('.png', '.jpg')):
                heatmap_urls.append(f"/uploads/scans/{scan.scan_id}/heatmaps/{filename}")
    
    return SliceViewerData(
        scan_id=scan.scan_id,
        total_slices=len(slice_urls),
        slice_urls=slice_urls,
        heatmap_urls=heatmap_urls if heatmap_urls else None,
        annotations=scan.slice_predictions
    )


@router.post("/{scan_id}/reprocess")
async def reprocess_scan(
    scan_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_radiologist)
):
    """Reprocess a scan with ML model"""
    scan = ScanService.get_scan_by_id(db, scan_id)
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    # Reset status
    scan.status = ScanStatus.PENDING
    db.commit()
    
    # Add background task
    background_tasks.add_task(
        process_scan_background,
        scan.id,
        str(settings.DATABASE_URL)
    )
    
    return {"message": "Scan queued for reprocessing"}


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_radiologist)
):
    """Delete a scan"""
    scan = ScanService.get_scan_by_id(db, scan_id)
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    # Check if scan has a report
    if scan.report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete scan with associated report"
        )
    
    success = ScanService.delete_scan(db, scan)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete scan"
        )


from datetime import datetime
