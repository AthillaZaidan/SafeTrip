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
from ..services.investigation_service import InvestigationService

router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])


@router.post("", response_model=InvestigationDetail)
def create_investigation(data: InvestigationCreate, db: Session = Depends(get_db)):
    inv = InvestigationService(db).create_investigation(data.report_id)
    if not inv:
        raise HTTPException(404, "Report not found")
    return _inv_to_detail(inv)


@router.get("/{investigation_id}", response_model=InvestigationDetail)
def get_investigation(investigation_id: str, db: Session = Depends(get_db)):
    inv = InvestigationService(db).get_investigation(investigation_id)
    if not inv:
        raise HTTPException(404, "Investigation not found")
    return _inv_to_detail(inv)


@router.get("/{investigation_id}/candidates")
def list_candidates(investigation_id: str, db: Session = Depends(get_db)):
    return [
        {
            "candidate_id": c.candidate_id,
            "score": c.score,
            "explanation": c.explanation,
            "url": c.url,
            "snapshot_url": c.snapshot_url,
            "camera_id": c.camera_id,
            "timestamp": c.timestamp,
            "verification_status": c.verification_status,
        }
        for c in InvestigationService(db).list_candidates(investigation_id)
    ]


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
            {
                "candidate_id": c.candidate_id,
                "score": c.score,
                "explanation": c.explanation,
                "url": c.url,
                "snapshot_url": c.snapshot_url,
                "camera_id": c.camera_id,
                "timestamp": c.timestamp,
                "verification_status": c.verification_status,
            }
            for c in inv.candidate_clips
        ],
        "timeline_entries": [
            {"id": e.id, "camera_id": e.camera_id, "timestamp": e.timestamp, "note": e.note, "sort_order": e.sort_order}
            for e in inv.timeline_entries
        ],
    }
