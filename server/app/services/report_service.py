from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..db.orm import AuditEvent, Report
from ..schemas.reports import SearchAttributes
from .investigation_ai import InvestigationAI


DEMO_CACHED_EXTRACTION = {
    "time_window_start": "2026-07-17T17:09:00+07:00",
    "time_window_end": "2026-07-17T17:11:59+07:00",
    "location": "",
    "upper_clothing": "grey jacket",
    "lower_clothing": "",
    "accessories": ["black backpack"],
    "direction": "toward Exit D",
    "event": "running",
}


def _demo_extraction_for(report: Report) -> dict | None:
    text = report.description.casefold()
    required_terms = (
        ("abu-abu", "grey"),
        ("tas hitam", "black backpack"),
        ("exit d", "pintu d"),
        ("lari", "running"),
    )
    if all(any(term in text for term in alternatives) for alternatives in required_terms):
        return DEMO_CACHED_EXTRACTION
    return None


class ReportService:
    def __init__(
        self,
        db: Session,
        ai: InvestigationAI | None = None,
        cached_extraction: dict | None = None,
    ):
        self.db = db
        self.ai = ai if ai is not None else InvestigationAI()
        self.cached_extraction = cached_extraction

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
        self.db.flush()
        self._audit("report", report.report_id, "created")
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_report(self, report_id: str) -> Optional[Report]:
        return self.db.query(Report).filter(Report.report_id == report_id).first()

    def extract_attributes(self, report_id: str) -> Optional[dict]:
        report = self.get_report(report_id)
        if not report:
            return None
        cached = (
            self.cached_extraction
            if self.cached_extraction is not None
            else _demo_extraction_for(report)
        )
        attributes, source = self.ai.extract_report(report, cached)
        persisted = {
            **attributes.model_dump(mode="json"),
            "extraction_source": source,
        }
        report.attributes = persisted
        report.status = "attributes_extracted"
        self._audit(
            "report",
            report_id,
            "attributes_extracted",
            {"source": source},
        )
        self.db.commit()
        return persisted

    def update_attributes(self, report_id: str, attributes: dict) -> Optional[Report]:
        report = self.get_report(report_id)
        if not report:
            return None
        validated = SearchAttributes.model_validate(attributes).model_dump(mode="json")
        source = (report.attributes or {}).get("extraction_source")
        report.attributes = {
            **validated,
            **({"extraction_source": source} if source else {}),
        }
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
            timestamp=datetime.datetime.now(datetime.UTC),
        ))
