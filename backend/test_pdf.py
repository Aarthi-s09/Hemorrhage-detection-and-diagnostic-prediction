#!/usr/bin/env python
"""Test PDF generation"""
from app.database import SessionLocal
from app.models.report import Report
from app.models.scan import Scan
from app.models.patient import Patient
from app.utils.pdf_generator import PDFGenerator

db = SessionLocal()

# Get report 1
report = db.query(Report).filter(Report.id == 1).first()
if not report:
    print("❌ Report not found")
    db.close()
    exit(1)

print(f"✅ Found report: {report.report_id}")

# Get scan
scan = report.scan
if not scan:
    print("❌ Scan not found")
    db.close()
    exit(1)

print(f"✅ Found scan: {scan.scan_id}")

# Get patient
patient = scan.patient if scan else None
if not patient:
    print("❌ Patient not found")
    db.close()
    exit(1)

print(f"✅ Found patient: {patient.full_name}")

# Try to generate PDF
try:
    pdf_gen = PDFGenerator()
    pdf_path = pdf_gen.generate_report_pdf(report, scan, patient)
    print(f"✅ PDF generated successfully: {pdf_path}")
except Exception as e:
    print(f"❌ Error generating PDF: {e}")
    import traceback
    traceback.print_exc()

db.close()
