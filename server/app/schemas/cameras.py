from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ZoneSchema(BaseModel):
    zone_id: str
    zone_type: str
    polygon: list[list[float]]
    capacity: Optional[int] = None
    risk_multiplier: float = 1.0
    danger_direction: Optional[list[float]] = None

    model_config = {"from_attributes": True}


class CameraBase(BaseModel):
    camera_id: str
    name: str
    location: str = ""
    stream_source: str = ""
    status: str = "active"

    model_config = {"from_attributes": True}


class CameraDetail(CameraBase):
    zones: list[ZoneSchema] = []


class CameraList(CameraBase):
    pass


class AnalyzeRequest(BaseModel):
    execution_mode: str = "cached_ai"


class AnalyzeResponse(BaseModel):
    camera_id: str
    status: str
    incidents_found: int = 0
