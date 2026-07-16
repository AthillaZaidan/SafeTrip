from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .geometry import motion_features
from .schemas import TrackObservation


@dataclass
class TrackState:
    track_id: int
    first_seen_frame: int
    last_seen_frame: int
    observations: deque[TrackObservation]
    current_zone_id: str | None = None
    previous_zone_id: str | None = None
    zone_entered_frame: int | None = None
    zone_entered_timestamp: float | None = None
    normalized_speed: float = 0.0
    direction_vector: tuple[float, float] = (0.0, 0.0)
    last_event_timestamp: dict[str, float] = field(default_factory=dict)

    def normalized_speed_over(self, window_seconds: float) -> float:
        if window_seconds <= 0 or len(self.observations) < 2:
            return self.normalized_speed
        current = self.observations[-1]
        previous = next(
            (item for item in reversed(self.observations) if current.timestamp_seconds - item.timestamp_seconds >= window_seconds),
            None,
        )
        if previous is None:
            return self.normalized_speed
        return motion_features(
            previous.footpoint_xy,
            current.footpoint_xy,
            current.timestamp_seconds - previous.timestamp_seconds,
            current.bbox_height,
        ).normalized_speed


class TrackStateManager:
    def __init__(self, history_size: int = 30, missing_frame_tolerance: int = 2):
        if history_size < 2 or missing_frame_tolerance < 0:
            raise ValueError("invalid track-state limits")
        self.history_size = history_size
        self.missing_frame_tolerance = missing_frame_tolerance
        self.states: dict[int, TrackState] = {}

    def update(self, observation: TrackObservation) -> TrackState:
        state = self.states.get(observation.track_id)
        if state is None:
            state = TrackState(
                track_id=observation.track_id,
                first_seen_frame=observation.frame_index,
                last_seen_frame=observation.frame_index,
                observations=deque(maxlen=self.history_size),
            )
            self.states[observation.track_id] = state
        previous = state.observations[-1] if state.observations else None
        frame_gap = observation.frame_index - state.last_seen_frame
        if previous is not None and frame_gap <= self.missing_frame_tolerance + 1:
            elapsed = observation.timestamp_seconds - previous.timestamp_seconds
            if elapsed > 0:
                motion = motion_features(previous.footpoint_xy, observation.footpoint_xy, elapsed, observation.bbox_height)
                state.normalized_speed = motion.normalized_speed
                state.direction_vector = motion.direction_vector
        else:
            state.normalized_speed = 0.0
            state.direction_vector = (0.0, 0.0)
        state.observations.append(observation)
        state.last_seen_frame = observation.frame_index
        return state

    def remove_stale(self, current_frame: int) -> list[TrackState]:
        stale_ids = [track_id for track_id, state in self.states.items() if current_frame - state.last_seen_frame > self.missing_frame_tolerance]
        return [self.states.pop(track_id) for track_id in stale_ids]

    def reset(self) -> None:
        self.states.clear()
