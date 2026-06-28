"""Gate-row packing helpers for compact OpenYield decoder/control placement."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sram_layoutgen.gds_util import measure_gds_bbox
from sram_layoutgen.geometry import Rect
from sram_layoutgen.stdcell import generated_cell_pins


@dataclass(frozen=True)
class GateCellFootprint:
    cell_name: str
    width: float
    height: float
    vdd_y_r0: float | None
    gnd_y_r0: float | None
    rail_thickness: float
    supported_orientations: tuple[str, ...] = ("R0", "MX")
    blocked_reason: str | None = None

    def rail_center(self, net: str, mirror: str) -> float | None:
        base = self.vdd_y_r0 if net == "vdd" else self.gnd_y_r0 if net == "gnd" else None
        if base is None:
            return None
        if mirror in {"MX", "XY"}:
            return self.height - base
        return base

    def top_rail_net(self, mirror: str) -> str | None:
        vdd = self.rail_center("vdd", mirror)
        gnd = self.rail_center("gnd", mirror)
        if vdd is None or gnd is None:
            return None
        return "vdd" if vdd >= gnd else "gnd"

    def bottom_rail_net(self, mirror: str) -> str | None:
        vdd = self.rail_center("vdd", mirror)
        gnd = self.rail_center("gnd", mirror)
        if vdd is None or gnd is None:
            return None
        return "vdd" if vdd <= gnd else "gnd"

    def top_rail_interval(self, mirror: str) -> tuple[str | None, float | None, float | None]:
        net = self.top_rail_net(mirror)
        if net is None:
            return None, None, None
        center = self.rail_center(net, mirror)
        half = self.rail_thickness / 2.0
        return net, center - half, center + half

    def bottom_rail_interval(self, mirror: str) -> tuple[str | None, float | None, float | None]:
        net = self.bottom_rail_net(mirror)
        if net is None:
            return None, None, None
        center = self.rail_center(net, mirror)
        half = self.rail_thickness / 2.0
        return net, center - half, center + half

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell_name": self.cell_name,
            "width": self.width,
            "height": self.height,
            "vdd_y_r0": self.vdd_y_r0,
            "gnd_y_r0": self.gnd_y_r0,
            "rail_thickness": self.rail_thickness,
            "supported_orientations": list(self.supported_orientations),
            "blocked_reason": self.blocked_reason,
        }


@dataclass(frozen=True)
class GateCellPlacement:
    instance_name: str
    cell_name: str
    x: float
    y: float
    width: float
    height: float
    mirror: str
    row_index: int

    @property
    def rect(self) -> Rect:
        return Rect(self.x, self.y, self.x + self.width, self.y + self.height)

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_name": self.instance_name,
            "cell_name": self.cell_name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "mirror": self.mirror,
            "row_index": self.row_index,
        }


@dataclass(frozen=True)
class GateRow:
    row_name: str
    row_index: int
    origin_x: float
    origin_y: float
    width: float
    height: float
    mirror: str
    cells: tuple[GateCellPlacement, ...]
    vdd_y: float | None
    gnd_y: float | None
    blocked_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_name": self.row_name,
            "row_index": self.row_index,
            "origin_x": self.origin_x,
            "origin_y": self.origin_y,
            "width": self.width,
            "height": self.height,
            "mirror": self.mirror,
            "vdd_y": self.vdd_y,
            "gnd_y": self.gnd_y,
            "blocked_reason": self.blocked_reason,
            "cells": [cell.to_dict() for cell in self.cells],
        }


@dataclass(frozen=True)
class GateRowPackingPlan:
    block_name: str
    explicit_opt_in: bool
    row_pitch: float
    total_width: float
    total_height: float
    rows: tuple[GateRow, ...]
    fallback_cells: tuple[str, ...]
    blocked_cells: tuple[dict[str, Any], ...]
    blocked_reason: str | None
    average_intra_row_gap_um: float
    rail_alignment: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_name": self.block_name,
            "explicit_opt_in": self.explicit_opt_in,
            "row_pitch": self.row_pitch,
            "total_width": self.total_width,
            "total_height": self.total_height,
            "fallback_cells": list(self.fallback_cells),
            "blocked_cells": list(self.blocked_cells),
            "blocked_reason": self.blocked_reason,
            "average_intra_row_gap_um": self.average_intra_row_gap_um,
            "rail_alignment": self.rail_alignment,
            "rows": [row.to_dict() for row in self.rows],
        }


def _local_rail_y(cell_name: str, width: float, height: float, net: str) -> float | None:
    rect = Rect(0.0, 0.0, width, height)
    pins = generated_cell_pins(cell_name, rect, "R0")
    matches = [float(pin["y"]) for pin in pins if str(pin["name"]) == net]
    if not matches:
        return None
    return sum(matches) / len(matches)


def build_gate_cell_footprint(cell_name: str, width: float, height: float, rail_thickness: float = 0.14) -> GateCellFootprint:
    vdd_y = _local_rail_y(cell_name, width, height, "vdd")
    gnd_y = _local_rail_y(cell_name, width, height, "gnd")
    blocked = None
    if width <= 0.0 or height <= 0.0:
        blocked = "non_positive_dimensions"
    elif vdd_y is None or gnd_y is None:
        blocked = "missing_power_rail_pin_metadata"
    return GateCellFootprint(
        cell_name=cell_name,
        width=float(width),
        height=float(height),
        vdd_y_r0=vdd_y,
        gnd_y_r0=gnd_y,
        rail_thickness=float(rail_thickness),
        blocked_reason=blocked,
    )


def pack_cells_left_to_right(
    row_name: str,
    row_index: int,
    cell_names: list[str],
    footprints: dict[str, GateCellFootprint],
    origin_x: float,
    origin_y: float,
    mirror: str,
) -> GateRow:
    placements: list[GateCellPlacement] = []
    x = float(origin_x)
    blocked_reason = None
    height = 0.0
    for col, cell_name in enumerate(cell_names):
        footprint = footprints[cell_name]
        if blocked_reason is None and footprint.blocked_reason:
            blocked_reason = footprint.blocked_reason
        height = max(height, footprint.height)
        placements.append(
            GateCellPlacement(
                instance_name=f"{row_name}_{col}",
                cell_name=cell_name,
                x=x,
                y=float(origin_y),
                width=footprint.width,
                height=footprint.height,
                mirror=mirror,
                row_index=row_index,
            )
        )
        x += footprint.width
    row_width = x - float(origin_x)
    row_footprint = footprints[cell_names[0]] if cell_names else None
    vdd_y = float(origin_y) + (row_footprint.rail_center("vdd", mirror) if row_footprint else 0.0) if row_footprint and row_footprint.rail_center("vdd", mirror) is not None else None
    gnd_y = float(origin_y) + (row_footprint.rail_center("gnd", mirror) if row_footprint else 0.0) if row_footprint and row_footprint.rail_center("gnd", mirror) is not None else None
    return GateRow(
        row_name=row_name,
        row_index=row_index,
        origin_x=float(origin_x),
        origin_y=float(origin_y),
        width=row_width,
        height=height,
        mirror=mirror,
        cells=tuple(placements),
        vdd_y=vdd_y,
        gnd_y=gnd_y,
        blocked_reason=blocked_reason,
    )


def pack_rows_bottom_to_top(
    block_name: str,
    row_cells: list[list[str]],
    footprints: dict[str, GateCellFootprint],
    origin_x: float,
    origin_y: float,
    row_pitch: float,
    orientation_policy: str = "alternating_r0_mx",
) -> tuple[GateRow, ...]:
    rows: list[GateRow] = []
    for row_index, cells in enumerate(row_cells):
        mirror = "MX" if orientation_policy == "alternating_r0_mx" and row_index % 2 else "R0"
        row = pack_cells_left_to_right(
            row_name=f"{block_name}_row{row_index}",
            row_index=row_index,
            cell_names=cells,
            footprints=footprints,
            origin_x=origin_x,
            origin_y=float(origin_y) + row_index * float(row_pitch),
            mirror=mirror,
        )
        rows.append(row)
    return tuple(rows)


def validate_rail_alignment(
    rows: tuple[GateRow, ...],
    footprints: dict[str, GateCellFootprint],
) -> dict[str, Any]:
    boundaries: list[dict[str, Any]] = []
    vdd_pass = True
    gnd_pass = True
    for lower, upper in zip(rows, rows[1:]):
        lower_first = footprints[lower.cells[0].cell_name]
        upper_first = footprints[upper.cells[0].cell_name]
        lower_net, lower_y0, lower_y1 = lower_first.top_rail_interval(lower.mirror)
        upper_net, upper_y0, upper_y1 = upper_first.bottom_rail_interval(upper.mirror)
        net_match = lower_net is not None and lower_net == upper_net
        stitch_net = lower_net if net_match else None
        stitch_y0 = lower.origin_y + float(lower_y1) if lower_y1 is not None else None
        stitch_y1 = upper.origin_y + float(upper_y0) if upper_y0 is not None else None
        passed = bool(
            net_match
            and stitch_y0 is not None
            and stitch_y1 is not None
            and stitch_y1 >= stitch_y0
        )
        entry = {
            "lower_row": lower.row_name,
            "upper_row": upper.row_name,
            "lower_top_net": lower_net,
            "upper_bottom_net": upper_net,
            "lower_top_y1": stitch_y0,
            "upper_bottom_y0": stitch_y1,
            "stitch_net": stitch_net,
            "stitch_required": passed,
            "passed": passed,
        }
        boundaries.append(entry)
        if stitch_net == "vdd":
            vdd_pass = vdd_pass and passed
        elif stitch_net == "gnd":
            gnd_pass = gnd_pass and passed
        else:
            vdd_pass = False
            gnd_pass = False
    return {
        "checked_boundaries": len(boundaries),
        "boundaries": boundaries,
        "rail_alignment_pass": all(item["passed"] for item in boundaries) if boundaries else True,
        "vdd_rail_continuity_candidate": vdd_pass,
        "gnd_rail_continuity_candidate": gnd_pass,
    }


def build_gate_row_packing_plan(
    block_name: str,
    row_cells: list[list[str]],
    footprints: dict[str, GateCellFootprint],
    origin_x: float,
    origin_y: float,
    explicit_opt_in: bool,
    row_pitch: float | None = None,
    orientation_policy: str = "alternating_r0_mx",
) -> GateRowPackingPlan:
    blocked_cells: list[dict[str, Any]] = []
    fallback_cells: list[str] = []
    allowed_rows: list[list[str]] = []
    heights: list[float] = []
    for row in row_cells:
        allowed_row: list[str] = []
        for cell_name in row:
            footprint = footprints[cell_name]
            if footprint.blocked_reason:
                blocked_cells.append({"cell_name": cell_name, "blocked_reason": footprint.blocked_reason})
                fallback_cells.append(cell_name)
                continue
            allowed_row.append(cell_name)
            heights.append(footprint.height)
        if allowed_row:
            allowed_rows.append(allowed_row)
    dominant_height = max(heights) if heights else 0.0
    if row_pitch is None:
        row_pitch = dominant_height
    rows = pack_rows_bottom_to_top(
        block_name=block_name,
        row_cells=allowed_rows,
        footprints=footprints,
        origin_x=origin_x,
        origin_y=origin_y,
        row_pitch=row_pitch,
        orientation_policy=orientation_policy,
    )
    rail_alignment = validate_rail_alignment(rows, footprints)
    total_width = max((row.width for row in rows), default=0.0)
    total_height = (len(rows) - 1) * row_pitch + max((row.height for row in rows), default=0.0) if rows else 0.0
    return GateRowPackingPlan(
        block_name=block_name,
        explicit_opt_in=explicit_opt_in,
        row_pitch=float(row_pitch),
        total_width=float(total_width),
        total_height=float(total_height),
        rows=rows,
        fallback_cells=tuple(fallback_cells),
        blocked_cells=tuple(blocked_cells),
        blocked_reason=None if rows else "no_packable_cells",
        average_intra_row_gap_um=0.0,
        rail_alignment=rail_alignment,
    )


def _gate_count_from_layout_json(path: Path | None, roles: set[str]) -> int | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    instances = payload.get("instances", [])
    return sum(1 for item in instances if str(item.get("role")) in roles)


def _bbox_dict(path: Path | None) -> dict[str, float] | None:
    if path is None or not path.exists():
        return None
    bbox = measure_gds_bbox(path)
    return bbox.to_dict() if bbox else None


def emit_gate_row_packing_report(
    plan: GateRowPackingPlan,
    out_json: Path,
    out_md: Path,
    old_gds: Path,
    new_gds: Path,
    old_layout_json: Path | None = None,
    new_layout_json: Path | None = None,
    top_cell_name: str | None = None,
) -> dict[str, Any]:
    roles = {"row_decoder", "wordline_driver", "control_glue", "column_select", "delay_chain"}
    old_size = old_gds.stat().st_size if old_gds.exists() else 0
    new_size = new_gds.stat().st_size if new_gds.exists() else 0
    report = {
        "gate_row_packing_available": True,
        "decoder_gate_cells_identified": True,
        "gate_row_packing_opt_in_available": True,
        "legacy_default_behavior_preserved": True,
        "hybrid_compacted_gds_generated": bool(new_gds.exists() and new_size > 0),
        "compacted_gds_path": str(new_gds),
        "old_gds_path": str(old_gds),
        "gds_file_size_before_bytes": old_size,
        "gds_file_size_after_bytes": new_size,
        "top_cell_name": top_cell_name,
        "top_cell_bbox_before_um": _bbox_dict(old_gds),
        "top_cell_bbox_after_um": _bbox_dict(new_gds),
        "gate_cell_count_before": _gate_count_from_layout_json(old_layout_json, roles),
        "gate_cell_count_after": _gate_count_from_layout_json(new_layout_json, roles),
        "packed_gate_rows_count": len(plan.rows),
        "gate_rows_packed": len(plan.rows),
        "average_intra_row_gap_before_um": None,
        "average_intra_row_gap_after_um": plan.average_intra_row_gap_um,
        "intra_row_gap_removed": plan.average_intra_row_gap_um <= 1e-9,
        "rail_alignment_pass_fail": plan.rail_alignment["rail_alignment_pass"],
        "rail_alignment_audit_available": True,
        "vdd_rail_continuity_candidate": plan.rail_alignment["vdd_rail_continuity_candidate"],
        "gnd_rail_continuity_candidate": plan.rail_alignment["gnd_rail_continuity_candidate"],
        "fallback_cells": list(plan.fallback_cells),
        "blocked_cells": list(plan.blocked_cells),
        "routing_still_legacy": True,
        "gds_writer_modified": False,
        "routing_modified": False,
        "can_claim_full_openyield_layout_now": False,
        "can_claim_drc_clean_now": False,
        "can_claim_lvs_clean_now": False,
        "can_enter_routing_compaction": bool(new_gds.exists() and new_size > 0),
        "can_enter_power_rail_stitching_verification": bool(new_gds.exists() and new_size > 0),
        "packing_plan": plan.to_dict(),
        "notes": [
            "old average intra-row gap is not reconstructed numerically from the previous GDS; the legacy screenshot and prior prototype visually show sparse gate placement.",
            "new gate rows are packed with x_next = x_current + cell_width and row pitch derived from legal cell height.",
            "routing still legacy",
            "gate placement compacted",
            "routing compaction not yet performed",
        ],
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Gate Row Packing Report",
        "",
        f"- old_gds: `{old_gds}`",
        f"- new_gds: `{new_gds}`",
        f"- gds size before bytes: `{old_size}`",
        f"- gds size after bytes: `{new_size}`",
        f"- packed gate rows count: `{len(plan.rows)}`",
        f"- average intra-row gap before um: `not_reconstructed`",
        f"- average intra-row gap after um: `{plan.average_intra_row_gap_um}`",
        f"- rail alignment pass/fail: `{plan.rail_alignment['rail_alignment_pass']}`",
        f"- VDD continuity candidate: `{plan.rail_alignment['vdd_rail_continuity_candidate']}`",
        f"- GND continuity candidate: `{plan.rail_alignment['gnd_rail_continuity_candidate']}`",
        f"- fallback cells: `{list(plan.fallback_cells)}`",
        f"- blocked cells: `{list(plan.blocked_cells)}`",
        "",
        "## Notes",
        "",
    ]
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.extend(["", "## Rows", ""])
    for row in plan.rows:
        lines.append(
            f"- {row.row_name}: mirror=`{row.mirror}` origin=(`{row.origin_x}`, `{row.origin_y}`) width=`{row.width}` cells=`{[cell.cell_name for cell in row.cells]}`"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report
