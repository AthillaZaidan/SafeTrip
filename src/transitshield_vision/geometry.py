from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


Point = tuple[float, float]


@dataclass(frozen=True)
class MotionFeatures:
    speed_pixels_per_second: float
    normalized_speed: float
    direction_vector: Point


def bbox_footpoint(bbox_xyxy: Sequence[float]) -> Point:
    x1, _y1, x2, y2 = bbox_xyxy
    return (float(x1 + x2) / 2.0, float(y2))


def _on_segment(point: Point, start: Point, end: Point, epsilon: float = 1e-9) -> bool:
    px, py = point
    ax, ay = start
    bx, by = end
    cross = (px - ax) * (by - ay) - (py - ay) * (bx - ax)
    if abs(cross) > epsilon:
        return False
    return min(ax, bx) - epsilon <= px <= max(ax, bx) + epsilon and min(ay, by) - epsilon <= py <= max(ay, by) + epsilon


def point_in_polygon(point: Point, polygon: Sequence[Point]) -> bool:
    if len(polygon) < 3:
        raise ValueError("polygon must have at least three points")
    inside = False
    x, y = point
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        if _on_segment(point, start, end):
            return True
        x1, y1 = start
        x2, y2 = end
        if (y1 > y) != (y2 > y):
            crossing_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < crossing_x:
                inside = not inside
    return inside


def motion_features(previous: Point, current: Point, delta_seconds: float, bbox_height: float) -> MotionFeatures:
    if delta_seconds <= 0:
        raise ValueError("delta_seconds must be positive")
    dx = current[0] - previous[0]
    dy = current[1] - previous[1]
    distance = math.hypot(dx, dy)
    speed = distance / delta_seconds
    direction = (0.0, 0.0) if distance == 0 else (dx / distance, dy / distance)
    return MotionFeatures(speed, speed / max(float(bbox_height), 1.0), direction)


def direction_alignment(direction: Point, danger_direction: Point) -> float | None:
    left = math.hypot(*direction)
    right = math.hypot(*danger_direction)
    if left == 0 or right == 0:
        return None
    return (direction[0] * danger_direction[0] + direction[1] * danger_direction[1]) / (left * right)
