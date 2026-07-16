from __future__ import annotations

from typing import Any

from .detector import _values
from .geometry import bbox_footpoint
from .schemas import TrackObservation


class UltralyticsByteTracker:
    def __init__(self, weights: str, *, device: str = "auto", confidence_threshold: float = 0.35, iou_threshold: float = 0.7, image_size: int = 640, model: Any = None):
        self.weights = weights
        self.device = device
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.image_size = image_size
        if model is None:
            try:
                from ultralytics import YOLO
            except ImportError as error:
                raise RuntimeError("ultralytics is required for full_ai mode") from error
            model = YOLO(weights)
        self.model = model

    def track(self, frame: Any, *, frame_index: int, timestamp_seconds: float) -> list[TrackObservation]:
        arguments = {
            "source": frame,
            "persist": True,
            "tracker": "bytetrack.yaml",
            "classes": [0],
            "conf": self.confidence_threshold,
            "iou": self.iou_threshold,
            "imgsz": self.image_size,
            "verbose": False,
        }
        if self.device != "auto":
            arguments["device"] = self.device
        results = self.model.track(**arguments)
        if not results or results[0].boxes is None or results[0].boxes.id is None:
            return []
        boxes = results[0].boxes
        observations: list[TrackObservation] = []
        for bbox, confidence, track_id in zip(_values(boxes.xyxy), _values(boxes.conf), _values(boxes.id), strict=True):
            xyxy = tuple(float(value) for value in bbox)
            observations.append(
                TrackObservation(
                    frame_index=frame_index,
                    timestamp_seconds=timestamp_seconds,
                    track_id=int(track_id),
                    confidence=float(confidence),
                    bbox_xyxy=xyxy,
                    footpoint_xy=bbox_footpoint(xyxy),
                    bbox_width=max(0.0, xyxy[2] - xyxy[0]),
                    bbox_height=max(0.0, xyxy[3] - xyxy[1]),
                )
            )
        return observations

    def reset(self) -> None:
        if hasattr(self.model, "predictor"):
            self.model.predictor = None
