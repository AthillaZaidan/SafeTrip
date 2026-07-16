from __future__ import annotations

from ..event_state_machine import EventStateMachine
from ..schemas import ClosedEvent, ConfirmedEvent


class CrowdCompressionDetector:
    def __init__(self, minimum_density_ratio: float, minimum_density_growth: float, maximum_average_normalized_speed: float, minimum_duration_seconds: float, cooldown_seconds: float):
        self.minimum_density_ratio = minimum_density_ratio
        self.minimum_density_growth = minimum_density_growth
        self.maximum_speed = maximum_average_normalized_speed
        self.machine = EventStateMachine(minimum_duration_seconds, cooldown_seconds)
        self._growth_candidates: set[str] = set()
        self._trigger_growth: dict[str, float] = {}

    def update(self, camera_id: str, zone_id: str, timestamp_seconds: float, people_count: int, capacity: int, density_growth: float, average_normalized_speed: float, flow_consistency: float | None, detection_confidence: float = 0.0) -> ConfirmedEvent | ClosedEvent | None:
        density_ratio = people_count / max(capacity, 1)
        key = f"{camera_id}:{zone_id}"
        dense_and_slow = density_ratio >= self.minimum_density_ratio and average_normalized_speed <= self.maximum_speed
        if not dense_and_slow:
            self._growth_candidates.discard(key)
            self._trigger_growth.pop(key, None)
        elif density_growth >= self.minimum_density_growth:
            self._growth_candidates.add(key)
            self._trigger_growth[key] = max(density_growth, self._trigger_growth.get(key, density_growth))
        condition = dense_and_slow and key in self._growth_candidates
        result = self.machine.update(key, condition, timestamp_seconds)
        if result.closed_now:
            return ClosedEvent(key, timestamp_seconds)
        if not result.confirmed_now:
            return None
        return ConfirmedEvent(
            "crowd_compression",
            camera_id,
            zone_id,
            key,
            [],
            result.candidate_started_at if result.candidate_started_at is not None else timestamp_seconds,
            timestamp_seconds,
            detection_confidence,
            {
                "people_count": people_count,
                "configured_capacity": capacity,
                "density_ratio": density_ratio,
                "density_growth": self._trigger_growth.get(key, density_growth),
                "average_normalized_speed": average_normalized_speed,
                "flow_consistency": flow_consistency,
                "compression_persistence_seconds": result.persistence_seconds,
            },
        )
