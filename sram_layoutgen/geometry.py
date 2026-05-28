"""Small rectangle-based layout database for SRAM macro generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True, order=True)
class Point:
    x: float
    y: float

    def to_dict(self) -> Dict[str, float]:
        return {"x": self.x, "y": self.y}


@dataclass(frozen=True)
class Rect:
    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self) -> None:
        if self.x1 < self.x0 or self.y1 < self.y0:
            raise ValueError(f"invalid rectangle: {self}")

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> Point:
        return Point((self.x0 + self.x1) / 2.0, (self.y0 + self.y1) / 2.0)

    def inflate(self, amount: float) -> "Rect":
        return Rect(self.x0 - amount, self.y0 - amount, self.x1 + amount, self.y1 + amount)

    def shifted(self, dx: float, dy: float) -> "Rect":
        return Rect(self.x0 + dx, self.y0 + dy, self.x1 + dx, self.y1 + dy)

    def overlaps(self, other: "Rect") -> bool:
        return not (
            self.x1 <= other.x0
            or other.x1 <= self.x0
            or self.y1 <= other.y0
            or other.y1 <= self.y0
        )

    def spacing_to(self, other: "Rect") -> float:
        if self.overlaps(other):
            return -min(
                self.x1 - other.x0,
                other.x1 - self.x0,
                self.y1 - other.y0,
                other.y1 - self.y0,
            )
        dx = max(other.x0 - self.x1, self.x0 - other.x1, 0.0)
        dy = max(other.y0 - self.y1, self.y0 - other.y1, 0.0)
        if dx == 0.0:
            return dy
        if dy == 0.0:
            return dx
        return (dx * dx + dy * dy) ** 0.5

    def to_dict(self) -> Dict[str, float]:
        return {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1}

    @staticmethod
    def union(rects: Iterable["Rect"]) -> "Rect":
        rect_list = list(rects)
        if not rect_list:
            return Rect(0.0, 0.0, 0.0, 0.0)
        return Rect(
            min(rect.x0 for rect in rect_list),
            min(rect.y0 for rect in rect_list),
            max(rect.x1 for rect in rect_list),
            max(rect.y1 for rect in rect_list),
        )


@dataclass
class Shape:
    layer: str
    rect: Rect
    purpose: str = "drawing"
    net: Optional[str] = None
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "layer": self.layer,
            "purpose": self.purpose,
            "net": self.net,
            "name": self.name,
            "rect": self.rect.to_dict(),
        }


@dataclass
class Pin:
    name: str
    net: str
    layer: str
    rect: Rect
    direction: str = "INOUT"
    use: str = "SIGNAL"

    @property
    def center(self) -> Point:
        return self.rect.center

    def to_shape(self) -> Shape:
        return Shape(self.layer, self.rect, "pin", self.net, self.name)

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "net": self.net,
            "layer": self.layer,
            "direction": self.direction,
            "use": self.use,
            "rect": self.rect.to_dict(),
        }


@dataclass
class Instance:
    name: str
    cell: str
    rect: Rect
    role: str = ""
    mirror: str = "R0"
    rotate: int = 0
    pins: List[Pin] = field(default_factory=list)
    placement_mode: str = "bbox"
    origin: Optional[Point] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "cell": self.cell,
            "role": self.role,
            "mirror": self.mirror,
            "rotate": self.rotate,
            "rect": self.rect.to_dict(),
            "placement_mode": self.placement_mode,
            "origin": self.origin.to_dict() if self.origin is not None else None,
            "pins": [pin.to_dict() for pin in self.pins],
        }


@dataclass
class CellArray:
    name: str
    cell: str
    origin: Point
    columns: int
    rows: int
    pitch_x: float
    pitch_y: float
    rect: Rect
    role: str = ""
    mirror_x: bool = False
    mirror_y: bool = False
    row_offset: int = 0
    column_offset: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "cell": self.cell,
            "role": self.role,
            "origin": self.origin.to_dict(),
            "columns": self.columns,
            "rows": self.rows,
            "pitch_x": self.pitch_x,
            "pitch_y": self.pitch_y,
            "rect": self.rect.to_dict(),
            "mirror_x": self.mirror_x,
            "mirror_y": self.mirror_y,
            "row_offset": self.row_offset,
            "column_offset": self.column_offset,
        }


class LayoutDB:
    """In-memory layout database with JSON and SVG export helpers."""

    def __init__(self, top_name: str) -> None:
        self.top_name = top_name
        self.shapes: List[Shape] = []
        self.instances: List[Instance] = []
        self.cell_arrays: List[CellArray] = []
        self.pins: Dict[str, List[Pin]] = {}
        self.metadata: Dict[str, object] = {}

    def add_shape(
        self,
        layer: str,
        rect: Rect,
        purpose: str = "drawing",
        net: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Shape:
        shape = Shape(layer, rect, purpose, net, name)
        self.shapes.append(shape)
        return shape

    def add_pin(
        self,
        name: str,
        net: str,
        layer: str,
        rect: Rect,
        direction: str = "INOUT",
        use: str = "SIGNAL",
    ) -> Pin:
        pin = Pin(name, net, layer, rect, direction, use)
        self.pins.setdefault(net, []).append(pin)
        self.shapes.append(pin.to_shape())
        return pin

    def add_instance(self, instance: Instance) -> None:
        self.instances.append(instance)

    def add_cell_array(self, array: CellArray) -> None:
        self.cell_arrays.append(array)

    @property
    def bounds(self) -> Rect:
        return Rect.union(shape.rect for shape in self.shapes)

    @property
    def area(self) -> float:
        return self.bounds.area

    def pin_list(self) -> List[Pin]:
        return [pin for pins in self.pins.values() for pin in pins]

    def shapes_by_layer(self) -> Dict[str, List[Shape]]:
        grouped: Dict[str, List[Shape]] = {}
        for shape in self.shapes:
            grouped.setdefault(shape.layer, []).append(shape)
        return grouped

    def route_length_by_layer(self, purposes: Iterable[str] = ("route",)) -> Dict[str, float]:
        allowed_purposes = set(purposes)
        result: Dict[str, float] = {}
        for shape in self.shapes:
            if shape.purpose not in allowed_purposes:
                continue
            result[shape.layer] = result.get(shape.layer, 0.0) + max(shape.rect.width, shape.rect.height)
        return {layer: round(length, 4) for layer, length in sorted(result.items())}

    def to_dict(self) -> Dict[str, object]:
        return {
            "top_name": self.top_name,
            "metadata": self.metadata,
            "bounds": self.bounds.to_dict(),
            "instances": [instance.to_dict() for instance in self.instances],
            "cell_arrays": [array.to_dict() for array in self.cell_arrays],
            "pins": [pin.to_dict() for pin in self.pin_list()],
            "shapes": [shape.to_dict() for shape in self.shapes],
        }

    def write_json(self, path: Path) -> None:
        import json

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def write_svg(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        bounds = self.bounds.inflate(2.0)
        scale = 8.0
        width = max(1.0, bounds.width * scale)
        height = max(1.0, bounds.height * scale)
        palette = {
            "boundary": "#404040",
            "nwell": "#cfe8ff",
            "pwell": "#ffe0ec",
            "active": "#7bc77b",
            "poly": "#d4863f",
            "m1": "#2f80ed",
            "m2": "#d84c4c",
            "m3": "#2f9e44",
            "m4": "#8f55d6",
            "via1": "#333333",
            "via2": "#333333",
            "via3": "#333333",
        }

        def sx(x: float) -> float:
            return (x - bounds.x0) * scale

        def sy(y: float) -> float:
            return height - (y - bounds.y0) * scale

        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.1f}" height="{height:.1f}" '
            f'viewBox="0 0 {width:.1f} {height:.1f}">',
            '<rect width="100%" height="100%" fill="#fbfbfa"/>',
        ]
        for shape in self.shapes:
            color = palette.get(shape.layer, "#999999")
            opacity = "0.35" if shape.purpose in {"module", "well"} else "0.86"
            stroke = "#222222" if shape.purpose in {"pin", "boundary"} else "none"
            rect = shape.rect
            lines.append(
                f'<rect x="{sx(rect.x0):.2f}" y="{sy(rect.y1):.2f}" '
                f'width="{rect.width * scale:.2f}" height="{rect.height * scale:.2f}" '
                f'fill="{color}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="0.7"/>'
            )
        lines.append("</svg>")
        path.write_text("\n".join(lines), encoding="utf-8")


def rect_from_center(center: Point, width: float, height: float) -> Rect:
    return Rect(
        center.x - width / 2.0,
        center.y - height / 2.0,
        center.x + width / 2.0,
        center.y + height / 2.0,
    )
