from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .geometry import bbox_footpoint
from .schemas import Incident, TrackObservation


@dataclass(frozen=True)
class EvidenceFrame:
    timestamp_seconds: float
    raw_frame: Any
    annotated_frame: Any


def evidence_paths(incident_id: str, root: str | Path = "outputs/incidents") -> dict[str, str]:
    base = Path(root) / incident_id
    return {
        "snapshot_raw": (base / "snapshot_raw.jpg").as_posix(),
        "snapshot_annotated": (base / "snapshot_annotated.jpg").as_posix(),
        "clip": (base / "evidence.mp4").as_posix(),
        "metadata": (base / "metadata.json").as_posix(),
    }


def ensure_evidence_directory(incident_id: str, root: str | Path = "outputs/incidents") -> Path:
    path = Path(root) / incident_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_evidence(
    incident: Incident,
    frames: Sequence[EvidenceFrame],
    *,
    fps: float,
    root: str | Path = "outputs/incidents",
    cv2_module: Any = None,
) -> dict[str, str]:
    if not frames:
        raise ValueError("at least one evidence frame is required")
    if fps <= 0:
        raise ValueError("evidence FPS must be positive")
    if cv2_module is None:
        try:
            import cv2 as cv2_module
        except ImportError as error:
            raise RuntimeError("opencv-python is required to write evidence") from error

    directory = ensure_evidence_directory(incident.incident_id, root)
    paths = {
        "snapshot_raw": (directory / "snapshot_raw.jpg").as_posix(),
        "snapshot_annotated": (directory / "snapshot_annotated.jpg").as_posix(),
        "clip": (directory / "evidence.mp4").as_posix(),
        "metadata": (directory / "metadata.json").as_posix(),
    }
    incident.evidence = paths
    Path(paths["metadata"]).write_text(json.dumps(incident.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    snapshot = min(frames, key=lambda frame: abs(frame.timestamp_seconds - incident.timestamp_detected_seconds))
    if not cv2_module.imwrite(paths["snapshot_raw"], snapshot.raw_frame):
        raise RuntimeError(f"failed to write raw evidence snapshot: {paths['snapshot_raw']}")
    if not cv2_module.imwrite(paths["snapshot_annotated"], snapshot.annotated_frame):
        raise RuntimeError(f"failed to write annotated evidence snapshot: {paths['snapshot_annotated']}")

    height, width = frames[0].annotated_frame.shape[:2]
    writer = cv2_module.VideoWriter(paths["clip"], cv2_module.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"failed to open evidence video writer: {paths['clip']}")
    try:
        for frame in frames:
            writer.write(frame.annotated_frame)
    finally:
        writer.release()
    return paths


def write_metadata_only(incident: Incident, *, root: str | Path = "outputs/incidents") -> dict[str, str]:
    directory = ensure_evidence_directory(incident.incident_id, root)
    paths = {
        "snapshot_raw": (directory / "snapshot_raw.jpg").as_posix(),
        "snapshot_annotated": (directory / "snapshot_annotated.jpg").as_posix(),
        "clip": (directory / "evidence.mp4").as_posix(),
        "metadata": (directory / "metadata.json").as_posix(),
    }
    incident.evidence = paths
    Path(paths["metadata"]).write_text(json.dumps(incident.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return paths


def generate_evidence_for_incident(camera: Any, incident: Incident, cached_frames: Sequence[dict[str, Any]], root: str | Path) -> dict[str, str]:
    from .video_io import iter_video_frames
    from .visualization import annotate_frame

    # ponytail: re-read the short demo video per incident; batch extraction if incident volume matters.
    records = {int(frame["frame_index"]): frame for frame in cached_frames}
    start = max(0.0, incident.timestamp_start_seconds - 5.0)
    end = (incident.timestamp_end_seconds or incident.timestamp_detected_seconds) + 5.0
    evidence_frames: list[EvidenceFrame] = []
    fps = camera.fps_override or 0.0
    for video_frame in iter_video_frames(camera.video_path, fps_override=camera.fps_override):
        if video_frame.timestamp_seconds < start:
            continue
        if video_frame.timestamp_seconds > end:
            break
        fps = video_frame.fps
        record = records.get(video_frame.frame_index, {"tracks": []})
        tracks = []
        for raw in record.get("tracks", []):
            bbox = tuple(float(value) for value in raw["bbox_xyxy"])
            tracks.append(
                TrackObservation(
                    video_frame.frame_index,
                    video_frame.timestamp_seconds,
                    int(raw["track_id"]),
                    float(raw.get("confidence", 0.0)),
                    bbox,
                    bbox_footpoint(bbox),
                    max(0.0, bbox[2] - bbox[0]),
                    max(0.0, bbox[3] - bbox[1]),
                )
            )
        raw_frame = video_frame.raw_bgr_frame.copy()
        annotated = annotate_frame(video_frame.raw_bgr_frame, camera.zones, tracks, [incident.incident_type])
        evidence_frames.append(EvidenceFrame(video_frame.timestamp_seconds, raw_frame, annotated))
    return write_evidence(incident, evidence_frames, fps=fps, root=root)
