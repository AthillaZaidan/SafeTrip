from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.officers import OfficerList, OfficerRecommend, OfficerRecommendRequest
from ..services.officer_service import OfficerService

router = APIRouter(prefix="/api/v1/officers", tags=["officers"])


@router.get("", response_model=list[OfficerList])
def list_officers(status: str | None = Query(None), db: Session = Depends(get_db)):
    return OfficerService(db).list_officers(status=status)


@router.get("/{officer_id}", response_model=OfficerList)
def get_officer(officer_id: str, db: Session = Depends(get_db)):
    o = OfficerService(db).get_officer(officer_id)
    if not o:
        raise HTTPException(404, "Officer not found")
    return o


@router.get("/recommend/list", response_model=list[OfficerRecommend])
def recommend_officers(
    incident_location: str = Query(""),
    count: int = Query(1),
    db: Session = Depends(get_db),
):
    return OfficerService(db).recommend(incident_location, count)
