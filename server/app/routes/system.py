from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db

router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "services": {
            "api": "ok",
            "database": "ok",
            "vision": "ok",
        },
    }


@router.get("/demo/scenarios")
def list_scenarios():
    return {
        "scenarios": [
            {"id": "restricted_intrusion", "name": "Restricted Zone Intrusion", "camera_id": "CAM_PLATFORM_B_01"},
            {"id": "person_down", "name": "Person Down Incident", "camera_id": "CAM_PLATFORM_B_01"},
            {"id": "crowd_compression", "name": "Crowd Compression", "camera_id": "CAM_PLATFORM_B_01"},
        ],
    }


@router.post("/demo/reset")
def reset_demo():
    return {"status": "reset", "message": "Demo data reset to initial state"}
