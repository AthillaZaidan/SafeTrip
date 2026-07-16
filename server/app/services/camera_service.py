from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..db.orm import AuditEvent, Camera, Zone


class CameraService:
    def __init__(self, db: Session):
        self.db = db

    def list_cameras(self) -> list[Camera]:
        return self.db.query(Camera).all()

    def get_camera(self, camera_id: str) -> Optional[Camera]:
        return self.db.query(Camera).filter(Camera.camera_id == camera_id).first()

    def get_zones(self, camera_id: str) -> list[Zone]:
        cam = self.get_camera(camera_id)
        if not cam:
            return []
        return self.db.query(Zone).filter(Zone.camera_id == cam.id).all()

    def analyze(self, camera_id: str, execution_mode: str) -> dict:
        cam = self.get_camera(camera_id)
        if not cam:
            return {"status": "error", "message": "Camera not found"}
        return {
            "camera_id": camera_id,
            "status": "completed",
            "incidents_found": 0,
            "mode": execution_mode,
        }

    def _audit(self, entity_type: str, entity_id: str, action: str, details: dict = None):
        self.db.add(AuditEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details=details or {},
            timestamp=datetime.datetime.utcnow(),
        ))
