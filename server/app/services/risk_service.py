from __future__ import annotations

import datetime, json, math
from typing import Optional

from sqlalchemy.orm import Session

from ..db.orm import Playbook


class RiskService:
    RISK_WEIGHTS = {
        "zone_multiplier": 0.30,
        "duration": 0.25,
        "person_count": 0.20,
        "density_growth": 0.15,
        "movement_speed": 0.10,
    }

    def __init__(self, db: Session):
        self.db = db

    def assess(self, data: dict) -> dict:
        zone_mult = data.get("zone_multiplier", 1.0)
        duration = data.get("duration_seconds", 0.0)
        person_count = data.get("person_count", 1)
        density_growth = data.get("density_growth", 0.0)
        movement_speed = data.get("movement_speed", 0.0)

        duration_score = min(duration / 30.0, 1.0)
        person_score = min(person_count / 20.0, 1.0)
        growth_score = min(density_growth / 0.3, 1.0)
        speed_score = min(movement_speed / 2.0, 1.0)

        score = 0.0
        score += zone_mult * self.RISK_WEIGHTS["zone_multiplier"] * 100
        score += duration_score * self.RISK_WEIGHTS["duration"] * 100
        score += person_score * self.RISK_WEIGHTS["person_count"] * 100
        score += growth_score * self.RISK_WEIGHTS["density_growth"] * 100
        score += speed_score * self.RISK_WEIGHTS["movement_speed"] * 100

        score = round(min(score, 100.0), 1)

        if score >= 75:
            severity = "critical"
        elif score >= 50:
            severity = "high"
        elif score >= 25:
            severity = "medium"
        else:
            severity = "low"

        return {
            "risk_score": score,
            "severity": severity,
            "contributing_indicators": {
                "duration_seconds": duration,
                "person_count": person_count,
                "density_growth": round(density_growth, 3),
                "movement_speed": round(movement_speed, 2),
            },
        }

    def list_playbooks(self) -> list[Playbook]:
        return self.db.query(Playbook).all()

    def recommend_playbook(self, incident_type: str, severity: str = "medium") -> Optional[Playbook]:
        return (
            self.db.query(Playbook)
            .filter(Playbook.incident_type == incident_type, Playbook.severity == severity)
            .first()
        ) or self.db.query(Playbook).filter(Playbook.incident_type == incident_type).first()
