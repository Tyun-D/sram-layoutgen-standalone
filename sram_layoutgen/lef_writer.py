"""Abstract LEF writer for SRAM macros."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from .geometry import LayoutDB, Rect
from .tech import Tech


class LEFWriter:
    def __init__(self, tech: Tech, units: int = 2000) -> None:
        self.tech = tech
        self.units = units

    def write(self, layout: LayoutDB, path: Path, obstruction_layers: Iterable[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        bounds = layout.bounds
        lines: List[str] = [
            "VERSION 5.4 ;",
            "NAMESCASESENSITIVE ON ;",
            'BUSBITCHARS "[]" ;',
            'DIVIDERCHAR "/" ;',
            "UNITS",
            f"  DATABASE MICRONS {self.units} ;",
            "END UNITS",
            f"MACRO {layout.top_name}",
            "   CLASS BLOCK ;",
            f"   SIZE {bounds.width:.4f} BY {bounds.height:.4f} ;",
            "   SYMMETRY X Y R90 ;",
        ]
        for pin in sorted(layout.pin_list(), key=lambda item: item.name):
            layer = self.tech.layer(pin.layer)
            lines.extend(
                [
                    f"   PIN {pin.name}",
                    f"      DIRECTION {pin.direction} ;",
                ]
            )
            if pin.use in {"POWER", "GROUND"}:
                lines.extend([f"      USE {pin.use} ;", "      SHAPE ABUTMENT ;"])
            lines.extend(
                [
                    "      PORT",
                    f"         LAYER {layer.lef_name} ;",
                    f"         RECT {pin.rect.x0:.4f} {pin.rect.y0:.4f} {pin.rect.x1:.4f} {pin.rect.y1:.4f} ;",
                    "      END",
                    f"   END {pin.name}",
                ]
            )
        lines.append("   OBS")
        for layer_name in obstruction_layers:
            if layer_name not in self.tech.layers:
                continue
            layer = self.tech.layer(layer_name)
            lines.append(f"      LAYER {layer.lef_name} ;")
            for rect in self._abstract_obstructions(layout, layer_name):
                lines.append(f"         RECT {rect.x0:.4f} {rect.y0:.4f} {rect.x1:.4f} {rect.y1:.4f} ;")
        lines.extend(["   END", f"END {layout.top_name}", "END LIBRARY", ""])
        path.write_text("\n".join(lines), encoding="utf-8")

    def _abstract_obstructions(self, layout: LayoutDB, layer_name: str) -> List[Rect]:
        bounds = layout.bounds
        margin = max(self.tech.layer(layer_name).pitch * 4.0, 0.8)
        core = Rect(bounds.x0 + margin, bounds.y0 + margin, bounds.x1 - margin, bounds.y1 - margin)
        if core.area <= 0:
            return []
        pin_rects = [pin.rect.inflate(margin / 2.0) for pin in layout.pin_list() if pin.layer == layer_name]
        fragments = [core]
        for pin_rect in pin_rects:
            new_fragments: List[Rect] = []
            for fragment in fragments:
                new_fragments.extend(_cut_rect(fragment, pin_rect))
            fragments = new_fragments
        return [rect for rect in fragments if rect.area > 0.01]


def _cut_rect(rect: Rect, cutter: Rect) -> List[Rect]:
    if not rect.overlaps(cutter):
        return [rect]
    x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
    cx0, cy0, cx1, cy1 = (
        max(rect.x0, cutter.x0),
        max(rect.y0, cutter.y0),
        min(rect.x1, cutter.x1),
        min(rect.y1, cutter.y1),
    )
    pieces = [
        Rect(x0, y0, x1, cy0),
        Rect(x0, cy1, x1, y1),
        Rect(x0, cy0, cx0, cy1),
        Rect(cx1, cy0, x1, cy1),
    ]
    return [piece for piece in pieces if piece.area > 0.01]

