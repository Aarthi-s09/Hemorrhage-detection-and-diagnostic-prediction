"""
PDF Report Generator
"""
import os
from datetime import datetime
from typing import Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from app.config import settings
from app.models.report import Report
from app.models.scan import Scan
from app.models.patient import Patient


class PDFGenerator:
    """Generate PDF reports for hemorrhage detection results"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles - only add if they don't exist"""
        # Check and add styles only if they don't exist
        if 'ReportTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ReportTitle',
                parent=self.styles['Heading1'],
                fontSize=18,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#1a365d')
            ))
        
        if 'ReportSectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ReportSectionHeader',
                parent=self.styles['Heading2'],
                fontSize=14,
                spaceBefore=15,
                spaceAfter=10,
                textColor=colors.HexColor('#2d3748')
            ))
        
        if 'ReportBodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ReportBodyText',
                parent=self.styles['Normal'],
                fontSize=11,
                leading=16,
                alignment=TA_JUSTIFY,
                spaceAfter=10
            ))
        
        if 'ReportCritical' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ReportCritical',
                parent=self.styles['Normal'],
                fontSize=12,
                textColor=colors.red,
                fontName='Helvetica-Bold'
            ))
        
        if 'ReportInfo' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ReportInfo',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.gray
            ))
    
    def generate_report_pdf(
        self,
        report: Report,
        scan: Scan,
        patient: Patient,
        output_path: Optional[str] = None
    ) -> str:
        """Generate PDF report"""
        # Create output path if not provided
        if not output_path:
            reports_dir = os.path.join(settings.UPLOAD_DIR, "reports")
            os.makedirs(reports_dir, exist_ok=True)
            output_path = os.path.join(reports_dir, f"{report.report_id}.pdf")
        
        # Create document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build content
        content = []
        
        # Header
        content.append(Paragraph("HEMORRHAGE DETECTION SYSTEM", self.styles['ReportTitle']))
        content.append(Paragraph("CT Brain Analysis Report", self.styles['Heading2']))
        content.append(Spacer(1, 20))
        
        # Report ID and Date
        content.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=10
        ))
        
        report_info = [
            ['Report ID:', report.report_id, 'Scan ID:', scan.scan_id],
            ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M'), 'Scan Date:', scan.scan_date.strftime('%Y-%m-%d') if scan.scan_date else 'N/A']
        ]
        
        info_table = Table(report_info, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.gray),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        content.append(info_table)
        content.append(Spacer(1, 15))
        
        # Patient Information Section
        content.append(Paragraph("Patient Information", self.styles['ReportSectionHeader']))
        content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e0')))
        
        patient_data = [
            ['Patient ID:', patient.patient_id, 'Name:', patient.full_name],
            ['Date of Birth:', patient.date_of_birth.strftime('%Y-%m-%d'), 'Age:', f"{patient.age} years" if patient.age else 'N/A'],
            ['Gender:', patient.gender.value.title(), 'Contact:', patient.phone or 'N/A']
        ]
        
        patient_table = Table(patient_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
        patient_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.gray),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        content.append(patient_table)
        content.append(Spacer(1, 15))
        
        # Analysis Results Section
        content.append(Paragraph("Analysis Results", self.styles['ReportSectionHeader']))
        content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e0')))
        
        # Detection Status
        if scan.has_hemorrhage:
            severity_color = colors.red if scan.spread_ratio >= 70 else (colors.orange if scan.spread_ratio >= 30 else colors.green)
            status_text = f"HEMORRHAGE DETECTED - {scan.severity_level.value.upper()}"
        else:
            severity_color = colors.green
            status_text = "NO HEMORRHAGE DETECTED"
        
        detection_data = [
            ['Detection Status:', status_text],
            ['Hemorrhage Type:', scan.hemorrhage_type.value.replace('_', ' ').title() if scan.has_hemorrhage else 'N/A'],
            ['Confidence Score:', f"{scan.confidence_score * 100:.1f}%" if scan.confidence_score else 'N/A'],
            ['Spread Ratio:', f"{scan.spread_ratio:.1f}%" if scan.spread_ratio else '0%'],
            ['Severity Level:', scan.severity_level.value.upper() if scan.severity_level else 'N/A']
        ]
        
        detection_table = Table(detection_data, colWidths=[1.5*inch, 5*inch])
        detection_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),
            ('TEXTCOLOR', (1, 0), (1, 0), severity_color),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        content.append(detection_table)
        content.append(Spacer(1, 15))
        
        # Critical Alert if severe
        if scan.spread_ratio and scan.spread_ratio >= 70:
            content.append(Paragraph(
                "⚠️ CRITICAL ALERT: This case requires immediate medical attention!",
                self.styles['ReportCritical']
            ))
            content.append(Spacer(1, 10))
        
        # Findings Section
        content.append(Paragraph("Detailed Findings", self.styles['ReportSectionHeader']))
        content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e0')))
        
        findings_text = report.findings.replace('\n', '<br/>')
        content.append(Paragraph(findings_text, self.styles['ReportBodyText']))
        content.append(Spacer(1, 10))
        
        # Radiologist Notes
        if report.radiologist_notes:
            content.append(Paragraph("Radiologist Notes", self.styles['ReportSectionHeader']))
            content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e0')))
            content.append(Paragraph(report.radiologist_notes, self.styles['ReportBodyText']))
            content.append(Spacer(1, 10))
        
        # Recommendations
        if report.recommendations:
            content.append(Paragraph("Recommendations", self.styles['ReportSectionHeader']))
            content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e0')))
            recommendations_text = report.recommendations.replace('\n', '<br/>')
            content.append(Paragraph(recommendations_text, self.styles['ReportBodyText']))
            content.append(Spacer(1, 10))
        
        # Conclusion
        if report.conclusion:
            content.append(Paragraph("Conclusion", self.styles['ReportSectionHeader']))
            content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e0')))
            content.append(Paragraph(report.conclusion, self.styles['ReportBodyText']))
        
        # Footer
        content.append(Spacer(1, 30))
        content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
        content.append(Spacer(1, 10))
        
        footer_text = f"""
        Generated by Hemorrhage Detection System<br/>
        Report ID: {report.report_id} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
        This report is AI-assisted and should be verified by a qualified radiologist.
        """
        content.append(Paragraph(footer_text, self.styles['ReportInfo']))
        
        # Build PDF
        doc.build(content)
        
        return output_path
    
    def generate_summary_report(self, scans: list, output_path: str) -> str:
        """Generate summary report for multiple scans"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        content = []
        content.append(Paragraph("Hemorrhage Detection - Summary Report", self.styles['ReportTitle']))
        content.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['ReportInfo']))
        content.append(Spacer(1, 20))
        
        # Summary statistics
        total = len(scans)
        positive = sum(1 for s in scans if s.has_hemorrhage)
        severe = sum(1 for s in scans if s.spread_ratio and s.spread_ratio >= 70)
        
        summary_data = [
            ['Total Scans Analyzed:', str(total)],
            ['Hemorrhage Detected:', f"{positive} ({positive/total*100:.1f}%)" if total > 0 else '0'],
            ['Severe Cases:', str(severe)],
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        content.append(summary_table)
        content.append(Spacer(1, 20))
        
        # Detailed table
        table_data = [['Scan ID', 'Patient', 'Status', 'Severity', 'Spread %']]
        for scan in scans:
            table_data.append([
                scan.scan_id,
                scan.patient.full_name if scan.patient else 'N/A',
                'Positive' if scan.has_hemorrhage else 'Negative',
                scan.severity_level.value.upper() if scan.severity_level else 'N/A',
                f"{scan.spread_ratio:.1f}%" if scan.spread_ratio else '0%'
            ])
        
        detail_table = Table(table_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1*inch, 1*inch])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        content.append(detail_table)
        
        doc.build(content)
        return output_path
