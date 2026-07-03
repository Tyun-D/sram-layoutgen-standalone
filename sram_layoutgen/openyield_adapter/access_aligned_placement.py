from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Rect:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return round(self.x1 - self.x0, 6)

    @property
    def height(self) -> float:
        return round(self.y1 - self.y0, 6)

    def to_dict(self) -> dict[str, float]:
        return {
            "x0": round(self.x0, 6),
            "y0": round(self.y0, 6),
            "x1": round(self.x1, 6),
            "y1": round(self.y1, 6),
            "width": self.width,
            "height": self.height,
        }


def rect_from_bbox(bbox: dict[str, Any]) -> Rect:
    return Rect(float(bbox["x0"]), float(bbox["y0"]), float(bbox["x1"]), float(bbox["y1"]))


def translate_bbox(bbox: dict[str, Any], dx: float, dy: float) -> dict[str, float]:
    return Rect(
        float(bbox["x0"]) + dx,
        float(bbox["y0"]) + dy,
        float(bbox["x1"]) + dx,
        float(bbox["y1"]) + dy,
    ).to_dict()


def union_rects(rects: list[dict[str, Any]]) -> dict[str, float]:
    x0 = min(float(rect["x0"]) for rect in rects)
    y0 = min(float(rect["y0"]) for rect in rects)
    x1 = max(float(rect["x1"]) for rect in rects)
    y1 = max(float(rect["y1"]) for rect in rects)
    return Rect(x0, y0, x1, y1).to_dict()


def place_vertical_stack(
    bboxes: list[dict[str, Any]],
    origin_x: float,
    origin_y: float,
    gap: float,
) -> list[dict[str, float]]:
    placed: list[dict[str, float]] = []
    current_y = origin_y
    for bbox in bboxes:
        width = float(bbox["width"])
        height = float(bbox["height"])
        placed.append(
            Rect(origin_x, current_y, origin_x + width, current_y + height).to_dict()
        )
        current_y += height + gap
    return placed


def place_horizontal_stack(
    bboxes: list[dict[str, Any]],
    origin_x: float,
    origin_y: float,
    gap: float,
) -> list[dict[str, float]]:
    placed: list[dict[str, float]] = []
    current_x = origin_x
    for bbox in bboxes:
        width = float(bbox["width"])
        height = float(bbox["height"])
        placed.append(
            Rect(current_x, origin_y, current_x + width, origin_y + height).to_dict()
        )
        current_x += width + gap
    return placed


def center_y(container: dict[str, Any], height: float) -> float:
    return round((float(container["y0"]) + float(container["y1"]) - height) / 2.0, 6)


def center_x(container: dict[str, Any], width: float) -> float:
    return round((float(container["x0"]) + float(container["x1"]) - width) / 2.0, 6)
