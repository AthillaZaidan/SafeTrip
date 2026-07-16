from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator


@dataclass(frozen=True)
class VideoFrame:
    frame_index: int
    timestamp_seconds: float
    fps: float
    raw_bgr_frame: Any


def iter_video_frames(
    video_path: str | Path,
    frame_stride: int = 1,
    max_frames: int | None = None,
    *,
    fps_override: float | None = None,
    capture_factory: Callable[[str], Any] | None = None,
) -> Iterator[VideoFrame]:
    if frame_stride < 1:
        raise ValueError("frame_stride must be at least 1")
    if max_frames is not None and max_frames < 1:
        raise ValueError("max_frames must be null or positive")
    if capture_factory is None:
        try:
            import cv2
        except ImportError as error:
            raise RuntimeError("opencv-python is required for video input") from error
        capture_factory = cv2.VideoCapture

    capture = capture_factory(str(video_path))
    if not capture.isOpened():
        capture.release()
        raise ValueError(f"unreadable video: {video_path}")
    fps = float(fps_override if fps_override is not None else capture.get(5))
    if fps <= 0:
        capture.release()
        raise ValueError(f"invalid FPS for video: {video_path}")

    frame_index = 0
    yielded = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % frame_stride == 0:
                yield VideoFrame(frame_index, frame_index / fps, fps, frame)
                yielded += 1
                if max_frames is not None and yielded >= max_frames:
                    break
            frame_index += 1
    finally:
        capture.release()
    if frame_index == 0 and yielded == 0:
        raise ValueError(f"video contains no readable frames: {video_path}")
