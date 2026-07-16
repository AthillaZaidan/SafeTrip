from __future__ import annotations

from collections.abc import Sequence

from .geometry import direction_alignment, point_in_polygon
from .schemas import ZoneConfig
from .track_state import TrackState


def get_active_zone(footpoint: tuple[float, float], zones: Sequence[ZoneConfig]) -> ZoneConfig | None:
    return next((zone for zone in zones if point_in_polygon(footpoint, zone.polygon)), None)


def validate_zones_for_frame(zones: Sequence[ZoneConfig], *, width: int, height: int) -> None:
    for zone in zones:
        if any(x < 0 or y < 0 or x > width or y > height for x, y in zone.polygon):
            raise ValueError(f"zone {zone.zone_id} has coordinates outside frame {width}x{height}")


def update_zone_transition(state: TrackState, zone: ZoneConfig | None, frame_index: int, timestamp_seconds: float) -> bool:
    zone_id = None if zone is None else zone.zone_id
    if zone_id == state.current_zone_id:
        return False
    state.previous_zone_id = state.current_zone_id
    state.current_zone_id = zone_id
    state.zone_entered_frame = frame_index if zone is not None else None
    state.zone_entered_timestamp = timestamp_seconds if zone is not None else None
    return True


def calculate_zone_dwell_seconds(state: TrackState, timestamp_seconds: float) -> float:
    if state.zone_entered_timestamp is None:
        return 0.0
    return max(0.0, timestamp_seconds - state.zone_entered_timestamp)


def calculate_direction_alignment(state: TrackState, danger_direction: tuple[float, float] | None) -> float | None:
    if danger_direction is None:
        return None
    return direction_alignment(state.direction_vector, danger_direction)
