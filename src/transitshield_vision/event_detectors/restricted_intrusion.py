from __future__ import annotations

from ..event_state_machine import EventStateMachine
from ..schemas import ConfirmedEvent


class RestrictedIntrusionDetector:
    def __init__(self, minimum_duration_seconds: float, cooldown_seconds: float, direction_threshold: float = 0.5):
        self.machine = EventStateMachine(minimum_duration_seconds, cooldown_seconds)
        self.direction_threshold = direction_threshold

    def update(self, camera_id: str, zone_id: str, track_id: int, timestamp_seconds: float, inside: bool, direction_alignment: float | None, confidence: float) -> ConfirmedEvent | None:
        key = f"{camera_id}:{zone_id}:track:{track_id}"
        result = self.machine.update(key, inside, timestamp_seconds)
        if not result.confirmed_now:
            return None
        return ConfirmedEvent(
            "restricted_zone_intrusion",
            camera_id,
            zone_id,
            key,
            [f"track:{track_id}"],
            result.candidate_started_at or timestamp_seconds,
            timestamp_seconds,
            confidence,
            {
                "inside_restricted_zone": True,
                "restricted_dwell_seconds": result.persistence_seconds,
                "moving_toward_danger": direction_alignment is not None and direction_alignment >= self.direction_threshold,
                "direction_alignment": direction_alignment,
                "people_count": 1,
            },
        )
