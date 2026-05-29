"""Built-in lightweight DRC checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .geometry import LayoutDB, Shape
from .tech import Tech


@dataclass
class DRCViolation:
    rule: str
    layer: str
    message: str
    shape_a: Optional[int] = None
    shape_b: Optional[int] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "rule": self.rule,
            "layer": self.layer,
            "message": self.message,
            "shape_a": self.shape_a,
            "shape_b": self.shape_b,
        }


@dataclass
class DRCResult:
    violations: List[DRCViolation] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.violations

    def to_dict(self) -> Dict[str, object]:
        return {
            "clean": self.clean,
            "violation_count": len(self.violations),
            "violations": [violation.to_dict() for violation in self.violations],
        }


class Verifier:
    def __init__(self, tech: Tech) -> None:
        self.tech = tech

    def run(self, layout: LayoutDB) -> DRCResult:
        result = DRCResult()
        self._check_widths(layout, result)
        self._check_spacing(layout, result)
        self._check_cell_overlaps(layout, result)
        return result

    def _check_widths(self, layout: LayoutDB, result: DRCResult) -> None:
        for index, shape in enumerate(layout.shapes):
            layer = self.tech.layers.get(shape.layer)
            if layer is None or shape.purpose in {"boundary", "debug_probe", "route_guide"}:
                continue
            width = min(shape.rect.width, shape.rect.height)
            if width + 1e-9 < layer.min_width:
                result.violations.append(
                    DRCViolation(
                        "min_width",
                        shape.layer,
                        f"shape {index} width {width:.4f} below {layer.min_width:.4f}",
                        index,
                    )
                )

    def _check_spacing(self, layout: LayoutDB, result: DRCResult) -> None:
        for layer_name, shapes in layout.shapes_by_layer().items():
            layer = self.tech.layers.get(layer_name)
            if layer is None or layer_name == "boundary":
                continue
            for i, a in enumerate(shapes):
                for j in range(i + 1, len(shapes)):
                    b = shapes[j]
                    if (
                        self._same_connectivity(a, b)
                        or a.purpose in {"boundary", "pin", "stdcell", "module", "route_guide", "debug_probe"}
                        or b.purpose in {"boundary", "pin", "stdcell", "module", "route_guide", "debug_probe"}
                    ):
                        continue
                    spacing = a.rect.spacing_to(b.rect)
                    if spacing + 1e-9 < layer.min_space:
                        result.violations.append(
                            DRCViolation(
                                "min_spacing",
                                layer_name,
                                f"shapes {i} and {j} spacing {spacing:.4f} below {layer.min_space:.4f}",
                                i,
                                j,
                            )
                        )

    @staticmethod
    def _same_connectivity(a: Shape, b: Shape) -> bool:
        return bool(a.net and b.net and a.net == b.net)

    @staticmethod
    def _legal_openram_physical_overlap(role_a: str, role_b: str) -> bool:
        storage_stitch_roles = {"bitcell_array", "dummy_bitcell", "replica_bitline"}
        replacement_stitch_roles = {"precharge", "replica_precharge", "column_mux"}
        if role_a in storage_stitch_roles and role_b in storage_stitch_roles:
            return True
        if role_a in replacement_stitch_roles and role_b in replacement_stitch_roles:
            return role_a == role_b or {role_a, role_b} == {"precharge", "replica_precharge"}
        return False

    def _check_cell_overlaps(self, layout: LayoutDB, result: DRCResult) -> None:
        tolerance_area = 1e-6
        objects = []
        for instance in layout.instances:
            objects.append((instance.name, instance.role or instance.cell, instance.rect))
        for array in layout.cell_arrays:
            objects.append((array.name, array.role or array.cell, array.rect))
        for i, (name_a, role_a, rect_a) in enumerate(objects):
            for name_b, role_b, rect_b in objects[i + 1 :]:
                overlap_w = min(rect_a.x1, rect_b.x1) - max(rect_a.x0, rect_b.x0)
                overlap_h = min(rect_a.y1, rect_b.y1) - max(rect_a.y0, rect_b.y0)
                if overlap_w <= 0.0 or overlap_h <= 0.0:
                    continue
                overlap_area = overlap_w * overlap_h
                if overlap_area <= tolerance_area:
                    continue
                if self._legal_openram_physical_overlap(role_a, role_b):
                    continue
                result.violations.append(
                    DRCViolation(
                        "cell_overlap",
                        "placement",
                        f"{name_a} overlaps {name_b} by {overlap_area:.6f} um^2",
                        i,
                    )
                )
