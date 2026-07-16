from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .geometry import point_in_polygon
from .pose import bbox_iou
from .schemas import Incident, TrackObservation, ZoneConfig


ZONE_COLORS = {
    "normal": (90, 180, 90),
    "limited_dwell": (0, 200, 255),
    "restricted": (0, 0, 255),
    "crowd_monitoring": (255, 170, 0),
    "track_area": (180, 0, 255),
}
EVENT_COLORS = {
    "crowd_compression": (0, 165, 255),
    "person_running_on_track": (0, 0, 255),
    "possible_person_down": (0, 0, 255),
    "restricted_zone_intrusion": (0, 0, 255),
}


def _incident_label(incident: Incident) -> str:
    indicators = incident.indicators
    if incident.incident_type == "restricted_zone_intrusion":
        return f"RESTRICTED INTRUSION | dwell {float(indicators.get('restricted_dwell_seconds') or 0):.1f}s"
    if incident.incident_type == "person_running_on_track":
        return f"RUNNING ON TRACK | speed {float(indicators.get('normalized_speed') or 0):.2f}"
    if incident.incident_type == "possible_person_down":
        pose = indicators.get("horizontal_body_score")
        pose_text = "n/a" if pose is None else f"{float(pose):.2f}"
        return f"POSSIBLE DOWN | pose {pose_text} | still {float(indicators.get('low_motion_seconds') or 0):.1f}s"
    if incident.incident_type == "crowd_compression":
        return f"CROWD COMPRESSION | {int(indicators.get('people_count') or 0)}/{int(indicators.get('configured_capacity') or 0)} people"
    return incident.incident_type.upper().replace("_", " ")


def _active_alerts(incidents: Sequence[Incident], timestamp_seconds: float | None) -> tuple[dict[str, list[tuple[str, str]]], dict[str, list[tuple[str, str]]]]:
    entity_alerts: dict[str, list[tuple[str, str]]] = {}
    zone_alerts: dict[str, list[tuple[str, str]]] = {}
    if timestamp_seconds is None:
        return entity_alerts, zone_alerts
    for incident in incidents:
        if timestamp_seconds < incident.timestamp_detected_seconds:
            continue
        if incident.timestamp_end_seconds is not None and timestamp_seconds > incident.timestamp_end_seconds:
            continue
        alert = (incident.incident_type, _incident_label(incident))
        for entity_id in incident.entity_ids:
            entity_alerts.setdefault(entity_id, []).append(alert)
        if incident.zone_id is not None:
            zone_alerts.setdefault(incident.zone_id, []).append(alert)
    return entity_alerts, zone_alerts


class AnnotatedVideoSink:
    def __init__(self, path: str | Path, *, fps: float, cv2_module: Any = None):
        if fps <= 0:
            raise ValueError("annotated video FPS must be positive")
        if cv2_module is None:
            try:
                import cv2 as cv2_module
            except ImportError as error:
                raise RuntimeError("opencv-python is required for annotated video") from error
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fps = fps
        self.cv2 = cv2_module
        self.writer = None

    def write(self, frame: Any) -> None:
        if self.writer is None:
            height, width = frame.shape[:2]
            self.writer = self.cv2.VideoWriter(self.path.as_posix(), self.cv2.VideoWriter_fourcc(*"mp4v"), self.fps, (width, height))
            if not self.writer.isOpened():
                self.writer.release()
                self.writer = None
                raise RuntimeError(f"failed to open annotated video writer: {self.path}")
        self.writer.write(frame)

    def close(self) -> None:
        if self.writer is not None:
            self.writer.release()
            self.writer = None


def annotate_frame(
    frame: Any,
    zones: Sequence[ZoneConfig],
    tracks: Sequence[TrackObservation],
    event_labels: Sequence[str] = (),
    *,
    pose_tracks: Sequence[TrackObservation] = (),
    incidents: Sequence[Incident] = (),
    timestamp_seconds: float | None = None,
    cv2_module: Any = None,
) -> Any:
    if cv2_module is None:
        try:
            import cv2 as cv2_module
        except ImportError as error:
            raise RuntimeError("opencv-python is required for annotation") from error
    import numpy as np

    annotated = frame.copy()
    font = cv2_module.FONT_HERSHEY_SIMPLEX
    entity_alerts, zone_alerts = _active_alerts(incidents, timestamp_seconds)
    crowd_zone_ids = {
        zone_id
        for zone_id, alerts in zone_alerts.items()
        if any(event_type == "crowd_compression" for event_type, _label in alerts)
    }
    for zone in zones:
        if zone.zone_id not in crowd_zone_ids:
            continue
        for track in tracks:
            if point_in_polygon(track.footpoint_xy, zone.polygon):
                entity_alerts.setdefault(f"track:{track.track_id}", []).extend(zone_alerts[zone.zone_id])

    for zone in zones:
        alerts = zone_alerts.get(zone.zone_id, [])
        color = EVENT_COLORS[alerts[0][0]] if alerts else ZONE_COLORS[zone.zone_type]
        points = np.asarray(zone.polygon, dtype=np.int32).reshape((-1, 1, 2))
        cv2_module.polylines(annotated, [points], True, color, 3 if alerts else 2)
        x, y = (int(value) for value in zone.polygon[0])
        cv2_module.putText(annotated, f"{zone.zone_id} ({zone.zone_type})", (x, max(15, y - 6)), font, 0.45, color, 1, cv2_module.LINE_AA)
        for index, (_event_type, label) in enumerate(alerts):
            cv2_module.putText(annotated, label, (x, max(32, y + 18 + index * 18)), font, 0.5, color, 2, cv2_module.LINE_AA)

    rendered: list[tuple[TrackObservation, list[str], str]] = [
        (track, [f"track:{track.track_id}"], f"Person #{track.track_id}") for track in tracks
    ]
    for pose_track in pose_tracks:
        pose_entity = f"pose_track:{pose_track.track_id}"
        overlaps = [(bbox_iou(pose_track.bbox_xyxy, item[0].bbox_xyxy), index) for index, item in enumerate(rendered)]
        overlap, index = max(overlaps, default=(0.0, -1))
        if overlap >= 0.3:
            observation, entities, name = rendered[index]
            entities.append(pose_entity)
            if pose_entity in entity_alerts:
                rendered[index] = (pose_track, entities, name)
        else:
            rendered.append((pose_track, [pose_entity], f"Person P#{pose_track.track_id}"))

    for track, entities, name in rendered:
        alerts = []
        for entity in entities:
            alerts.extend(entity_alerts.get(entity, []))
        alerts = list(dict.fromkeys(alerts))
        color = (0, 255, 0)
        if alerts:
            color = (0, 0, 255) if any(event_type != "crowd_compression" for event_type, _label in alerts) else (0, 165, 255)
        x1, y1, x2, y2 = (int(value) for value in track.bbox_xyxy)
        cv2_module.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2_module.circle(annotated, tuple(int(value) for value in track.footpoint_xy), 4, (0, 255, 255), -1)
        cv2_module.putText(annotated, f"{name} | {track.confidence:.2f}", (x1, max(15, y1 - 5)), font, 0.45, color, 1, cv2_module.LINE_AA)
        for index, (_event_type, label) in enumerate(alerts):
            cv2_module.putText(annotated, label, (x1, min(y2 + 18 + index * 18, annotated.shape[0] - 5) if hasattr(annotated, "shape") else y2 + 18 + index * 18), font, 0.45, color, 2, cv2_module.LINE_AA)
    for index, label in enumerate(event_labels):
        cv2_module.putText(annotated, label, (10, 25 + index * 22), font, 0.6, (0, 0, 255), 2, cv2_module.LINE_AA)
    return annotated
