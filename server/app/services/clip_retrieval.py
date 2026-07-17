from __future__ import annotations

import datetime
import json
from pathlib import Path

from pydantic import ValidationError

from ..schemas.investigations import VLMResult
from ..schemas.reports import SearchAttributes


REQUIRED_CLIP_FIELDS = {
    "clip_id",
    "camera_id",
    "location",
    "start_time",
    "end_time",
    "path",
    "attributes",
    "cached_vlm_result",
}
REQUIRED_ATTRIBUTE_FIELDS = {
    "upper_clothing",
    "lower_clothing",
    "accessories",
    "direction",
    "event",
}
MATCH_WEIGHTS = {
    "location": 0.20,
    "upper_clothing": 0.30,
    "accessories": 0.25,
    "direction": 0.15,
    "event": 0.10,
}


def _parse_timestamp(value: object, field: str, clip_id: str) -> datetime.datetime:
    if not isinstance(value, str):
        raise ValueError(f"clip {clip_id!r} has invalid {field}")
    try:
        return datetime.datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"clip {clip_id!r} has invalid {field}") from error


def load_clip_library(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as file:
        clips = json.load(file)

    if not isinstance(clips, list):
        raise ValueError("clip library must be a JSON array")

    seen_ids: set[str] = set()
    for index, clip in enumerate(clips):
        if not isinstance(clip, dict):
            raise ValueError(f"clip at index {index} must be an object")
        missing = REQUIRED_CLIP_FIELDS - clip.keys()
        if missing:
            raise ValueError(f"clip at index {index} missing required fields: {sorted(missing)}")

        clip_id = clip["clip_id"]
        if not isinstance(clip_id, str) or not clip_id:
            raise ValueError(f"clip at index {index} has invalid clip_id")
        if clip_id in seen_ids:
            raise ValueError(f"duplicate clip_id: {clip_id}")
        seen_ids.add(clip_id)

        for field in ("camera_id", "location", "path"):
            if not isinstance(clip[field], str) or not clip[field].strip():
                raise ValueError(f"clip {clip_id!r} has invalid {field}")

        if not isinstance(clip["attributes"], dict):
            raise ValueError(f"clip {clip_id!r} attributes must be an object")
        missing_attributes = REQUIRED_ATTRIBUTE_FIELDS - clip["attributes"].keys()
        if missing_attributes:
            raise ValueError(
                f"clip {clip_id!r} attributes missing required fields: {sorted(missing_attributes)}"
            )

        for field in ("upper_clothing", "lower_clothing", "direction", "event"):
            value = clip["attributes"][field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"clip {clip_id!r} has invalid {field}")
        accessories = clip["attributes"]["accessories"]
        if not isinstance(accessories, list) or not all(
            isinstance(value, str) and value.strip() for value in accessories
        ):
            raise ValueError(f"clip {clip_id!r} has invalid accessories")

        if not isinstance(clip["cached_vlm_result"], dict):
            raise ValueError(f"clip {clip_id!r} cached_vlm_result must be an object")
        try:
            cached_result = VLMResult.model_validate(clip["cached_vlm_result"])
        except ValidationError as error:
            raise ValueError(f"clip {clip_id!r} has invalid cached_vlm_result") from error
        if cached_result.source != "cached":
            raise ValueError(f"clip {clip_id!r} cached_vlm_result must use source 'cached'")

        start = _parse_timestamp(clip["start_time"], "start_time", clip_id)
        end = _parse_timestamp(clip["end_time"], "end_time", clip_id)
        try:
            reversed_range = end < start
        except TypeError as error:
            raise ValueError(f"clip {clip_id!r} timestamps must use matching timezones") from error
        if reversed_range:
            raise ValueError(f"clip {clip_id!r} end_time must not be before start_time")

    return clips


def _normalized(value: object) -> str:
    return " ".join(str(value).casefold().split())


def _attribute_matches(field: str, expected: object, actual: object) -> bool:
    if field == "accessories":
        actual_values = {_normalized(value) for value in actual}
        return all(_normalized(value) in actual_values for value in expected)
    return _normalized(expected) == _normalized(actual)


def _align_timestamp(
    value: datetime.datetime,
    reference: datetime.datetime | None,
) -> datetime.datetime:
    if reference is None or (value.utcoffset() is None) == (reference.utcoffset() is None):
        return value
    if reference.utcoffset() is None:
        return value.replace(tzinfo=None)
    return value.replace(tzinfo=reference.tzinfo)


def retrieve_candidates(
    attributes: SearchAttributes,
    clips: list[dict],
    limit: int = 5,
) -> list[dict]:
    results = []
    for clip in clips:
        start = datetime.datetime.fromisoformat(clip["start_time"])
        end = datetime.datetime.fromisoformat(clip["end_time"])
        reference = attributes.time_window_start or attributes.time_window_end
        start = _align_timestamp(start, reference)
        end = _align_timestamp(end, reference)
        if attributes.time_window_start and end < attributes.time_window_start:
            continue
        if attributes.time_window_end and start > attributes.time_window_end:
            continue
        if attributes.camera_ids and clip["camera_id"] not in attributes.camera_ids:
            continue

        searchable = {"location": clip["location"], **clip["attributes"]}
        requested = {
            field: getattr(attributes, field)
            for field in MATCH_WEIGHTS
            if getattr(attributes, field)
        }
        matched = [
            field
            for field, expected in requested.items()
            if _attribute_matches(field, expected, searchable[field])
        ]
        denominator = sum(MATCH_WEIGHTS[field] for field in requested)
        score = (
            sum(MATCH_WEIGHTS[field] for field in matched) / denominator
            if denominator
            else 0.0
        )
        results.append(
            {
                **clip,
                "metadata_score": round(score, 6),
                "matched_attributes": matched,
            }
        )

    return sorted(results, key=lambda clip: (-clip["metadata_score"], clip["clip_id"]))[
        : max(0, limit)
    ]
