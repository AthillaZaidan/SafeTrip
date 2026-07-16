from __future__ import annotations

import datetime, random
from typing import Optional

from sqlalchemy.orm import Session

from ..db.orm import (
    AuditEvent,
    CandidateClip,
    Investigation,
    InvestigationTimelineEntry,
    Report,
)


class InvestigationService:
    def __init__(self, db: Session):
        self.db = db

    def create_investigation(self, report_id: str) -> Optional[Investigation]:
        report = self.db.query(Report).filter(Report.report_id == report_id).first()
        if not report:
            return None
        investigation = Investigation(
            report_id=report.id,
            search_filters=report.attributes or {},
            status="searching",
        )
        self.db.add(investigation)
        self.db.flush()
        self._generate_candidates(investigation, report)
        report.status = "investigating"
        self._audit("investigation", investigation.investigation_id, "created")
        self.db.commit()
        return investigation

    def get_investigation(self, investigation_id: str) -> Optional[Investigation]:
        return self.db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()

    def list_candidates(self, investigation_id: str) -> list[CandidateClip]:
        inv = self.get_investigation(investigation_id)
        if not inv:
            return []
        return self.db.query(CandidateClip).filter(CandidateClip.investigation_id == inv.id).all()

    def update_candidate(self, investigation_id: str, candidate_id: str, verification_status: str) -> Optional[CandidateClip]:
        candidate = self.db.query(CandidateClip).filter(CandidateClip.candidate_id == candidate_id).first()
        if not candidate:
            return None
        candidate.verification_status = verification_status
        if verification_status == "confirmed":
            self.db.add(InvestigationTimelineEntry(
                investigation_id=candidate.investigation_id,
                candidate_id=candidate.id,
                timestamp=candidate.timestamp or datetime.datetime.utcnow(),
                camera_id=candidate.camera_id,
                note=f"Candidate {candidate_id} confirmed",
                sort_order=candidate.score * 100,
            ))
            candidate.investigation.status = "in_progress"
        self._audit("candidate", candidate_id, verification_status)
        self.db.commit()
        return candidate

    def get_timeline(self, investigation_id: str) -> list[InvestigationTimelineEntry]:
        inv = self.get_investigation(investigation_id)
        if not inv:
            return []
        return (
            self.db.query(InvestigationTimelineEntry)
            .filter(InvestigationTimelineEntry.investigation_id == inv.id)
            .order_by(InvestigationTimelineEntry.timestamp.asc())
            .all()
        )

    def _generate_candidates(self, investigation: Investigation, report: Report):
        locations = ["Platform B", "Concourse A", "Gate 5", "Exit 2", "Platform B - South"]
        cameras = ["CAM_PLATFORM_B_01", "CAM_PLATFORM_B_01", "CAM_CONCOURSE_A_01"]
        explanations = [
            "Subject matches upper clothing description: grey jacket visible from frame 45-120.",
            "Movement pattern aligns with reported direction toward Exit 2.",
            "Timing matches reported window at 17:10, person visible crossing platform.",
            "Backpack accessory detected, matching report description.",
            "Close interaction observed near Platform B at 17:08.",
        ]
        for i in range(5):
            self.db.add(CandidateClip(
                investigation_id=investigation.id,
                score=round(random.uniform(0.65, 0.95), 3),
                explanation=explanations[i],
                url=f"evidence/clips/{report.report_id}/candidate_{i+1}.mp4",
                snapshot_url=f"evidence/snapshots/{report.report_id}/candidate_{i+1}.jpg",
                camera_id=random.choice(cameras),
                timestamp=report.time_window_start or datetime.datetime.utcnow(),
                verification_status="pending",
            ))
        self.db.flush()
        investigation.status = "awaiting_review"

    def _audit(self, entity_type: str, entity_id: str, action: str, details: dict = None):
        self.db.add(AuditEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details=details or {},
            timestamp=datetime.datetime.utcnow(),
        ))
