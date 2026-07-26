from __future__ import annotations

from typing import Any


def bbox_center(bbox: dict[str, float]) -> dict[str, float]:
    return {
        "x": round((float(bbox["x0"]) + float(bbox["x1"])) / 2.0, 6),
        "y": round((float(bbox["y0"]) + float(bbox["y1"])) / 2.0, 6),
    }


def polygon_bbox(points: list[tuple[float, float]]) -> dict[str, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return {
        "x0": round(min(xs), 6),
        "y0": round(min(ys), 6),
        "x1": round(max(xs), 6),
        "y1": round(max(ys), 6),
        "width": round(max(xs) - min(xs), 6),
        "height": round(max(ys) - min(ys), 6),
    }


def rect_bbox(x0: float, y0: float, x1: float, y1: float) -> dict[str, float]:
    return {
        "x0": round(min(x0, x1), 6),
        "y0": round(min(y0, y1), 6),
        "x1": round(max(x0, x1), 6),
        "y1": round(max(y0, y1), 6),
        "width": round(abs(x1 - x0), 6),
        "height": round(abs(y1 - y0), 6),
    }
