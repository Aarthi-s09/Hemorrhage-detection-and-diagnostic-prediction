"""
Report Service - Handle report generation and management
"""
import os
import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.config import settings
from app.models.report import Report, ReportStatus
from app.models.scan import Scan
from app.schemas.report import ReportCreate, ReportUpdate


class ReportService:
    """Service for report operations"""
    
    @staticmethod
    def generate_report_id() -> str:
        """Generate unique report ID"""
        return f"RPT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    @staticmethod
    def generate_findings(scan: Scan) -> str:
        """Generate AI findings text from scan results - Simple and neat template"""
        
        template = f"""
╔══════════════════════════════════════════════════════════════════╗
║              CT BRAIN HEMORRHAGE ANALYSIS REPORT                 ║
╚══════════════════════════════════════════════════════════════════╝

SCAN ID: {scan.scan_id}
DATE: {scan.created_at.strftime('%Y-%m-%d %H:%M')}

───────────────────────────────────────────────────────────────────

ANALYSIS RESULT: {'POSITIVE' if scan.has_hemorrhage else 'NEGATIVE'}

"""
        
        if scan.has_hemorrhage:
            template += f"""HEMORRHAGE DETECTED ⚠️

Type: {scan.hemorrhage_type.value.replace('_', ' ').title()}
Spread Ratio: {scan.spread_ratio:.1f}%
Severity Level: {scan.severity_level.value.upper()}
Confidence: {scan.confidence_score * 100:.1f}%
"""
            
            if scan.affected_regions:
                regions = ', '.join([r.title() for r in scan.affected_regions])
                template += f"\nAffected Regions: {regions}"
            
            template += "\n\n───────────────────────────────────────────────────────────────────\n\n"
            
            if scan.spread_ratio >= 70:
                template += "STATUS: CRITICAL\n"
                template += "⚠️ Immediate medical attention required\n"
                template += "Emergency neurosurgical consultation indicated\n"
            elif scan.spread_ratio >= 30:
                template += "STATUS: MODERATE\n"
                template += "Close monitoring and neurology consultation required\n"
            else:
                template += "STATUS: MILD\n"
                template += "Routine follow-up recommended\n"
                
            template += "\nClinical correlation is advised."
            
        else:
            template += f"""NO HEMORRHAGE DETECTED ✓

Brain parenchyma: Normal
Intracranial abnormality: None identified
Confidence: {scan.confidence_score * 100:.1f}%

───────────────────────────────────────────────────────────────────

STATUS: NORMAL
No immediate intervention required.
"""
        
        return template
    
    @staticmethod
    def generate_recommendations(scan: Scan) -> str:
        """Generate recommendations based on scan results - Simple and clear"""
        
        if not scan.has_hemorrhage:
            return """CLINICAL RECOMMENDATIONS:

• Continue standard care protocol
• No immediate intervention required
• Routine follow-up as needed"""
        
        if scan.spread_ratio >= 70:
            return """URGENT CLINICAL RECOMMENDATIONS:

Priority: IMMEDIATE ACTION REQUIRED

1. Immediate neurosurgical consultation
2. Consider emergent surgical intervention
3. Close neurological monitoring (continuous)
4. Serial CT follow-up in 6-12 hours
5. Strict blood pressure control
6. ICU admission strongly recommended
7. Notify attending physician immediately"""
            
        elif scan.spread_ratio >= 30:
            return """CLINICAL RECOMMENDATIONS:

Priority: TIMELY INTERVENTION

1. Neurology consultation within 24 hours
2. Close neurological monitoring
3. Repeat CT scan in 24-48 hours
4. Blood pressure monitoring and management
5. Review anticoagulation status
6. Consider admission for observation"""
            
        else:
            return """CLINICAL RECOMMENDATIONS:

Priority: ROUTINE FOLLOW-UP

1. Outpatient neurology consultation
2. Repeat CT scan in 1 week
3. Monitor for symptoms (headache, confusion, weakness)
4. Patient education on warning signs
5. Activity restrictions as per clinical judgment"""
    
    @staticmethod
    def create_report(db: Session, report_data: ReportCreate, created_by: int) -> Report:
        """Create a new report"""
        report_id = ReportService.generate_report_id()
        
        # Get scan for severity
        scan = db.query(Scan).filter(Scan.id == report_data.scan_id).first()
        
        report = Report(
            report_id=report_id,
            scan_id=report_data.scan_id,
            created_by=created_by,
            doctor_id=report_data.doctor_id,
            title=report_data.title,
            findings=report_data.findings,
            radiologist_notes=report_data.radiologist_notes,
            recommendations=report_data.recommendations,
            conclusion=report_data.conclusion,
            severity_score=scan.spread_ratio if scan else None,
            is_critical=scan.spread_ratio >= 70 if scan and scan.spread_ratio else False,
            status=ReportStatus.DRAFT
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def create_auto_report(db: Session, scan: Scan, created_by: int) -> Report:
        """Create an automatic report from scan results"""
        report_id = ReportService.generate_report_id()
        
        findings = ReportService.generate_findings(scan)
        recommendations = ReportService.generate_recommendations(scan)
        
        conclusion = "Hemorrhage detected - clinical correlation required." if scan.has_hemorrhage else "No acute findings."
        
        report = Report(
            report_id=report_id,
            scan_id=scan.id,
            patient_id=scan.patient_id,  # Add patient_id from scan
            created_by=created_by,
            title=f"CT Brain Analysis - {scan.scan_id}",
            findings=findings,
            recommendations=recommendations,
            conclusion=conclusion,
            severity_score=scan.spread_ratio,
            is_critical=scan.spread_ratio >= 70 if scan.spread_ratio else False,
            status=ReportStatus.PENDING_REVIEW
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def get_report_by_id(db: Session, report_id: int) -> Optional[Report]:
        """Get report by database ID"""
        return db.query(Report).filter(Report.id == report_id).first()
    
    @staticmethod
    def get_report_by_report_id(db: Session, report_id: str) -> Optional[Report]:
        """Get report by report ID string"""
        return db.query(Report).filter(Report.report_id == report_id).first()
    
    @staticmethod
    def get_report_by_scan(db: Session, scan_id: int) -> Optional[Report]:
        """Get report for a specific scan"""
        return db.query(Report).filter(Report.scan_id == scan_id).first()
    
    @staticmethod
    def get_reports(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[ReportStatus] = None,
        doctor_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Tuple[List[Report], int]:
        """Get list of reports with pagination"""
        query = db.query(Report)
        
        if status:
            query = query.filter(Report.status == status)
        if doctor_id:
            query = query.filter(Report.doctor_id == doctor_id)
        if created_by:
            query = query.filter(Report.created_by == created_by)
        
        total = query.count()
        reports = query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
        
        return reports, total
    
    @staticmethod
    def update_report(db: Session, report: Report, update_data: ReportUpdate) -> Report:
        """Update report"""
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(report, field, value)
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def verify_report(db: Session, report: Report, notes: Optional[str] = None) -> Report:
        """Mark report as verified by radiologist"""
        report.is_verified = True
        report.verified_at = datetime.utcnow()
        report.status = ReportStatus.REVIEWED
        if notes:
            report.radiologist_notes = notes
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def send_report(db: Session, report: Report, doctor_id: int) -> Report:
        """Send report to doctor"""
        report.doctor_id = doctor_id
        report.status = ReportStatus.SENT
        report.sent_at = datetime.utcnow()
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def acknowledge_report(db: Session, report: Report) -> Report:
        """Mark report as acknowledged by doctor"""
        report.status = ReportStatus.ACKNOWLEDGED
        report.acknowledged_at = datetime.utcnow()
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def set_pdf_path(db: Session, report: Report, pdf_path: str) -> Report:
        """Set PDF path for report"""
        report.pdf_path = pdf_path
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def get_report_statistics(db: Session, user_id: Optional[int] = None) -> dict:
        """Get report statistics"""
        query = db.query(Report)
        if user_id:
            query = query.filter(
                (Report.created_by == user_id) | (Report.doctor_id == user_id)
            )
        
        total = query.count()
        pending = query.filter(Report.status == ReportStatus.PENDING_REVIEW).count()
        sent = query.filter(Report.status == ReportStatus.SENT).count()
        acknowledged = query.filter(Report.status == ReportStatus.ACKNOWLEDGED).count()
        critical = query.filter(Report.is_critical == True).count()
        
        return {
            "total_reports": total,
            "pending_review": pending,
            "sent_to_doctors": sent,
            "acknowledged": acknowledged,
            "critical_cases": critical
        }
