from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any, Iterable

from .schemas import EVENT_TYPES


@dataclass(frozen=True)
class GroundTruthEvent:
    event_type: str
    camera_id: str
    zone_id: str | None
    start_seconds: float
    end_seconds: float
    track_id: int | None = None


def temporal_iou(pred_start: float, pred_end: float, gt_start: float, gt_end: float, epsilon: float = 1e-9) -> float:
    intersection = max(0.0, min(pred_end, gt_end) - max(pred_start, gt_start))
    union = max(pred_end, gt_end) - min(pred_start, gt_start)
    return intersection / max(union, epsilon)


def evaluate_events(predictions: Iterable[dict[str, Any]], ground_truth: Iterable[GroundTruthEvent], *, duration_hours: float, iou_threshold: float = 0.1) -> dict[str, Any]:
    predictions = list(predictions)
    truth = list(ground_truth)
    used_truth: set[int] = set()
    true_positives = 0
    latencies: list[float] = []

    for prediction in predictions:
        best_index = None
        best_iou = 0.0
        pred_end = prediction.get("timestamp_end_seconds")
        if pred_end is None:
            pred_end = prediction["timestamp_detected_seconds"]
        for index, expected in enumerate(truth):
            if index in used_truth:
                continue
            if prediction["incident_type"] != expected.event_type or prediction["camera_id"] != expected.camera_id:
                continue
            if expected.zone_id is not None and prediction.get("zone_id") != expected.zone_id:
                continue
            overlap = temporal_iou(prediction["timestamp_start_seconds"], pred_end, expected.start_seconds, expected.end_seconds)
            if overlap >= iou_threshold and overlap > best_iou:
                best_iou = overlap
                best_index = index
        if best_index is not None:
            used_truth.add(best_index)
            true_positives += 1
            latencies.append(prediction["timestamp_detected_seconds"] - truth[best_index].start_seconds)

    false_alerts = len(predictions) - true_positives
    missed = len(truth) - true_positives
    precision = true_positives / len(predictions) if predictions else 0.0
    recall = true_positives / len(truth) if truth else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positives": true_positives,
        "false_alerts": false_alerts,
        "missed_events": missed,
        "event_precision": precision,
        "event_recall": recall,
        "event_f1": f1,
        "average_detection_latency_seconds": mean(latencies) if latencies else None,
        "false_alerts_per_camera_hour": false_alerts / duration_hours if duration_hours > 0 else None,
        "duplicate_alert_rate": false_alerts / len(predictions) if predictions else 0.0,
    }


def evaluate_by_event_type(predictions: Iterable[dict[str, Any]], ground_truth: Iterable[GroundTruthEvent], *, duration_hours: float, iou_threshold: float = 0.1) -> dict[str, dict[str, Any]]:
    predictions = list(predictions)
    ground_truth = list(ground_truth)
    return {
        event_type: evaluate_events(
            [item for item in predictions if item.get("incident_type") == event_type],
            [item for item in ground_truth if item.event_type == event_type],
            duration_hours=duration_hours,
            iou_threshold=iou_threshold,
        )
        for event_type in sorted(EVENT_TYPES)
    }
