from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EvidenceClipSchema(BaseModel):
    camera_id: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    url: str = ""
    snapshot_url: str = ""

    model_config = {"from_attributes": True}


class TimelineEventSchema(BaseModel):
    event_type: str
    description: str = ""
    actor: str = ""
    timestamp: datetime.datetime
    details: dict = {}

    model_config = {"from_attributes": True}


class AssignmentBase(BaseModel):
    assignment_id: str
    officer_name: str = ""
    officer_id: str = ""
    status: str = "assigned"
    notes: str = ""
    assigned_at: Optional[datetime.datetime] = None
    acknowledged_at: Optional[datetime.datetime] = None
    arrived_at: Optional[datetime.datetime] = None
    resolved_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


class IncidentCreate(BaseModel):
    incident_type: str
    camera_id: str = ""
    zone_id: str = ""
    severity: str = "low"
    risk_score: float = 0.0
    location: str = ""
    description: str = ""
    indicators: dict = {}
    evidence: dict = {}
    source_mode: str = "manual_demo"


class IncidentUpdate(BaseModel):
    severity: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    resolution_notes: Optional[str] = None


class IncidentList(BaseModel):
    incident_id: str
    incident_type: str
    severity: str
    risk_score: float
    status: str
    location: str
    camera_id: str = ""
    timestamp: Optional[datetime.datetime] = None
    created_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


class IncidentDetail(IncidentList):
    zone_id: str = ""
    description: str = ""
    indicators: dict = {}
    evidence: dict = {}
    source_mode: str = ""
    resolution_notes: str = ""
    updated_at: Optional[datetime.datetime] = None
    assignments: list[AssignmentBase] = []
    evidence_clips: list[EvidenceClipSchema] = []
    timeline_events: list[TimelineEventSchema] = []


class PlaybookApproval(BaseModel):
    playbook_id: int
