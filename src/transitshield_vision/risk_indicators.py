from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskContribution:
    indicator: str
    points: int
    reason: str


@dataclass(frozen=True)
class RiskResult:
    score: int
    severity: str
    contributions: tuple[RiskContribution, ...]


def _severity(score: int) -> str:
    if score >= 80:
        return "Critical"
    if score >= 55:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def score_indicators(event_type: str, indicators: dict) -> RiskResult:
    contributions: list[RiskContribution] = []

    def add(condition: bool, indicator: str, points: int, reason: str) -> None:
        if condition:
            contributions.append(RiskContribution(indicator, points, reason))

    if event_type == "restricted_zone_intrusion":
        add(bool(indicators.get("inside_restricted_zone")), "inside_restricted_zone", 30, "Person is inside a configured restricted zone")
        add(float(indicators.get("restricted_dwell_seconds", 0)) >= 3, "restricted_dwell_seconds", 20, "Restricted-zone dwell reached three seconds")
        add(bool(indicators.get("moving_toward_danger")), "moving_toward_danger", 30, "Movement aligns with the configured danger direction")
    elif event_type == "person_running_on_track":
        add(bool(indicators.get("inside_track_area")), "inside_track_area", 40, "Person is inside a railway or vehicle track area")
        add(float(indicators.get("normalized_speed", 0)) >= 1.0, "normalized_speed", 25, "Normalized movement speed is consistent with running")
        add(float(indicators.get("running_duration_seconds", 0)) >= 0.5, "running_duration_seconds", 15, "Running condition persisted beyond the debounce threshold")
    elif event_type == "possible_person_down":
        add(float(indicators.get("bbox_aspect_ratio", 0)) >= 1.1, "bbox_aspect_ratio", 25, "Body geometry is horizontal")
        add(float(indicators.get("normalized_speed", 1)) <= 0.08, "normalized_speed", 25, "Movement is low")
        add(float(indicators.get("low_motion_seconds", 0)) >= 3, "low_motion_seconds", 25, "Low motion persisted")
        add(float(indicators.get("horizontal_body_score") or 0) >= 0.65, "horizontal_body_score", 15, "Pose keypoints support horizontal orientation")
    elif event_type == "crowd_compression":
        add(float(indicators.get("density_ratio", 0)) >= 0.85, "density_ratio", 30, "Zone density is near configured capacity")
        add(float(indicators.get("density_growth", 0)) >= 0.15, "density_growth", 25, "Density rose from its causal baseline")
        add(float(indicators.get("average_normalized_speed", 1)) <= 0.12, "average_normalized_speed", 25, "Average crowd movement is low")
    else:
        raise ValueError(f"unsupported event_type: {event_type}")

    score = min(100, sum(item.points for item in contributions))
    return RiskResult(score, _severity(score), tuple(contributions))
