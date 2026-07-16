from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MODES = {"full_ai", "cached_ai", "manual_demo"}


def select_execution_source(execution_mode: str) -> str:
    if execution_mode not in MODES:
        raise ValueError(f"unsupported execution_mode: {execution_mode}")
    return execution_mode


def load_cached_frames(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"required cached output is missing: {source}")
    frames = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    for frame in frames:
        if not {"frame_index", "timestamp_seconds", "tracks"} <= frame.keys():
            raise ValueError("cached frame requires frame_index, timestamp_seconds, and tracks")
    return frames


def load_manual_incidents(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"manual scenario is missing: {source}")
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("manual scenario must contain an incident list")
    return payload
