from __future__ import annotations

from ..event_state_machine import EventStateMachine
from ..schemas import ConfirmedEvent


class RunningOnTrackDetector:
    def __init__(self, minimum_normalized_speed: float, minimum_duration_seconds: float, cooldown_seconds: float):
        self.minimum_speed = minimum_normalized_speed
        self.machine = EventStateMachine(minimum_duration_seconds, cooldown_seconds)

    def update(self, camera_id: str, zone_id: str, track_id: int, timestamp_seconds: float, inside_track_area: bool, normalized_speed: float, confidence: float, movement_direction: tuple[float, float] | None = None) -> ConfirmedEvent | None:
        key = f"{camera_id}:{zone_id}:track:{track_id}"
        result = self.machine.update(key, inside_track_area and normalized_speed >= self.minimum_speed, timestamp_seconds)
        if not result.confirmed_now:
            return None
        return ConfirmedEvent(
            "person_running_on_track",
            camera_id,
            zone_id,
            key,
            [f"track:{track_id}"],
            result.candidate_started_at or timestamp_seconds,
            timestamp_seconds,
            confidence,
            {
                "inside_track_area": True,
                "normalized_speed": normalized_speed,
                "running_duration_seconds": result.persistence_seconds,
                "movement_direction": movement_direction,
                "track_id": track_id,
            },
        )
