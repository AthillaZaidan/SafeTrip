from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .schemas import TrackObservation, ZoneConfig


ZONE_COLORS = {
    "normal": (90, 180, 90),
    "limited_dwell": (0, 200, 255),
    "restricted": (0, 0, 255),
    "crowd_monitoring": (255, 170, 0),
    "track_area": (180, 0, 255),
}


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
    for zone in zones:
        color = ZONE_COLORS[zone.zone_type]
        points = np.asarray(zone.polygon, dtype=np.int32).reshape((-1, 1, 2))
        cv2_module.polylines(annotated, [points], True, color, 2)
        x, y = (int(value) for value in zone.polygon[0])
        cv2_module.putText(annotated, f"{zone.zone_id} ({zone.zone_type})", (x, max(15, y - 6)), font, 0.45, color, 1, cv2_module.LINE_AA)
    for track in tracks:
        x1, y1, x2, y2 = (int(value) for value in track.bbox_xyxy)
        cv2_module.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2_module.circle(annotated, tuple(int(value) for value in track.footpoint_xy), 4, (0, 255, 255), -1)
        cv2_module.putText(annotated, f"track:{track.track_id} {track.confidence:.2f}", (x1, max(15, y1 - 5)), font, 0.45, (0, 255, 0), 1, cv2_module.LINE_AA)
    for index, label in enumerate(event_labels):
        cv2_module.putText(annotated, label, (10, 25 + index * 22), font, 0.6, (0, 0, 255), 2, cv2_module.LINE_AA)
    return annotated
