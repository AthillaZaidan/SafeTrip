from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RiskInput(BaseModel):
    incident_type: str
    zone_type: str
    duration_seconds: float = 0.0
    person_count: int = 1
    density_growth: float = 0.0
    movement_speed: float = 0.0
    danger_direction_alignment: float = 0.0


class RiskOutput(BaseModel):
    risk_score: float
    severity: str
    contributing_indicators: dict


class PlaybookSchema(BaseModel):
    id: int
    name: str
    incident_type: str
    severity: str = "medium"
    actions: list[str]
    escalation_condition: str = ""
    escalation_playbook_id: Optional[int] = None

    model_config = {"from_attributes": True}


class PlaybookRecommendRequest(BaseModel):
    incident_type: str
    severity: str = "medium"
