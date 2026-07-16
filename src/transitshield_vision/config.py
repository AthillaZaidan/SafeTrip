from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schemas import EVENT_TYPES, ZoneConfig


EXECUTION_MODES = {"full_ai", "cached_ai", "manual_demo"}
ZONE_TYPES = {"normal", "limited_dwell", "restricted", "crowd_monitoring"}


@dataclass(frozen=True)
class RuntimeConfig:
    execution_mode: str = "cached_ai"
    device: str = "auto"
    frame_stride: int = 1
    max_frames: int | None = None
    person_confidence_threshold: float = 0.35
    detector_image_size: int = 640
    detector_weights: str = "yolo11n.pt"
    pose_weights: str | None = "yolo11n-pose.pt"
    save_annotated_video: bool = True
    random_seed: int = 42


@dataclass(frozen=True)
class CameraConfig:
    camera_id: str
    name: str
    video_path: str
    fps_override: float | None
    enabled_events: tuple[str, ...]
    zones: tuple[ZoneConfig, ...]


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_runtime_config(data: dict[str, Any]) -> RuntimeConfig:
    config = RuntimeConfig(**data)
    if config.execution_mode not in EXECUTION_MODES:
        raise ValueError(f"unsupported execution_mode: {config.execution_mode}")
    if config.frame_stride < 1:
        raise ValueError("frame_stride must be at least 1")
    if config.max_frames is not None and config.max_frames < 1:
        raise ValueError("max_frames must be null or positive")
    if not 0 <= config.person_confidence_threshold <= 1:
        raise ValueError("person_confidence_threshold must be between 0 and 1")
    if config.detector_image_size < 1:
        raise ValueError("detector_image_size must be positive")
    return config


def _point(value: Any, field: str) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{field} must contain x and y")
    return float(value[0]), float(value[1])


def parse_camera_config(data: dict[str, Any], *, require_video: bool = True) -> CameraConfig:
    camera_id = str(data.get("camera_id", "")).strip()
    video_path = str(data.get("video_path", "")).strip()
    if not camera_id:
        raise ValueError("camera_id is required")
    if not video_path:
        raise ValueError("video_path is required")
    if require_video and not Path(video_path).is_file():
        raise ValueError(f"video_path does not exist: {video_path}")
    enabled_events = tuple(data.get("enabled_events", EVENT_TYPES))
    if not enabled_events or len(set(enabled_events)) != len(enabled_events) or not set(enabled_events) <= set(EVENT_TYPES):
        raise ValueError(f"enabled_events must be unique values from {list(EVENT_TYPES)}")

    zones: list[ZoneConfig] = []
    seen: set[str] = set()
    for raw in data.get("zones", []):
        zone_id = str(raw.get("zone_id", "")).strip()
        zone_type = raw.get("zone_type")
        polygon = tuple(_point(point, "polygon point") for point in raw.get("polygon", []))
        if not zone_id or zone_id in seen:
            raise ValueError("zone_id must be present and unique")
        if zone_type not in ZONE_TYPES:
            raise ValueError(f"unsupported zone_type: {zone_type}")
        if len(polygon) < 3:
            raise ValueError(f"polygon for {zone_id} must have at least three points")
        capacity = raw.get("capacity")
        if zone_type == "crowd_monitoring" and (not isinstance(capacity, int) or capacity < 1):
            raise ValueError("crowd_monitoring zone capacity must be positive")
        danger = raw.get("danger_direction")
        zones.append(
            ZoneConfig(
                zone_id=zone_id,
                camera_id=camera_id,
                zone_type=zone_type,
                polygon=polygon,
                capacity=capacity,
                risk_multiplier=float(raw.get("risk_multiplier", 1.0)),
                danger_direction=None if danger is None else _point(danger, "danger_direction"),
            )
        )
        seen.add(zone_id)
    if not zones:
        raise ValueError("at least one zone is required")
    fps_override = data.get("fps_override")
    if fps_override is not None and float(fps_override) <= 0:
        raise ValueError("fps_override must be positive")
    return CameraConfig(
        camera_id=camera_id,
        name=str(data.get("name", camera_id)),
        video_path=video_path,
        fps_override=None if fps_override is None else float(fps_override),
        enabled_events=enabled_events,
        zones=tuple(zones),
    )


def parse_event_rules(data: dict[str, Any]) -> dict[str, dict[str, float | bool]]:
    if set(data) != set(EVENT_TYPES):
        raise ValueError(f"event rules must contain exactly {sorted(EVENT_TYPES)}")
    parsed: dict[str, dict[str, float | bool]] = {}
    for event_type, raw in data.items():
        values: dict[str, float | bool] = {}
        for key, value in raw.items():
            if isinstance(value, bool):
                values[key] = value
            elif isinstance(value, (int, float)):
                if float(value) < 0:
                    raise ValueError(f"{event_type}.{key} cannot be negative")
                values[key] = float(value)
            else:
                raise ValueError(f"{event_type}.{key} must be numeric or boolean")
        for required in ("minimum_duration_seconds", "cooldown_seconds"):
            if required not in values:
                raise ValueError(f"{event_type}.{required} is required")
        parsed[event_type] = values
    return parsed


def set_deterministic_seed(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
