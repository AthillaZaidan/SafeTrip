import datetime
import json
from pathlib import Path

import pytest

from server.app.schemas.investigations import VLMResult
from server.app.schemas.reports import SearchAttributes
from server.app.services.clip_retrieval import load_clip_library, retrieve_candidates


JAKARTA = datetime.timezone(datetime.timedelta(hours=7))


def _timestamp(minute: int, second: int = 0) -> datetime.datetime:
    return datetime.datetime(2026, 7, 17, 17, minute, second, tzinfo=JAKARTA)


def _clip(
    clip_id: str,
    *,
    camera_id: str = "CAM_A",
    location: str = "Exit D Link",
    minute: int = 10,
    upper_clothing: str = "grey jacket",
    accessories: list[str] | None = None,
    direction: str = "toward Exit D",
    event: str = "running",
) -> dict:
    return {
        "clip_id": clip_id,
        "camera_id": camera_id,
        "location": location,
        "start_time": _timestamp(minute).isoformat(),
        "end_time": _timestamp(minute, 15).isoformat(),
        "path": f"data/investigation-videos/{clip_id}.mp4",
        "attributes": {
            "upper_clothing": upper_clothing,
            "lower_clothing": "dark trousers",
            "accessories": accessories or ["black backpack"],
            "direction": direction,
            "event": event,
        },
        "cached_vlm_result": {
            "supported_attributes": ["grey jacket"],
            "contradicted_attributes": [],
            "uncertainties": [],
            "relevant_start_seconds": 1.0,
            "relevant_end_seconds": 4.0,
            "match_recommendation": "likely_match",
            "source": "cached",
        },
    }


def _write_library(tmp_path: Path, clips: list[dict]) -> Path:
    path = tmp_path / "library.json"
    path.write_text(json.dumps(clips), encoding="utf-8")
    return path


def test_load_clip_library_validates_required_fields(tmp_path):
    path = _write_library(tmp_path, [{"clip_id": "CLIP-1"}])

    with pytest.raises(ValueError, match="missing required fields"):
        load_clip_library(path)


def test_load_clip_library_rejects_duplicate_ids(tmp_path):
    path = _write_library(tmp_path, [_clip("CLIP-1"), _clip("CLIP-1")])

    with pytest.raises(ValueError, match="duplicate clip_id"):
        load_clip_library(path)


def test_load_clip_library_requires_ordered_timestamps(tmp_path):
    clip = _clip("CLIP-1")
    clip["end_time"] = _timestamp(9).isoformat()
    path = _write_library(tmp_path, [clip])

    with pytest.raises(ValueError, match="end_time"):
        load_clip_library(path)


def test_load_clip_library_does_not_require_local_media(tmp_path):
    path = _write_library(tmp_path, [_clip("CLIP-MISSING")])

    assert load_clip_library(path)[0]["path"].endswith("CLIP-MISSING.mp4")


def test_load_clip_library_rejects_non_list_accessories(tmp_path):
    clip = _clip("CLIP-1")
    clip["attributes"]["accessories"] = None
    path = _write_library(tmp_path, [clip])

    with pytest.raises(ValueError, match="accessories"):
        load_clip_library(path)


def test_load_clip_library_rejects_invalid_cached_vlm_enum(tmp_path):
    clip = _clip("CLIP-1")
    clip["cached_vlm_result"]["match_recommendation"] = "definite_match"
    path = _write_library(tmp_path, [clip])

    with pytest.raises(ValueError, match="cached_vlm_result"):
        load_clip_library(path)


def test_retrieval_hard_filters_time_window_and_camera_ids():
    clips = [
        _clip("IN-WINDOW", camera_id="CAM_A", minute=10),
        _clip("WRONG-CAMERA", camera_id="CAM_B", minute=10),
        _clip("OUTSIDE-TIME", camera_id="CAM_A", minute=12),
    ]
    attributes = SearchAttributes(
        time_window_start=_timestamp(9, 30),
        time_window_end=_timestamp(11),
        camera_ids=["CAM_A"],
        upper_clothing="grey jacket",
    )

    assert [item["clip_id"] for item in retrieve_candidates(attributes, clips)] == [
        "IN-WINDOW"
    ]


def test_retrieval_treats_naive_confirmed_times_as_library_local_time():
    attributes = SearchAttributes(
        time_window_start=datetime.datetime(2026, 7, 17, 17, 9, 30),
        time_window_end=datetime.datetime(2026, 7, 17, 17, 11),
    )

    results = retrieve_candidates(attributes, [_clip("LOCAL-TIME", minute=10)])

    assert [item["clip_id"] for item in results] == ["LOCAL-TIME"]


def test_retrieval_ranks_full_match_above_one_attribute_distractors():
    clips = [
        _clip("TARGET"),
        _clip("WRONG-UPPER", upper_clothing="blue jacket"),
        _clip("WRONG-BAG", accessories=["red backpack"]),
        _clip("WRONG-DIRECTION", direction="away from Exit D"),
        _clip("WRONG-EVENT", event="walking"),
        _clip("WRONG-LOCATION", location="Lantai 2 Mezzanine"),
    ]
    attributes = SearchAttributes(
        location="Exit D Link",
        upper_clothing="grey jacket",
        accessories=["black backpack"],
        direction="toward Exit D",
        event="running",
    )

    results = retrieve_candidates(attributes, clips)

    assert results[0]["clip_id"] == "TARGET"
    assert results[0]["metadata_score"] == 1.0
    assert all(results[0]["metadata_score"] > item["metadata_score"] for item in results[1:])
    assert set(results[0]["matched_attributes"]) == {
        "location",
        "upper_clothing",
        "accessories",
        "direction",
        "event",
    }


def test_retrieval_returns_five_and_uses_clip_id_as_final_tie_breaker():
    clips = [_clip(f"CLIP-{number:02d}") for number in range(7, 0, -1)]

    results = retrieve_candidates(SearchAttributes(upper_clothing="grey jacket"), clips)

    assert [item["clip_id"] for item in results] == [
        "CLIP-01",
        "CLIP-02",
        "CLIP-03",
        "CLIP-04",
        "CLIP-05",
    ]


def test_tracked_tanah_abang_library_is_complete_and_deterministic():
    manifest_path = Path("configs/investigation_library.json")
    clips = load_clip_library(manifest_path)

    assert len(clips) == 9
    assert len({clip["clip_id"] for clip in clips}) == 9
    assert [clip["clip_id"] for clip in clips] == [
        f"CLIP-TA-{number:03d}" for number in range(1, 10)
    ]
    assert [clip["path"] for clip in clips] == [
        f"data/investigation-videos/clip-ta-{number:03d}.mp4"
        for number in range(1, 10)
    ]
    assert all(clip["path"].startswith("data/investigation-videos/") for clip in clips)
    cached_fields = {
        "supported_attributes",
        "contradicted_attributes",
        "uncertainties",
        "relevant_start_seconds",
        "relevant_end_seconds",
        "match_recommendation",
        "source",
    }
    assert all(set(clip["cached_vlm_result"]) == cached_fields for clip in clips)
    assert all(
        VLMResult.model_validate(clip["cached_vlm_result"]).source == "cached"
        for clip in clips
    )
    assert {clip["camera_id"] for clip in clips} == {
        "CAM_TA_LEVEL_1_CONCOURSE",
        "CAM_TA_LEVEL_2_MEZZANINE",
        "CAM_TA_EXIT_D_LINK",
    }
    assert {clip["location"] for clip in clips} == {
        "Lantai 1 Concourse",
        "Lantai 2 Mezzanine",
        "Exit D Link",
    }

    target_attributes = {
        "upper_clothing": "grey jacket",
        "lower_clothing": "dark trousers",
        "accessories": ["black backpack"],
        "direction": "toward Exit D",
        "event": "running",
    }
    targets = [clip for clip in clips if clip["attributes"] == target_attributes]
    assert len(targets) == 3
    assert [clip["camera_id"] for clip in targets] == [
        "CAM_TA_LEVEL_1_CONCOURSE",
        "CAM_TA_LEVEL_2_MEZZANINE",
        "CAM_TA_EXIT_D_LINK",
    ]
    assert [clip["start_time"] for clip in targets] == sorted(
        clip["start_time"] for clip in targets
    )
    variation_types = set()
    for target in targets:
        distractors = [
            clip
            for clip in clips
            if clip["camera_id"] == target["camera_id"] and clip is not target
        ]
        assert len(distractors) == 2
        for distractor in distractors:
            target_values = {
                "location": target["location"],
                **target["attributes"],
            }
            distractor_values = {
                "location": distractor["location"],
                **distractor["attributes"],
            }
            changed_fields = {
                field
                for field in target_values
                if target_values[field] != distractor_values[field]
            }
            assert len(changed_fields) == 1
            variation_types.update(changed_fields)
    assert variation_types == {"upper_clothing", "accessories", "direction"}

    report = SearchAttributes(
        time_window_start=_timestamp(9),
        time_window_end=_timestamp(11, 59),
        upper_clothing="grey jacket",
        accessories=["black backpack"],
        direction="toward Exit D",
        event="running",
    )
    ranked = retrieve_candidates(report, clips)

    assert [item["clip_id"] for item in ranked[:3]] == [
        "CLIP-TA-001",
        "CLIP-TA-004",
        "CLIP-TA-007",
    ]
