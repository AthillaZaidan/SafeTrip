from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence

from .detector import _values
from .schemas import TrackObservation


Keypoint = tuple[float, float, float]


@dataclass(frozen=True)
class PoseObservation:
    track_id: int
    bbox_xyxy: tuple[float, float, float, float]
    keypoints: tuple[Keypoint, ...]
    confidence: float
    horizontal_score: float | None


def body_horizontal_score(keypoints: Sequence[Keypoint], minimum_visibility: float = 0.25) -> float | None:
    if len(keypoints) < 13:
        return None
    required = [keypoints[index] for index in (5, 6, 11, 12)]
    if any(point[2] < minimum_visibility for point in required):
        return None
    shoulder = ((required[0][0] + required[1][0]) / 2, (required[0][1] + required[1][1]) / 2)
    hip = ((required[2][0] + required[3][0]) / 2, (required[2][1] + required[3][1]) / 2)
    dx, dy = hip[0] - shoulder[0], hip[1] - shoulder[1]
    length = math.hypot(dx, dy)
    return None if length == 0 else abs(dx) / length


def bbox_iou(left: Sequence[float], right: Sequence[float]) -> float:
    intersection_width = max(0.0, min(left[2], right[2]) - max(left[0], right[0]))
    intersection_height = max(0.0, min(left[3], right[3]) - max(left[1], right[1]))
    intersection = intersection_width * intersection_height
    left_area = max(0.0, left[2] - left[0]) * max(0.0, left[3] - left[1])
    right_area = max(0.0, right[2] - right[0]) * max(0.0, right[3] - right[1])
    return intersection / max(left_area + right_area - intersection, 1e-9)


def match_pose_scores(tracks: Sequence[TrackObservation], poses: Sequence[tuple[Sequence[float], float]], minimum_iou: float = 0.3) -> dict[int, float]:
    matched: dict[int, float] = {}
    for track in tracks:
        candidates = [(bbox_iou(track.bbox_xyxy, bbox), score) for bbox, score in poses]
        if candidates:
            overlap, score = max(candidates, key=lambda item: item[0])
            if overlap >= minimum_iou:
                matched[track.track_id] = score
    return matched


class UltralyticsPoseEstimator:
    def __init__(self, weights: str, *, device: str = "auto", confidence_threshold: float = 0.35, model: Any = None):
        self.weights = weights
        self.device = device
        self.confidence_threshold = confidence_threshold
        if model is None:
            try:
                from ultralytics import YOLO
            except ImportError as error:
                raise RuntimeError("ultralytics is required for pose inference") from error
            model = YOLO(weights)
        self.model = model

    def estimate(self, frame: Any) -> list[PoseObservation]:
        arguments = {
            "source": frame,
            "persist": True,
            "tracker": "bytetrack.yaml",
            "conf": self.confidence_threshold,
            "verbose": False,
        }
        if self.device != "auto":
            arguments["device"] = self.device
        results = self.model.track(**arguments)
        if not results or results[0].boxes is None or results[0].boxes.id is None or results[0].keypoints is None:
            return []
        boxes = _values(results[0].boxes.xyxy)
        confidences = _values(results[0].boxes.conf)
        track_ids = _values(results[0].boxes.id)
        points = _values(results[0].keypoints.data)
        observations: list[PoseObservation] = []
        for track_id, bbox, confidence, raw_points in zip(track_ids, boxes, confidences, points, strict=True):
            keypoints = tuple((float(point[0]), float(point[1]), float(point[2]) if len(point) > 2 else 1.0) for point in raw_points)
            observations.append(PoseObservation(int(track_id), tuple(float(value) for value in bbox), keypoints, float(confidence), body_horizontal_score(keypoints)))
        return observations

    def reset(self) -> None:
        if hasattr(self.model, "predictor"):
            self.model.predictor = None
