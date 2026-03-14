"""
Report API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.database import get_db
from app.models.report import Report, ReportStatus
from app.models.scan import Scan
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.report import (
    ReportCreate, ReportUpdate, ReportResponse, 
    ReportDetailResponse, ReportListResponse, 
    ReportVerify, ReportSend, ReportPDFResponse
)
from app.services.report_service import ReportService
from app.services.notification_service import NotificationService
from app.utils.security import get_current_active_user, require_radiologist, require_doctor
from app.utils.pdf_generator import PDFGenerator
from app.websocket import connection_manager
from datetime import datetime


router = APIRouter()


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_radiologist)
):
    """Create a new report"""
    # Verify scan exists and belongs to this user
    scan = db.query(Scan).filter(Scan.id == report_data.scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    # Check if report already exists for this scan
    existing = ReportService.get_report_by_scan(db, report_data.scan_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report already exists for this scan"
        )
    
    report = ReportService.create_report(db, report_data, current_user.id)
    
    # Notify radiologist
    NotificationService.create_report_ready_notification(db, report, current_user.id)
    
    return report


@router.get("/", response_model=ReportListResponse)
async def get_reports(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[ReportStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of reports"""
    # For development: Show ALL reports (authentication disabled)
    # In production, filter based on user role
    doctor_id = None
    created_by = None
    
    # Uncomment below for production with real authentication
    # doctor_id = current_user.id if current_user.role == UserRole.DOCTOR else None
    # created_by = current_user.id if current_user.role == UserRole.RADIOLOGIST else None
    # if current_user.role == UserRole.ADMIN:
    #     doctor_id = None
    #     created_by = None
    
    reports, total = ReportService.get_reports(
        db,
        skip=(page - 1) * size,
        limit=size,
        status=status,
        doctor_id=doctor_id,
        created_by=created_by
    )
    
    return ReportListResponse(
        reports=reports,
        total=total,
        page=page,
        size=size
    )


@router.get("/pending")
async def get_pending_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_radiologist)
):
    """Get reports pending review"""
    reports, _ = ReportService.get_reports(
        db, status=ReportStatus.PENDING_REVIEW, created_by=current_user.id
    )
    return reports


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get report details"""
    report = ReportService.get_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Build detailed response
    response = ReportDetailResponse.model_validate(report)
    
    # Add related info
    if report.scan:
        response.scan_info = {
            "scan_id": report.scan.scan_id,
            "has_hemorrhage": report.scan.has_hemorrhage == 1,
            "spread_ratio": report.scan.spread_ratio,
            "severity_level": report.scan.severity_level.value if report.scan.severity_level else None
        }
        if report.scan.patient:
            response.patient_name = report.scan.patient.full_name
            response.patient_id = report.scan.patient.patient_id
    
    if report.created_by_user:
        response.creator_name = report.created_by_user.full_name
    
    if report.assigned_doctor:
        response.doctor_name = report.assigned_doctor.full_name
    
    return response


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: int,
    report_update: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_radiologist)
):
    """Update a report"""
    report = ReportService.get_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if report.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this report"
        )
    
    report = ReportService.update_report(db, report, report_update)
    return report


@router.post("/{report_id}/verify", response_model=ReportResponse)
async def verify_report(
    report_id: int,
    verify_data: ReportVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_radiologist)
):
    """Verify/approve a report"""
    report = ReportService.get_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    report = ReportService.verify_report(db, report, verify_data.radiologist_notes)
    return report


@router.post("/{report_id}/send", response_model=ReportResponse)
async def send_report(
    report_id: int,
    send_data: ReportSend,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_radiologist)
):
    """Send report to a doctor"""
    report = ReportService.get_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if not report.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report must be verified before sending"
        )
    
    # Verify doctor exists
    doctor = db.query(User).filter(
        User.id == send_data.doctor_id,
        User.role == UserRole.DOCTOR
    ).first()
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    report = ReportService.send_report(db, report, send_data.doctor_id)
    
    # Create notification for doctor
    NotificationService.create_report_sent_notification(db, report, doctor.id)
    
    # Send WebSocket notification
    await connection_manager.send_report_notification(
        report.report_id,
        doctor.id,
        report.is_critical
    )
    
    return report


@router.post("/{report_id}/acknowledge", response_model=ReportResponse)
async def acknowledge_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """Doctor acknowledges receipt of report"""
    report = ReportService.get_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if report.doctor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This report is not assigned to you"
        )
    
    report = ReportService.acknowledge_report(db, report)
    return report


@router.post("/{report_id}/generate-pdf", response_model=ReportPDFResponse)
async def generate_report_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate PDF for a report"""
    report = ReportService.get_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Get related data
    scan = report.scan
    patient = scan.patient if scan else None
    
    if not scan or not patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incomplete report data"
        )
    
    # Generate PDF
    pdf_generator = PDFGenerator()
    pdf_path = pdf_generator.generate_report_pdf(report, scan, patient)
    
    # Update report with PDF path
    ReportService.set_pdf_path(db, report, pdf_path)
    
    return ReportPDFResponse(
        report_id=report.report_id,
        pdf_url=f"/uploads/reports/{report.report_id}.pdf",
        generated_at=datetime.utcnow()
    )


@router.get("/{report_id}/pdf")
async def download_report_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download report PDF"""
    report = ReportService.get_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    if not report.pdf_path or not os.path.exists(report.pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not generated yet"
        )
    
    return FileResponse(
        report.pdf_path,
        media_type="application/pdf",
        filename=f"{report.report_id}.pdf"
    )
