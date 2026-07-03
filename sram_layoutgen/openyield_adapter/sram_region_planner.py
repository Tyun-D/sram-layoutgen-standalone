from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RegionBox:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def shifted(self, dx: float, dy: float) -> "RegionBox":
        return RegionBox(self.x0 + dx, self.y0 + dy, self.x1 + dx, self.y1 + dy)

    def to_dict(self) -> dict[str, float]:
        return {
            "x0": round(self.x0, 6),
            "y0": round(self.y0, 6),
            "x1": round(self.x1, 6),
            "y1": round(self.y1, 6),
            "width": round(self.width, 6),
            "height": round(self.height, 6),
        }


def union_boxes(boxes: Iterable[RegionBox]) -> RegionBox:
    items = list(boxes)
    if not items:
        return RegionBox(0.0, 0.0, 0.0, 0.0)
    return RegionBox(
        min(item.x0 for item in items),
        min(item.y0 for item in items),
        max(item.x1 for item in items),
        max(item.y1 for item in items),
    )


def box_from_size(x: float, y: float, width: float, height: float) -> RegionBox:
    return RegionBox(x, y, x + width, y + height)
