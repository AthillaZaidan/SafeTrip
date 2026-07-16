from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.incidents import (
    AssignmentBase,
    EvidenceClipSchema,
    IncidentCreate,
    IncidentDetail,
    IncidentList,
    IncidentUpdate,
    PlaybookApproval,
    TimelineEventSchema,
)
from ..schemas.officers import AssignmentCreate, AssignmentUpdate
from ..services.incident_service import IncidentService

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentList])
def list_incidents(
    status: str | None = Query(None),
    severity: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return IncidentService(db).list_incidents(status=status, severity=severity)


@router.post("", response_model=IncidentDetail)
def create_incident(data: IncidentCreate, db: Session = Depends(get_db)):
    incident = IncidentService(db).create_incident(data.model_dump())
    return _to_detail(incident, db)


@router.get("/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = IncidentService(db).get_incident(incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    return _to_detail(incident, db)


@router.patch("/{incident_id}", response_model=IncidentDetail)
def update_incident(incident_id: str, data: IncidentUpdate, db: Session = Depends(get_db)):
    incident = IncidentService(db).update_incident(incident_id, data.model_dump(exclude_none=True))
    if not incident:
        raise HTTPException(404, "Incident not found")
    return _to_detail(incident, db)


@router.get("/{incident_id}/evidence")
def get_evidence(incident_id: str, db: Session = Depends(get_db)):
    clips = IncidentService(db).get_evidence(incident_id)
    return [EvidenceClipSchema.model_validate(c).model_dump() for c in clips]


@router.get("/{incident_id}/timeline")
def get_timeline(incident_id: str, db: Session = Depends(get_db)):
    events = IncidentService(db).get_timeline(incident_id)
    return [TimelineEventSchema.model_validate(e).model_dump() for e in events]


@router.post("/{incident_id}/playbook")
def approve_playbook(incident_id: str, data: PlaybookApproval, db: Session = Depends(get_db)):
    incident = IncidentService(db).approve_playbook(incident_id, data.playbook_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    return {"status": "approved", "playbook_id": data.playbook_id}


@router.post("/{incident_id}/assignments")
def assign_officer(incident_id: str, data: AssignmentCreate, db: Session = Depends(get_db)):
    result = IncidentService(db).assign_officer(incident_id, data.officer_id)
    if not result:
        raise HTTPException(400, "Incident or officer not found")
    return result


@router.patch("/assignments/{assignment_id}")
def update_assignment(assignment_id: str, data: AssignmentUpdate, db: Session = Depends(get_db)):
    result = IncidentService(db).update_assignment(assignment_id, data.status, data.notes)
    if not result:
        raise HTTPException(404, "Assignment not found")
    return result


def _to_detail(incident, db: Session):
    svc = IncidentService(db)
    assignments = []
    for a in incident.assignments:
        assignments.append({
            "assignment_id": a.assignment_id,
            "officer_name": a.officer.name if a.officer else "",
            "officer_id": a.officer.officer_id if a.officer else "",
            "status": a.status,
            "notes": a.notes,
            "assigned_at": a.assigned_at,
            "acknowledged_at": a.acknowledged_at,
            "arrived_at": a.arrived_at,
            "resolved_at": a.resolved_at,
        })
    return {
        "incident_id": incident.incident_id,
        "incident_type": incident.incident_type,
        "severity": incident.severity,
        "risk_score": incident.risk_score,
        "status": incident.status,
        "location": incident.location,
        "camera_id": incident.camera_ref.camera_id if incident.camera_ref else "",
        "zone_id": incident.zone_ref.zone_id if incident.zone_ref else "",
        "description": incident.description,
        "indicators": incident.indicators or {},
        "evidence": incident.evidence or {},
        "source_mode": incident.source_mode,
        "resolution_notes": incident.resolution_notes,
        "timestamp": incident.timestamp,
        "created_at": incident.created_at,
        "updated_at": incident.updated_at,
        "assignments": assignments,
        "evidence_clips": [EvidenceClipSchema.model_validate(c).model_dump() for c in incident.evidence_clips],
        "timeline_events": [TimelineEventSchema.model_validate(e).model_dump() for e in incident.timeline_events],
    }
