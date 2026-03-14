"""
Scan Service - Handle CT scan uploads and analysis
"""
import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
import numpy as np

from app.config import settings
from app.models.scan import Scan, ScanStatus, HemorrhageType, SeverityLevel
from app.models.patient import Patient
from app.schemas.scan import ScanCreate, ScanAnalysisResult


class ScanService:
    """Service for CT scan operations"""
    
    @staticmethod
    def generate_scan_id() -> str:
        """Generate unique scan ID"""
        return f"SCN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    @staticmethod
    def save_uploaded_file(file_content: bytes, original_filename: str, scan_id: str) -> str:
        """Save uploaded file and return path"""
        # Create directory for this scan
        scan_dir = os.path.join(settings.UPLOAD_DIR, "scans", scan_id)
        os.makedirs(scan_dir, exist_ok=True)
        
        # Get file extension
        ext = os.path.splitext(original_filename)[1].lower()
        file_path = os.path.join(scan_dir, f"original{ext}")
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return file_path
    
    @staticmethod
    def create_scan(
        db: Session,
        scan_data: ScanCreate,
        file_path: str,
        uploaded_by: int
    ) -> Scan:
        """Create a new scan record"""
        scan_id = ScanService.generate_scan_id()
        
        scan = Scan(
            scan_id=scan_id,
            patient_id=scan_data.patient_id,
            uploaded_by=uploaded_by,
            scan_type=scan_data.scan_type,
            notes=scan_data.notes,
            file_path=file_path,
            status=ScanStatus.PENDING
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return scan
    
    @staticmethod
    def get_scan_by_id(db: Session, scan_id: int) -> Optional[Scan]:
        """Get scan by database ID"""
        return db.query(Scan).filter(Scan.id == scan_id).first()
    
    @staticmethod
    def get_scan_by_scan_id(db: Session, scan_id: str) -> Optional[Scan]:
        """Get scan by scan ID string"""
        return db.query(Scan).filter(Scan.scan_id == scan_id).first()
    
    @staticmethod
    def get_scans(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[ScanStatus] = None,
        patient_id: Optional[int] = None
    ) -> Tuple[List[Scan], int]:
        """Get list of scans with pagination"""
        query = db.query(Scan)
        
        if status:
            query = query.filter(Scan.status == status)
        if patient_id:
            query = query.filter(Scan.patient_id == patient_id)
        
        total = query.count()
        scans = query.order_by(Scan.created_at.desc()).offset(skip).limit(limit).all()
        
        return scans, total
    
    @staticmethod
    def get_pending_scans(db: Session) -> List[Scan]:
        """Get all pending scans for processing"""
        return db.query(Scan).filter(Scan.status == ScanStatus.PENDING).all()
    
    @staticmethod
    def update_scan_status(db: Session, scan: Scan, status: ScanStatus) -> Scan:
        """Update scan status"""
        scan.status = status
        if status == ScanStatus.COMPLETED:
            scan.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(scan)
        return scan
    
    @staticmethod
    def update_scan_results(db: Session, scan: Scan, results: ScanAnalysisResult) -> Scan:
        """Update scan with analysis results"""
        scan.has_hemorrhage = 1 if results.has_hemorrhage else 0
        scan.hemorrhage_type = results.hemorrhage_type
        scan.confidence_score = results.confidence_score
        scan.spread_ratio = results.spread_ratio
        scan.severity_level = results.severity_level
        scan.slice_predictions = results.slice_predictions
        scan.affected_regions = results.affected_regions
        scan.heatmap_path = results.heatmap_path
        scan.status = ScanStatus.COMPLETED
        scan.processed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(scan)
        return scan
    
    @staticmethod
    def calculate_severity_level(spread_ratio: float) -> SeverityLevel:
        """Calculate severity level from spread ratio"""
        if spread_ratio < settings.SEVERITY_THRESHOLD_MILD * 100:
            return SeverityLevel.MILD
        elif spread_ratio < settings.SEVERITY_THRESHOLD_MODERATE * 100:
            return SeverityLevel.MODERATE
        else:
            return SeverityLevel.SEVERE
    
    @staticmethod
    def get_recent_scans(
        db: Session,
        user_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Scan]:
        """Get recent scans, optionally filtered by uploader"""
        query = db.query(Scan)
        if user_id:
            query = query.filter(Scan.uploaded_by == user_id)
        return query.order_by(Scan.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_critical_scans(db: Session, limit: int = 10) -> List[Scan]:
        """Get recent critical (severe) scans"""
        return db.query(Scan).filter(
            Scan.severity_level == SeverityLevel.SEVERE,
            Scan.status == ScanStatus.COMPLETED
        ).order_by(Scan.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_scan_statistics(db: Session) -> dict:
        """Get scan statistics for dashboard"""
        total = db.query(Scan).count()
        pending = db.query(Scan).filter(Scan.status == ScanStatus.PENDING).count()
        completed = db.query(Scan).filter(Scan.status == ScanStatus.COMPLETED).count()
        hemorrhage_positive = db.query(Scan).filter(Scan.has_hemorrhage == 1).count()
        severe_cases = db.query(Scan).filter(Scan.severity_level == SeverityLevel.SEVERE).count()
        
        return {
            "total_scans": total,
            "pending_scans": pending,
            "completed_scans": completed,
            "hemorrhage_detected": hemorrhage_positive,
            "severe_cases": severe_cases,
            "detection_rate": (hemorrhage_positive / completed * 100) if completed > 0 else 0
        }
    
    @staticmethod
    def delete_scan(db: Session, scan: Scan) -> bool:
        """Delete a scan and its files"""
        try:
            # Delete scan directory
            scan_dir = os.path.dirname(scan.file_path)
            if os.path.exists(scan_dir):
                shutil.rmtree(scan_dir)
            
            # Delete from database
            db.delete(scan)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
