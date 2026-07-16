from __future__ import annotations

from typing import Any

from .schemas import EVENT_TYPES


def validate_annotation_document(document: dict[str, Any]) -> dict[str, Any]:
    for field in ("video_id", "camera_id", "fps", "events"):
        if field not in document:
            raise ValueError(f"annotation field missing: {field}")
    if float(document["fps"]) <= 0:
        raise ValueError("annotation fps must be positive")
    if not isinstance(document["events"], list):
        raise ValueError("annotation events must be a list")
    for event in document["events"]:
        if event.get("event_type") not in EVENT_TYPES:
            raise ValueError(f"unknown event_type: {event.get('event_type')}")
        start = event.get("start_frame")
        end = event.get("end_frame")
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start:
            raise ValueError(f"invalid frame range: {start}..{end}")
    return document
