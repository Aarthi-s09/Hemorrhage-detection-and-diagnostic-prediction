"""
Dashboard API Routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func

from app.database import get_db
from app.models.scan import Scan, ScanStatus, SeverityLevel
from app.models.report import Report, ReportStatus
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.services.scan_service import ScanService
from app.services.report_service import ReportService
from app.utils.security import get_current_active_user


router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get dashboard statistics"""
    scan_stats = ScanService.get_scan_statistics(db)
    report_stats = ReportService.get_report_statistics(db, current_user.id)
    
    # Get patient count
    patient_count = db.query(Patient).count()
    
    # Get today's scans
    today = datetime.utcnow().date()
    todays_scans = db.query(Scan).filter(
        func.date(Scan.created_at) == today
    ).count()
    
    return {
        "scans": scan_stats,
        "reports": report_stats,
        "patients": {
            "total": patient_count
        },
        "today": {
            "scans_uploaded": todays_scans
        }
    }


@router.get("/radiologist")
async def get_radiologist_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get radiologist-specific dashboard data"""
    # Pending scans for review
    pending_scans = db.query(Scan).filter(
        Scan.status == ScanStatus.COMPLETED,
        Scan.uploaded_by == current_user.id
    ).order_by(Scan.created_at.desc()).limit(10).all()
    
    # Reports pending verification
    pending_reports = db.query(Report).filter(
        Report.created_by == current_user.id,
        Report.status == ReportStatus.PENDING_REVIEW
    ).order_by(Report.created_at.desc()).limit(10).all()
    
    # Critical cases
    critical_scans = db.query(Scan).filter(
        Scan.severity_level == SeverityLevel.SEVERE,
        Scan.status == ScanStatus.COMPLETED
    ).order_by(Scan.created_at.desc()).limit(5).all()
    
    # Weekly statistics
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_scans = db.query(Scan).filter(
        Scan.uploaded_by == current_user.id,
        Scan.created_at >= week_ago
    ).count()
    
    weekly_reports = db.query(Report).filter(
        Report.created_by == current_user.id,
        Report.created_at >= week_ago
    ).count()
    
    return {
        "pending_scans": [
            {
                "id": s.id,
                "scan_id": s.scan_id,
                "patient_name": s.patient.full_name if s.patient else "Unknown",
                "has_hemorrhage": s.has_hemorrhage == 1,
                "severity": s.severity_level.value if s.severity_level else None,
                "created_at": s.created_at.isoformat()
            } for s in pending_scans
        ],
        "pending_reports": [
            {
                "id": r.id,
                "report_id": r.report_id,
                "title": r.title,
                "is_critical": r.is_critical,
                "created_at": r.created_at.isoformat()
            } for r in pending_reports
        ],
        "critical_cases": [
            {
                "id": s.id,
                "scan_id": s.scan_id,
                "patient_name": s.patient.full_name if s.patient else "Unknown",
                "spread_ratio": s.spread_ratio,
                "created_at": s.created_at.isoformat()
            } for s in critical_scans
        ],
        "weekly_stats": {
            "scans_uploaded": weekly_scans,
            "reports_created": weekly_reports
        }
    }


@router.get("/doctor")
async def get_doctor_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get doctor-specific dashboard data"""
    # Reports assigned to this doctor
    assigned_reports = db.query(Report).filter(
        Report.doctor_id == current_user.id
    ).order_by(Report.created_at.desc()).limit(20).all()
    
    # Unacknowledged reports
    unacknowledged = [r for r in assigned_reports if r.status == ReportStatus.SENT]
    
    # Critical reports
    critical_reports = [r for r in assigned_reports if r.is_critical and r.status != ReportStatus.ACKNOWLEDGED]
    
    # Weekly received
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_received = db.query(Report).filter(
        Report.doctor_id == current_user.id,
        Report.sent_at >= week_ago
    ).count()
    
    return {
        "unacknowledged_reports": [
            {
                "id": r.id,
                "report_id": r.report_id,
                "title": r.title,
                "severity_score": r.severity_score,
                "is_critical": r.is_critical,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None
            } for r in unacknowledged
        ],
        "critical_alerts": [
            {
                "id": r.id,
                "report_id": r.report_id,
                "title": r.title,
                "severity_score": r.severity_score,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None
            } for r in critical_reports
        ],
        "recent_reports": [
            {
                "id": r.id,
                "report_id": r.report_id,
                "title": r.title,
                "status": r.status.value,
                "is_critical": r.is_critical,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None
            } for r in assigned_reports[:10]
        ],
        "stats": {
            "total_assigned": len(assigned_reports),
            "pending_review": len(unacknowledged),
            "critical_pending": len(critical_reports),
            "weekly_received": weekly_received
        }
    }


@router.get("/severity-distribution")
async def get_severity_distribution(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get severity distribution for charts"""
    since = datetime.utcnow() - timedelta(days=days)
    
    # Count by severity level
    scans = db.query(Scan).filter(
        Scan.status == ScanStatus.COMPLETED,
        Scan.created_at >= since
    ).all()
    
    distribution = {
        "none": 0,
        "mild": 0,
        "moderate": 0,
        "severe": 0
    }
    
    for scan in scans:
        if scan.severity_level:
            distribution[scan.severity_level.value] += 1
    
    return distribution


@router.get("/trend")
async def get_scan_trend(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get scan trend data for charts"""
    trend_data = []
    
    for i in range(days):
        date = datetime.utcnow().date() - timedelta(days=i)
        
        total = db.query(Scan).filter(
            func.date(Scan.created_at) == date
        ).count()
        
        positive = db.query(Scan).filter(
            func.date(Scan.created_at) == date,
            Scan.has_hemorrhage == 1
        ).count()
        
        trend_data.append({
            "date": date.isoformat(),
            "total_scans": total,
            "positive_cases": positive
        })
    
    # Reverse to show oldest first
    trend_data.reverse()
    
    return trend_data
