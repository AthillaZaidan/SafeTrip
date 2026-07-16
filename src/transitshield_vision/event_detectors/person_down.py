from __future__ import annotations

from ..event_state_machine import EventStateMachine
from ..schemas import ConfirmedEvent


class PersonDownDetector:
    def __init__(self, minimum_aspect_ratio: float, maximum_normalized_speed: float, minimum_duration_seconds: float, cooldown_seconds: float, minimum_pose_horizontal_score: float = 0.65):
        self.minimum_aspect_ratio = minimum_aspect_ratio
        self.maximum_speed = maximum_normalized_speed
        self.minimum_pose_score = minimum_pose_horizontal_score
        self.machine = EventStateMachine(minimum_duration_seconds, cooldown_seconds)

    def update(self, camera_id: str, track_id: int, timestamp_seconds: float, bbox_aspect_ratio: float, normalized_speed: float, horizontal_body_score: float | None, confidence: float, entity_prefix: str = "track") -> ConfirmedEvent | None:
        geometry = bbox_aspect_ratio >= self.minimum_aspect_ratio and normalized_speed <= self.maximum_speed
        pose_ok = horizontal_body_score is None or horizontal_body_score >= self.minimum_pose_score
        entity_id = f"{entity_prefix}:{track_id}"
        key = f"{camera_id}:{entity_id}"
        result = self.machine.update(key, geometry and pose_ok, timestamp_seconds)
        if not result.confirmed_now:
            return None
        return ConfirmedEvent(
            "possible_person_down",
            camera_id,
            None,
            key,
            [entity_id],
            result.candidate_started_at or timestamp_seconds,
            timestamp_seconds,
            confidence,
            {
                "bbox_aspect_ratio": bbox_aspect_ratio,
                "normalized_speed": normalized_speed,
                "low_motion_seconds": result.persistence_seconds,
                "horizontal_body_score": horizontal_body_score,
                "pose_available": horizontal_body_score is not None,
            },
        )
