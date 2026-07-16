from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.reports import AttributeUpdate, ReportCreate, ReportDetail, ReportList, ReportUpdate
from ..services.report_service import ReportService

router = APIRouter(prefix="/api/v1", tags=["reports"])


@router.get("/reports", response_model=list[ReportList])
def list_reports(db: Session = Depends(get_db)):
    return ReportService(db).list_reports()


@router.post("/reports", response_model=ReportDetail)
def create_report(data: ReportCreate, db: Session = Depends(get_db)):
    report = ReportService(db).create_report(data.model_dump())
    return _report_to_detail(report)


@router.get("/reports/{report_id}", response_model=ReportDetail)
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = ReportService(db).get_report(report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return _report_to_detail(report)


@router.post("/reports/{report_id}/extract")
def extract_attributes(report_id: str, db: Session = Depends(get_db)):
    attrs = ReportService(db).extract_attributes(report_id)
    if not attrs:
        raise HTTPException(404, "Report not found")
    return {"report_id": report_id, "attributes": attrs}


@router.patch("/reports/{report_id}/attributes")
def update_attributes(report_id: str, data: AttributeUpdate, db: Session = Depends(get_db)):
    report = ReportService(db).update_attributes(report_id, data.attributes)
    if not report:
        raise HTTPException(404, "Report not found")
    return {"report_id": report_id, "attributes": report.attributes, "status": report.status}


def _report_to_detail(report):
    return {
        "report_id": report.report_id,
        "reporter_type": report.reporter_type,
        "time_window_start": report.time_window_start,
        "time_window_end": report.time_window_end,
        "location": report.location,
        "description": report.description,
        "direction": report.direction,
        "attributes": report.attributes or {},
        "image_url": report.image_url,
        "status": report.status,
    }
