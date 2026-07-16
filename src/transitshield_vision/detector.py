from __future__ import annotations

from typing import Any

from .schemas import Detection


def _values(value: Any) -> list[Any]:
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "tolist"):
        value = value.tolist()
    return list(value)


class UltralyticsPersonDetector:
    def __init__(self, weights: str, *, device: str = "auto", confidence_threshold: float = 0.35, iou_threshold: float = 0.7, model: Any = None):
        self.weights = weights
        self.device = device
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        if model is None:
            try:
                from ultralytics import YOLO
            except ImportError as error:
                raise RuntimeError("ultralytics is required for full_ai mode") from error
            model = YOLO(weights)
        self.model = model

    def detect(self, frame: Any, *, frame_index: int, timestamp_seconds: float) -> list[Detection]:
        arguments = {
            "source": frame,
            "classes": [0],
            "conf": self.confidence_threshold,
            "iou": self.iou_threshold,
            "verbose": False,
        }
        if self.device != "auto":
            arguments["device"] = self.device
        results = self.model.predict(**arguments)
        if not results or results[0].boxes is None:
            return []
        boxes = results[0].boxes
        return [
            Detection(frame_index, timestamp_seconds, int(class_id), "person", float(confidence), tuple(float(value) for value in bbox))
            for bbox, confidence, class_id in zip(_values(boxes.xyxy), _values(boxes.conf), _values(boxes.cls), strict=True)
        ]
