from __future__ import annotations

import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class VLMResult(BaseModel):
    supported_attributes: list[str] = Field(default_factory=list)
    contradicted_attributes: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    relevant_start_seconds: Optional[float] = Field(default=None, ge=0)
    relevant_end_seconds: Optional[float] = Field(default=None, ge=0)
    match_recommendation: Literal["likely_match", "possible_match", "unlikely_match"]
    source: Literal["gemini", "cached", "fallback"]

    @model_validator(mode="after")
    def validate_relevant_range(self):
        if (
            self.relevant_start_seconds is not None
            and self.relevant_end_seconds is not None
            and self.relevant_end_seconds < self.relevant_start_seconds
        ):
            raise ValueError("relevant_end_seconds must not be before relevant_start_seconds")
        return self


class CandidateUpdate(BaseModel):
    verification_status: Literal["confirmed", "rejected"]
    note: Optional[str] = None


class CandidateSchema(BaseModel):
    candidate_id: str
    clip_id: str = ""
    score: float
    explanation: str = ""
    url: str = ""
    snapshot_url: str = ""
    camera_id: str = ""
    location: str = ""
    clip_metadata: dict = Field(default_factory=dict)
    vlm_result: dict = Field(default_factory=dict)
    media_available: bool = False
    timestamp: Optional[datetime.datetime] = None
    verification_status: str = "pending"

    model_config = {"from_attributes": True}


class TimelineEntrySchema(BaseModel):
    id: int
    camera_id: str = ""
    location: str = ""
    timestamp: Optional[datetime.datetime] = None
    note: str = ""
    sort_order: int = 0
    human_verified: bool = False

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
    search_filters: dict = Field(default_factory=dict)
    candidate_clips: list[CandidateSchema] = Field(default_factory=list)
    timeline_entries: list[TimelineEntrySchema] = Field(default_factory=list)
