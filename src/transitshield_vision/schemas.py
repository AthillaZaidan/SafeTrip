from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


EVENT_TYPES = {
    "restricted_zone_intrusion",
    "possible_person_down",
    "crowd_compression",
    "person_running_on_track",
}
SOURCE_MODES = {"full_ai", "cached_ai", "manual_demo"}


@dataclass(frozen=True)
class Detection:
    frame_index: int
    timestamp_seconds: float
    class_id: int
    class_name: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]


@dataclass(frozen=True)
class TrackObservation:
    frame_index: int
    timestamp_seconds: float
    track_id: int
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]
    footpoint_xy: tuple[float, float]
    bbox_width: float
    bbox_height: float


@dataclass(frozen=True)
class ZoneConfig:
    zone_id: str
    camera_id: str
    zone_type: str
    polygon: tuple[tuple[float, float], ...]
    capacity: int | None = None
    risk_multiplier: float = 1.0
    danger_direction: tuple[float, float] | None = None


@dataclass(frozen=True)
class ConfirmedEvent:
    event_type: str
    camera_id: str
    zone_id: str | None
    entity_key: str
    entity_ids: list[str]
    start_timestamp_seconds: float
    detected_timestamp_seconds: float
    confidence: float
    indicators: dict[str, Any]


@dataclass
class Incident:
    incident_id: str
    incident_type: str
    camera_id: str
    zone_id: str | None
    entity_ids: list[str]
    timestamp_start_seconds: float
    timestamp_detected_seconds: float
    timestamp_end_seconds: float | None
    duration_seconds: float
    detection_confidence: float
    indicators: dict[str, Any]
    evidence: dict[str, str | None]
    source_mode: str
    requires_human_review: bool = True

    def validate(self) -> None:
        if self.incident_type not in EVENT_TYPES:
            raise ValueError(f"unsupported incident_type: {self.incident_type}")
        if self.source_mode not in SOURCE_MODES:
            raise ValueError(f"unsupported source_mode: {self.source_mode}")
        if not self.incident_id or not self.camera_id or not self.entity_ids:
            raise ValueError("incident_id, camera_id, and entity_ids are required")
        if not 0 <= self.detection_confidence <= 1:
            raise ValueError("detection_confidence must be between 0 and 1")
        if self.timestamp_detected_seconds < self.timestamp_start_seconds:
            raise ValueError("detection timestamp cannot precede event start")
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def validate_incident_payload(payload: dict[str, Any]) -> None:
    required = {
        "incident_id",
        "incident_type",
        "camera_id",
        "zone_id",
        "entity_ids",
        "timestamp_start_seconds",
        "timestamp_detected_seconds",
        "timestamp_end_seconds",
        "duration_seconds",
        "detection_confidence",
        "indicators",
        "evidence",
        "source_mode",
        "requires_human_review",
    }
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"incident fields missing: {sorted(missing)}")
    Incident(**{key: payload[key] for key in required}).validate()
