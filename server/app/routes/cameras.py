from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.cameras import AnalyzeRequest, AnalyzeResponse, CameraDetail, CameraList
from ..services.camera_service import CameraService

router = APIRouter(prefix="/api/v1/cameras", tags=["cameras"])


@router.get("", response_model=list[CameraList])
def list_cameras(db: Session = Depends(get_db)):
    return CameraService(db).list_cameras()


@router.get("/{camera_id}", response_model=CameraDetail)
def get_camera(camera_id: str, db: Session = Depends(get_db)):
    cam = CameraService(db).get_camera(camera_id)
    if not cam:
        raise HTTPException(404, "Camera not found")
    cam_dict = CameraDetail.model_validate(cam).model_dump()
    cam_dict["zones"] = CameraService(db).get_zones(camera_id)
    return cam_dict


@router.get("/{camera_id}/zones")
def get_camera_zones(camera_id: str, db: Session = Depends(get_db)):
    zones = CameraService(db).get_zones(camera_id)
    return [{"zone_id": z.zone_id, "zone_type": z.zone_type, "polygon": z.polygon,
             "capacity": z.capacity, "risk_multiplier": z.risk_multiplier,
             "danger_direction": z.danger_direction} for z in zones]


@router.post("/{camera_id}/analyze", response_model=AnalyzeResponse)
def analyze_camera(camera_id: str, req: AnalyzeRequest, db: Session = Depends(get_db)):
    result = CameraService(db).analyze(camera_id, req.execution_mode)
    return result
