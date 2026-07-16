from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.risk import PlaybookRecommendRequest, PlaybookSchema, RiskInput, RiskOutput
from ..services.risk_service import RiskService

router = APIRouter(prefix="/api/v1", tags=["risk"])


@router.post("/risk/assess", response_model=RiskOutput)
def assess_risk(data: RiskInput, db: Session = Depends(get_db)):
    return RiskService(db).assess(data.model_dump())


@router.get("/playbooks", response_model=list[PlaybookSchema])
def list_playbooks(db: Session = Depends(get_db)):
    playbooks = RiskService(db).list_playbooks()
    return [
        {
            "id": p.id,
            "name": p.name,
            "incident_type": p.incident_type,
            "severity": p.severity,
            "actions": p.actions or [],
            "escalation_condition": p.escalation_condition,
            "escalation_playbook_id": p.escalation_playbook_id,
        }
        for p in playbooks
    ]


@router.get("/playbooks/recommend", response_model=PlaybookSchema)
def recommend_playbook(incident_type: str, severity: str = "medium", db: Session = Depends(get_db)):
    p = RiskService(db).recommend_playbook(incident_type, severity)
    if not p:
        raise HTTPException(404, "No matching playbook found")
    return {
        "id": p.id,
        "name": p.name,
        "incident_type": p.incident_type,
        "severity": p.severity,
        "actions": p.actions or [],
        "escalation_condition": p.escalation_condition,
        "escalation_playbook_id": p.escalation_playbook_id,
    }
