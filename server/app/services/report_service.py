from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..db.orm import AuditEvent, Investigation, Report


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def create_report(self, data: dict) -> Report:
        report = Report(
            reporter_type=data.get("reporter_type", "passenger"),
            time_window_start=data.get("time_window_start"),
            time_window_end=data.get("time_window_end"),
            location=data.get("location", ""),
            description=data.get("description", ""),
            direction=data.get("direction", ""),
            image_url=data.get("image_url", ""),
            status="submitted",
        )
        self.db.add(report)
        self._audit("report", report.report_id, "created")
        self.db.commit()
        return report

    def get_report(self, report_id: str) -> Optional[Report]:
        return self.db.query(Report).filter(Report.report_id == report_id).first()

    def extract_attributes(self, report_id: str) -> Optional[dict]:
        report = self.get_report(report_id)
        if not report:
            return None
        attributes = {
            "time_window": "",
            "location": report.location,
            "event": report.description[:200],
            "direction": report.direction,
        }
        report.attributes = attributes
        report.status = "attributes_extracted"
        self._audit("report", report_id, "attributes_extracted")
        self.db.commit()
        return attributes

    def update_attributes(self, report_id: str, attributes: dict) -> Optional[Report]:
        report = self.get_report(report_id)
        if not report:
            return None
        report.attributes = attributes
        report.status = "attributes_confirmed"
        self._audit("report", report_id, "attributes_confirmed")
        self.db.commit()
        return report

    def list_reports(self) -> list[Report]:
        return self.db.query(Report).order_by(Report.created_at.desc()).all()

    def _audit(self, entity_type: str, entity_id: str, action: str, details: dict = None):
        self.db.add(AuditEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details=details or {},
            timestamp=datetime.datetime.utcnow(),
        ))
