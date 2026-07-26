from __future__ import annotations

from typing import Iterable


def rect_bbox(x0: float, y0: float, x1: float, y1: float) -> dict[str, float]:
    return {
        "x0": round(float(x0), 6),
        "y0": round(float(y0), 6),
        "x1": round(float(x1), 6),
        "y1": round(float(y1), 6),
        "width": round(float(x1) - float(x0), 6),
        "height": round(float(y1) - float(y0), 6),
    }


def polygon_bbox(points: Iterable[tuple[float, float]]) -> dict[str, float]:
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    return rect_bbox(min(xs), min(ys), max(xs), max(ys))


def bbox_center(bbox: dict[str, float]) -> dict[str, float]:
    return {
        "x": round((float(bbox["x0"]) + float(bbox["x1"])) / 2.0, 6),
        "y": round((float(bbox["y0"]) + float(bbox["y1"])) / 2.0, 6),
    }
