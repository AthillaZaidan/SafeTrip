from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.investigations import (
    CandidateSchema,
    CandidateUpdate,
    InvestigationCreate,
    InvestigationDetail,
    TimelineEntrySchema,
)
from ..services.investigation_service import InvestigationService, ReportNotReadyError

router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])


@router.post("", response_model=InvestigationDetail)
def create_investigation(data: InvestigationCreate, db: Session = Depends(get_db)):
    try:
        inv = InvestigationService(db).create_investigation(data.report_id)
    except ReportNotReadyError as error:
        raise HTTPException(409, str(error)) from error
    if not inv:
        raise HTTPException(404, "Report not found")
    return _inv_to_detail(inv)


@router.get("/{investigation_id}", response_model=InvestigationDetail)
def get_investigation(investigation_id: str, db: Session = Depends(get_db)):
    inv = InvestigationService(db).get_investigation(investigation_id)
    if not inv:
        raise HTTPException(404, "Investigation not found")
    return _inv_to_detail(inv)


@router.get("/{investigation_id}/candidates", response_model=list[CandidateSchema])
def list_candidates(investigation_id: str, db: Session = Depends(get_db)):
    candidates = InvestigationService(db).list_candidates(investigation_id)
    if candidates is None:
        raise HTTPException(404, "Investigation not found")
    return [_candidate_to_schema(candidate) for candidate in candidates]


@router.patch("/{investigation_id}/candidates/{candidate_id}")
def update_candidate(investigation_id: str, candidate_id: str, data: CandidateUpdate, db: Session = Depends(get_db)):
    result = InvestigationService(db).update_candidate(
        investigation_id, candidate_id, data.verification_status
    )
    if not result:
        raise HTTPException(404, "Candidate not found")
    return {"candidate_id": candidate_id, "verification_status": result.verification_status}


@router.get("/{investigation_id}/timeline")
def get_investigation_timeline(investigation_id: str, db: Session = Depends(get_db)):
    entries = InvestigationService(db).get_timeline(investigation_id)
    return [
        {"id": e.id, "camera_id": e.camera_id, "timestamp": e.timestamp, "note": e.note, "sort_order": e.sort_order}
        for e in entries
    ]


def _inv_to_detail(inv):
    return {
        "investigation_id": inv.investigation_id,
        "report_id": inv.report.report_id if inv.report else "",
        "status": inv.status,
        "search_filters": inv.search_filters or {},
        "candidate_clips": [
            _candidate_to_schema(candidate)
            for candidate in sorted(
                inv.candidate_clips,
                key=lambda candidate: (-candidate.score, candidate.clip_id),
            )
        ],
        "timeline_entries": [
            {"id": e.id, "camera_id": e.camera_id, "timestamp": e.timestamp, "note": e.note, "sort_order": e.sort_order}
            for e in inv.timeline_entries
        ],
    }


def _candidate_to_schema(candidate) -> CandidateSchema:
    metadata = candidate.clip_metadata or {}
    return CandidateSchema(
        candidate_id=candidate.candidate_id,
        clip_id=candidate.clip_id or "",
        score=candidate.score,
        explanation=candidate.explanation or "",
        url=candidate.url or None,
        snapshot_url=candidate.snapshot_url or None,
        camera_id=candidate.camera_id or "",
        location=candidate.location or "",
        clip_metadata=metadata,
        vlm_result=candidate.vlm_result or None,
        media_available=bool(metadata.get("media_available")),
        timestamp=candidate.timestamp,
        verification_status=candidate.verification_status,
    )
