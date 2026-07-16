from __future__ import annotations

import re
from collections import defaultdict, deque
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from .config import CameraConfig
from .event_detectors import CrowdCompressionDetector, PersonDownDetector, RestrictedIntrusionDetector, RunningOnTrackDetector
from .evidence import evidence_paths
from .geometry import bbox_footpoint, point_in_polygon
from .schemas import ConfirmedEvent, Incident, TrackObservation
from .track_state import TrackStateManager
from .zone_analysis import calculate_direction_alignment


class SafetyPipeline:
    def __init__(self, camera: CameraConfig, event_rules: dict[str, dict[str, float | bool]], *, source_mode: str, evidence_root: str | Path = "outputs/incidents"):
        if source_mode not in {"full_ai", "cached_ai", "manual_demo"}:
            raise ValueError(f"unsupported source_mode: {source_mode}")
        self.camera = camera
        self.rules = event_rules
        self.source_mode = source_mode
        self.evidence_root = evidence_root
        self.track_states = TrackStateManager()
        self.pose_track_states = TrackStateManager()
        restricted = event_rules["restricted_zone_intrusion"]
        running = event_rules["person_running_on_track"]
        down = event_rules["possible_person_down"]
        crowd = event_rules["crowd_compression"]
        self.restricted = RestrictedIntrusionDetector(float(restricted["minimum_duration_seconds"]), float(restricted["cooldown_seconds"]), float(restricted.get("danger_direction_cosine_threshold", 0.5)))
        self.running = RunningOnTrackDetector(float(running["minimum_normalized_speed"]), float(running["minimum_duration_seconds"]), float(running["cooldown_seconds"]))
        self.person_down = PersonDownDetector(float(down["minimum_aspect_ratio"]), float(down["maximum_normalized_speed"]), float(down["minimum_duration_seconds"]), float(down["cooldown_seconds"]), float(down.get("minimum_pose_horizontal_score", 0.65)))
        self._person_down_motion_window = float(down.get("motion_window_seconds", 0.75))
        self.crowd = CrowdCompressionDetector(float(crowd["minimum_density_ratio"]), float(crowd["minimum_density_growth"]), float(crowd["maximum_average_normalized_speed"]), float(crowd["minimum_duration_seconds"]), float(crowd["cooldown_seconds"]))
        self._crowd_growth_window = float(crowd.get("density_growth_window_seconds", 2.0))
        self._crowd_motion_window = float(crowd.get("motion_window_seconds", 0.75))
        self._crowd_history: dict[str, deque[tuple[float, float]]] = defaultdict(deque)
        self._incident_sequence = 0

    def _observation(self, raw: dict[str, Any], frame_index: int, timestamp: float) -> TrackObservation:
        bbox = tuple(float(value) for value in raw["bbox_xyxy"])
        return TrackObservation(
            frame_index,
            timestamp,
            int(raw["track_id"]),
            float(raw.get("confidence", 0.0)),
            bbox,
            bbox_footpoint(bbox),
            max(0.0, bbox[2] - bbox[0]),
            max(0.0, bbox[3] - bbox[1]),
        )

    def process_cached_frames(self, frames: Iterable[dict[str, Any]]) -> list[Incident]:
        incidents: list[Incident] = []
        restricted_zones = [zone for zone in self.camera.zones if zone.zone_type == "restricted"]
        track_zones = [zone for zone in self.camera.zones if zone.zone_type == "track_area"]
        crowd_zones = [zone for zone in self.camera.zones if zone.zone_type == "crowd_monitoring"]

        for frame in frames:
            frame_index = int(frame["frame_index"])
            timestamp = float(frame["timestamp_seconds"])
            observations = [self._observation(raw, frame_index, timestamp) for raw in frame.get("tracks", [])]
            states = {observation.track_id: self.track_states.update(observation) for observation in observations}
            pose_tracking = "pose_tracks" in frame
            pose_observations = [self._observation(raw, frame_index, timestamp) for raw in frame.get("pose_tracks", [])]
            pose_states = {observation.track_id: self.pose_track_states.update(observation) for observation in pose_observations}
            events: list[ConfirmedEvent] = []

            for observation in observations:
                state = states[observation.track_id]
                for zone in restricted_zones:
                    inside = point_in_polygon(observation.footpoint_xy, zone.polygon)
                    event = self.restricted.update(self.camera.camera_id, zone.zone_id, observation.track_id, timestamp, inside, calculate_direction_alignment(state, zone.danger_direction), observation.confidence)
                    if event:
                        events.append(event)
                for zone in track_zones:
                    inside = point_in_polygon(observation.footpoint_xy, zone.polygon)
                    event = self.running.update(self.camera.camera_id, zone.zone_id, observation.track_id, timestamp, inside, state.normalized_speed, observation.confidence, state.direction_vector)
                    if event:
                        events.append(event)
                if not pose_tracking:
                    aspect_ratio = observation.bbox_width / max(observation.bbox_height, 1.0)
                    event = self.person_down.update(self.camera.camera_id, observation.track_id, timestamp, aspect_ratio, state.normalized_speed, frame.get("pose_scores", {}).get(str(observation.track_id)), observation.confidence)
                    if event:
                        events.append(event)

            for raw, observation in zip(frame.get("pose_tracks", []), pose_observations, strict=True):
                state = pose_states[observation.track_id]
                aspect_ratio = observation.bbox_width / max(observation.bbox_height, 1.0)
                event = self.person_down.update(
                    self.camera.camera_id,
                    observation.track_id,
                    timestamp,
                    aspect_ratio,
                    state.normalized_speed_over(self._person_down_motion_window),
                    raw.get("horizontal_score"),
                    observation.confidence,
                    entity_prefix="pose_track",
                )
                if event:
                    events.append(event)

            for zone in crowd_zones:
                members = [observation for observation in observations if point_in_polygon(observation.footpoint_xy, zone.polygon)]
                density_ratio = len(members) / max(zone.capacity or 1, 1)
                history = self._crowd_history[zone.zone_id]
                target = timestamp - self._crowd_growth_window
                oldest_allowed = timestamp - 2 * self._crowd_growth_window
                while history and history[0][0] < oldest_allowed:
                    history.popleft()
                eligible = [ratio for sample_time, ratio in history if sample_time <= target]
                density_growth = density_ratio - eligible[-1] if eligible else 0.0
                history.append((timestamp, density_ratio))
                speeds = [states[item.track_id].normalized_speed_over(self._crowd_motion_window) for item in members]
                average_speed = median(speeds) if speeds else 0.0
                directions = [states[item.track_id].direction_vector for item in members if states[item.track_id].direction_vector != (0.0, 0.0)]
                flow_consistency = None
                if directions:
                    flow_consistency = ((sum(x for x, _ in directions) / len(directions)) ** 2 + (sum(y for _, y in directions) / len(directions)) ** 2) ** 0.5
                event = self.crowd.update(self.camera.camera_id, zone.zone_id, timestamp, len(members), zone.capacity or 1, density_growth, average_speed, flow_consistency)
                if event:
                    events.append(event)

            incidents.extend(self._incident(event) for event in events)
            self.track_states.remove_stale(frame_index)
            self.pose_track_states.remove_stale(frame_index)
        return incidents

    def _incident(self, event: ConfirmedEvent) -> Incident:
        self._incident_sequence += 1
        camera_token = re.sub(r"[^A-Z0-9]+", "_", self.camera.camera_id.upper()).strip("_")
        incident_id = f"INC_{camera_token}_{self._incident_sequence:06d}"
        return Incident(
            incident_id=incident_id,
            incident_type=event.event_type,
            camera_id=event.camera_id,
            zone_id=event.zone_id,
            entity_ids=event.entity_ids or [event.entity_key],
            timestamp_start_seconds=event.start_timestamp_seconds,
            timestamp_detected_seconds=event.detected_timestamp_seconds,
            timestamp_end_seconds=None,
            duration_seconds=event.detected_timestamp_seconds - event.start_timestamp_seconds,
            detection_confidence=event.confidence,
            indicators=event.indicators,
            evidence=evidence_paths(incident_id, self.evidence_root),
            source_mode=self.source_mode,
        )
