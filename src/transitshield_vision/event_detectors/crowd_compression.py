from __future__ import annotations

from ..event_state_machine import EventStateMachine
from ..schemas import ConfirmedEvent


class CrowdCompressionDetector:
    def __init__(self, minimum_density_ratio: float, minimum_density_growth: float, maximum_average_normalized_speed: float, minimum_duration_seconds: float, cooldown_seconds: float):
        self.minimum_density_ratio = minimum_density_ratio
        self.minimum_density_growth = minimum_density_growth
        self.maximum_speed = maximum_average_normalized_speed
        self.machine = EventStateMachine(minimum_duration_seconds, cooldown_seconds)

    def update(self, camera_id: str, zone_id: str, timestamp_seconds: float, people_count: int, capacity: int, density_growth: float, average_normalized_speed: float, flow_consistency: float | None) -> ConfirmedEvent | None:
        density_ratio = people_count / max(capacity, 1)
        condition = density_ratio >= self.minimum_density_ratio and density_growth >= self.minimum_density_growth and average_normalized_speed <= self.maximum_speed
        key = f"{camera_id}:{zone_id}"
        result = self.machine.update(key, condition, timestamp_seconds)
        if not result.confirmed_now:
            return None
        return ConfirmedEvent(
            "crowd_compression",
            camera_id,
            zone_id,
            key,
            [],
            result.candidate_started_at or timestamp_seconds,
            timestamp_seconds,
            min(1.0, density_ratio),
            {
                "people_count": people_count,
                "configured_capacity": capacity,
                "density_ratio": density_ratio,
                "density_growth": density_growth,
                "average_normalized_speed": average_normalized_speed,
                "flow_consistency": flow_consistency,
                "compression_persistence_seconds": result.persistence_seconds,
            },
        )
