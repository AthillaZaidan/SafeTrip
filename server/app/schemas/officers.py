from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class OfficerBase(BaseModel):
    officer_id: str
    name: str
    role: str = "Safety Officer"
    location: str = ""
    status: str = "available"

    model_config = {"from_attributes": True}


class OfficerList(OfficerBase):
    pass


class OfficerRecommendRequest(BaseModel):
    incident_location: str = ""
    count: int = 1


class OfficerRecommend(OfficerBase):
    distance: float = 0.0


class AssignmentCreate(BaseModel):
    officer_id: str


class AssignmentUpdate(BaseModel):
    status: str
    notes: str = ""
