from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .config import CameraConfig, RuntimeConfig
from .evidence import generate_evidence_for_incident, write_metadata_only
from .fallback import load_cached_frames, load_manual_incidents, select_execution_source
from .geometry import bbox_footpoint
from .incident_export import write_incidents
from .pipeline import SafetyPipeline
from .pose import UltralyticsPoseEstimator, match_pose_scores
from .schemas import EVENT_TYPES, Incident, TrackObservation, validate_incident_payload
from .tracker import UltralyticsByteTracker
from .video_io import iter_video_frames
from .visualization import AnnotatedVideoSink, annotate_frame


@dataclass(frozen=True)
class RunResult:
    incidents: tuple[Incident, ...]
    summary: dict[str, Any]
    output_paths: dict[str, str]


def _write_json(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _run_tracking(
    runtime: RuntimeConfig,
    camera: CameraConfig,
    cache_path: Path,
    tracker: UltralyticsByteTracker | None,
    pose_estimator: UltralyticsPoseEstimator | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    tracker = tracker or UltralyticsByteTracker(
        runtime.detector_weights,
        device=runtime.device,
        confidence_threshold=runtime.person_confidence_threshold,
    )
    warnings: list[str] = []
    if runtime.pose_weights and pose_estimator is None:
        try:
            pose_estimator = UltralyticsPoseEstimator(runtime.pose_weights, device=runtime.device, confidence_threshold=runtime.person_confidence_threshold)
        except Exception as error:
            warnings.append(f"pose model disabled: {error}")
    pose_tracking_enabled = pose_estimator is not None
    pose_tracker_to_reset = pose_estimator
    frames: list[dict[str, Any]] = []
    try:
        for video_frame in iter_video_frames(
            camera.video_path,
            runtime.frame_stride,
            runtime.max_frames,
            fps_override=camera.fps_override,
        ):
            tracks = tracker.track(video_frame.raw_bgr_frame, frame_index=video_frame.frame_index, timestamp_seconds=video_frame.timestamp_seconds)
            poses = []
            pose_scores: dict[int, float] = {}
            if pose_estimator is not None:
                try:
                    poses = pose_estimator.estimate(video_frame.raw_bgr_frame)
                    pose_scores = match_pose_scores(tracks, [(pose.bbox_xyxy, pose.horizontal_score) for pose in poses if pose.horizontal_score is not None])
                except Exception as error:
                    warnings.append(f"pose inference disabled at frame {video_frame.frame_index}: {error}")
                    pose_estimator = None
            frame = {
                "frame_index": video_frame.frame_index,
                "timestamp_seconds": video_frame.timestamp_seconds,
                "fps": video_frame.fps,
                "pose_scores": {str(track_id): score for track_id, score in pose_scores.items()},
                "tracks": [
                    {
                        "track_id": item.track_id,
                        "confidence": item.confidence,
                        "bbox_xyxy": list(item.bbox_xyxy),
                        "footpoint_xy": list(item.footpoint_xy),
                    }
                    for item in tracks
                ],
            }
            if pose_tracking_enabled:
                frame["pose_tracks"] = [
                    {
                        "track_id": item.track_id,
                        "confidence": item.confidence,
                        "bbox_xyxy": list(item.bbox_xyxy),
                        "horizontal_score": item.horizontal_score,
                    }
                    for item in poses
                ]
            frames.append(frame)
    finally:
        tracker.reset()
        if pose_tracker_to_reset is not None:
            pose_tracker_to_reset.reset()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text("".join(json.dumps(frame, sort_keys=True) + "\n" for frame in frames), encoding="utf-8")
    return frames, warnings


def _cached_observations(raw_items: list[dict[str, Any]], frame_index: int, timestamp_seconds: float) -> list[TrackObservation]:
    observations = []
    for raw in raw_items:
        bbox = tuple(float(value) for value in raw["bbox_xyxy"])
        observations.append(
            TrackObservation(
                frame_index,
                timestamp_seconds,
                int(raw["track_id"]),
                float(raw.get("confidence", 0.0)),
                bbox,
                bbox_footpoint(bbox),
                max(0.0, bbox[2] - bbox[0]),
                max(0.0, bbox[3] - bbox[1]),
            )
        )
    return observations


def _render_annotated_video(camera: CameraConfig, frames: list[dict[str, Any]], incidents: list[Incident], annotated_path: Path) -> None:
    records = {int(frame["frame_index"]): frame for frame in frames}
    last_cached_frame = max(records, default=-1)
    last_record: dict[str, Any] = {}
    sink: AnnotatedVideoSink | None = None
    try:
        for video_frame in iter_video_frames(camera.video_path, fps_override=camera.fps_override):
            if video_frame.frame_index > last_cached_frame:
                break
            last_record = records.get(video_frame.frame_index, last_record)
            record = last_record
            tracks = _cached_observations(record.get("tracks", []), video_frame.frame_index, video_frame.timestamp_seconds)
            pose_tracks = _cached_observations(record.get("pose_tracks", []), video_frame.frame_index, video_frame.timestamp_seconds)
            sink = sink or AnnotatedVideoSink(annotated_path, fps=video_frame.fps)
            sink.write(
                annotate_frame(
                    video_frame.raw_bgr_frame,
                    camera.zones,
                    tracks,
                    pose_tracks=pose_tracks,
                    incidents=incidents,
                    timestamp_seconds=video_frame.timestamp_seconds,
                )
            )
    finally:
        if sink is not None:
            sink.close()


def run_pipeline(
    runtime: RuntimeConfig,
    camera: CameraConfig,
    event_rules: dict[str, dict[str, float | bool]],
    *,
    output_root: str | Path = "outputs",
    cache_path: str | Path | None = None,
    manual_path: str | Path | None = None,
    tracker: UltralyticsByteTracker | None = None,
    pose_estimator: UltralyticsPoseEstimator | None = None,
    evidence_generator: Any = None,
) -> RunResult:
    started = time.perf_counter()
    mode = select_execution_source(runtime.execution_mode)
    output_root = Path(output_root)
    video_id = Path(camera.video_path).stem
    default_cache = output_root / "frame-events" / f"{video_id}_tracks.jsonl"
    annotated_path = output_root / "annotated-videos" / f"{video_id}_annotated.mp4"
    frames: list[dict[str, Any]] = []
    warnings: list[str] = []

    if mode == "full_ai":
        frames, warnings = _run_tracking(runtime, camera, default_cache, tracker, pose_estimator)
        incidents = SafetyPipeline(camera, event_rules, source_mode=mode, evidence_root=output_root / "incidents").process_cached_frames(frames)
        if runtime.save_annotated_video:
            try:
                _render_annotated_video(camera, frames, incidents, annotated_path)
            except Exception as error:
                warnings.append(f"annotated video disabled: {error}")
        evidence_generator = evidence_generator or generate_evidence_for_incident
        for incident in incidents:
            try:
                evidence_generator(camera, incident, frames, output_root / "incidents")
            except Exception as error:
                write_metadata_only(incident, root=output_root / "incidents")
                warnings.append(f"evidence generation failed for {incident.incident_id}: {error}")
    elif mode == "cached_ai":
        frames = load_cached_frames(cache_path or default_cache)
        incidents = SafetyPipeline(camera, event_rules, source_mode=mode, evidence_root=output_root / "incidents").process_cached_frames(frames)
    else:
        if manual_path is None:
            raise ValueError("manual_demo requires manual_path")
        payloads = load_manual_incidents(manual_path)
        incidents = []
        for payload in payloads:
            validate_incident_payload(payload)
            incident = Incident(**payload)
            if incident.source_mode != "manual_demo":
                raise ValueError("manual scenario incidents must use source_mode manual_demo")
            incidents.append(incident)

    incidents_path = output_root / "incidents.json"
    summary_path = output_root / "pipeline_summary.json"
    write_incidents(incidents, incidents_path)
    elapsed = time.perf_counter() - started
    fps = float(frames[0].get("fps", 0.0)) if frames else (camera.fps_override or 0.0)
    summary = {
        "video_id": video_id,
        "camera_id": camera.camera_id,
        "execution_mode": mode,
        "total_frames_processed": len(frames),
        "fps": fps,
        "processing_seconds": elapsed,
        "average_processing_fps": len(frames) / elapsed if elapsed > 0 else 0.0,
        "incident_counts": {event_type: sum(item.incident_type == event_type for item in incidents) for event_type in sorted(EVENT_TYPES)},
        "warnings": warnings,
    }
    _write_json(summary, summary_path)
    return RunResult(
        tuple(incidents),
        summary,
        {
            "incidents": incidents_path.as_posix(),
            "pipeline_summary": summary_path.as_posix(),
            "track_cache": (Path(cache_path) if cache_path is not None else default_cache).as_posix(),
            "annotated_video": annotated_path.as_posix() if runtime.save_annotated_video and mode == "full_ai" else None,
        },
    )
