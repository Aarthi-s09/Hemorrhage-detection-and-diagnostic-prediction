#!/usr/bin/env python
"""Check reports in database"""
from app.database import SessionLocal
from app.models.report import Report
from app.models.scan import Scan

db = SessionLocal()

# Check reports
reports = db.query(Report).all()
print(f"Total reports in database: {len(reports)}")
if reports:
    print("\nReports:")
    for r in reports:
        print(f"  - {r.report_id} (Scan: {r.scan_id}, Status: {r.status.value})")

# Check scans
scans = db.query(Scan).all()
print(f"\nTotal scans in database: {len(scans)}")
if scans:
    print("\nScans:")
    for s in scans:
        print(f"  - {s.scan_id} (Status: {s.status.value}, Has hemorrhage: {s.has_hemorrhage})")

# Check if scan 1 has a report
scan1 = db.query(Scan).filter(Scan.id == 1).first()
if scan1:
    report_for_scan1 = db.query(Report).filter(Report.scan_id == 1).first()
    print(f"\nScan 1 has report: {report_for_scan1 is not None}")

db.close()
