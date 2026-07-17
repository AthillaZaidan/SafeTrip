from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from ..db.orm import (
    AuditEvent,
    CandidateClip,
    Investigation,
    InvestigationTimelineEntry,
    Report,
)
from ..schemas.reports import SearchAttributes
from .clip_retrieval import load_clip_library, retrieve_candidates
from .investigation_ai import InvestigationAI


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LIBRARY_PATH = REPO_ROOT / "configs" / "investigation_library.json"


class ReportNotReadyError(ValueError):
    pass


class InvestigationService:
    def __init__(
        self,
        db: Session,
        ai: InvestigationAI | None = None,
        library_path: str | Path = DEFAULT_LIBRARY_PATH,
    ):
        self.db = db
        self.ai = ai if ai is not None else InvestigationAI()
        self.library_path = Path(library_path)

    def create_investigation(self, report_id: str) -> Optional[Investigation]:
        report = self.db.query(Report).filter(Report.report_id == report_id).first()
        if not report:
            return None
        if report.status != "attributes_confirmed":
            raise ReportNotReadyError("Report attributes must be confirmed first")
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

    def list_candidates(self, investigation_id: str) -> Optional[list[CandidateClip]]:
        inv = self.get_investigation(investigation_id)
        if not inv:
            return None
        return (
            self.db.query(CandidateClip)
            .filter(CandidateClip.investigation_id == inv.id)
            .order_by(CandidateClip.score.desc(), CandidateClip.clip_id.asc())
            .all()
        )

    def update_candidate(
        self,
        investigation_id: str,
        candidate_id: str,
        verification_status: str,
        note: str | None = None,
    ) -> Optional[CandidateClip]:
        investigation = self.get_investigation(investigation_id)
        if investigation is None:
            return None
        candidate = (
            self.db.query(CandidateClip)
            .filter(
                CandidateClip.investigation_id == investigation.id,
                CandidateClip.candidate_id == candidate_id,
            )
            .first()
        )
        if candidate is None:
            return None
        if verification_status not in {"confirmed", "rejected"}:
            raise ValueError("verification_status must be confirmed or rejected")

        candidate.verification_status = verification_status
        timeline_entry = (
            self.db.query(InvestigationTimelineEntry)
            .filter(InvestigationTimelineEntry.candidate_id == candidate.id)
            .first()
        )
        if verification_status == "confirmed":
            if timeline_entry is None:
                timeline_entry = InvestigationTimelineEntry(
                    investigation_id=candidate.investigation_id,
                    candidate_id=candidate.id,
                    timestamp=candidate.timestamp
                    or datetime.datetime.now(datetime.UTC),
                    camera_id=candidate.camera_id,
                    location=candidate.location,
                    note=note or f"Candidate {candidate_id} confirmed",
                    sort_order=0,
                )
                self.db.add(timeline_entry)
            else:
                timeline_entry.timestamp = (
                    candidate.timestamp or timeline_entry.timestamp
                )
                timeline_entry.camera_id = candidate.camera_id
                timeline_entry.location = candidate.location
                if note is not None:
                    timeline_entry.note = note
        elif timeline_entry is not None:
            self.db.delete(timeline_entry)

        self.db.flush()
        self._update_review_status(investigation)
        self._renumber_timeline(investigation.id)
        self._audit(
            "candidate",
            candidate_id,
            verification_status,
            {
                "investigation_id": investigation_id,
                **({"note": note} if note else {}),
            },
        )
        self.db.commit()
        return candidate

    def get_timeline(
        self,
        investigation_id: str,
    ) -> Optional[list[InvestigationTimelineEntry]]:
        inv = self.get_investigation(investigation_id)
        if not inv:
            return None
        return (
            self.db.query(InvestigationTimelineEntry)
            .filter(InvestigationTimelineEntry.investigation_id == inv.id)
            .order_by(InvestigationTimelineEntry.timestamp.asc())
            .all()
        )

    def _update_review_status(self, investigation: Investigation):
        statuses = [
            status
            for (status,) in (
                self.db.query(CandidateClip.verification_status)
                .filter(CandidateClip.investigation_id == investigation.id)
                .all()
            )
        ]
        if statuses and all(status != "pending" for status in statuses):
            investigation.status = "review_complete"
        elif "confirmed" in statuses:
            investigation.status = "in_progress"
        else:
            investigation.status = "awaiting_review"

    def _renumber_timeline(self, investigation_id: int):
        entries = (
            self.db.query(InvestigationTimelineEntry)
            .filter(InvestigationTimelineEntry.investigation_id == investigation_id)
            .order_by(
                InvestigationTimelineEntry.timestamp.asc(),
                InvestigationTimelineEntry.id.asc(),
            )
            .all()
        )
        for sort_order, entry in enumerate(entries):
            entry.sort_order = sort_order

    def _generate_candidates(self, investigation: Investigation, report: Report):
        attributes = SearchAttributes.model_validate(report.attributes or {})
        clips = load_clip_library(self.library_path)
        for clip in retrieve_candidates(attributes, clips):
            media_path = Path(clip["path"])
            if not media_path.is_absolute():
                media_path = REPO_ROOT / media_path
            media_available = media_path.is_file()
            vlm_result = self.ai.verify_clip(
                media_path,
                attributes,
                cached_vlm=clip["cached_vlm_result"],
            )
            supported = ", ".join(vlm_result.supported_attributes) or "none"
            contradicted = ", ".join(vlm_result.contradicted_attributes) or "none"
            self.db.add(CandidateClip(
                investigation_id=investigation.id,
                clip_id=clip["clip_id"],
                score=clip["metadata_score"],
                explanation=(
                    f"Supported: {supported}. Contradicted: {contradicted}."
                ),
                url=None,
                snapshot_url=None,
                camera_id=clip["camera_id"],
                location=clip["location"],
                clip_metadata={
                    "start_time": clip["start_time"],
                    "end_time": clip["end_time"],
                    "attributes": clip["attributes"],
                    "matched_attributes": clip["matched_attributes"],
                    "metadata_score": clip["metadata_score"],
                    "media_available": media_available,
                },
                vlm_result=vlm_result.model_dump(mode="json"),
                timestamp=datetime.datetime.fromisoformat(clip["start_time"]),
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
            timestamp=datetime.datetime.now(datetime.UTC),
        ))
