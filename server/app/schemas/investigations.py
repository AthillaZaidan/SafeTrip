from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CandidateUpdate(BaseModel):
    verification_status: str


class CandidateSchema(BaseModel):
    candidate_id: str
    score: float
    explanation: str = ""
    url: str = ""
    snapshot_url: str = ""
    camera_id: str = ""
    timestamp: Optional[datetime.datetime] = None
    verification_status: str = "pending"

    model_config = {"from_attributes": True}


class TimelineEntrySchema(BaseModel):
    id: int
    camera_id: str = ""
    timestamp: Optional[datetime.datetime] = None
    note: str = ""
    sort_order: int = 0

    model_config = {"from_attributes": True}


class InvestigationCreate(BaseModel):
    report_id: str


class InvestigationList(BaseModel):
    investigation_id: str
    report_id: str = ""
    status: str = "pending"
    created_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


class InvestigationDetail(InvestigationList):
    search_filters: dict = {}
    candidate_clips: list[CandidateSchema] = []
    timeline_entries: list[TimelineEntrySchema] = []
