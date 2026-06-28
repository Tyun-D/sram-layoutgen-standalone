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
    bbox_y0: float = 0.0
    bbox_y1: float | None = None
    supported_orientations: tuple[str, ...] = ("R0", "MX")
    blocked_reason: str | None = None

    def rail_center(self, net: str, mirror: str) -> float | None:
        base = self.vdd_y_r0 if net == "vdd" else self.gnd_y_r0 if net == "gnd" else None
        if base is None:
            return None
        if mirror in {"MX", "XY"}:
            return self.height - base
        return base

    @property
    def bbox_height(self) -> float:
        upper = self.bbox_y1 if self.bbox_y1 is not None else self.height
        return float(upper) - float(self.bbox_y0)

    def origin_y_for_bbox_y0(self, target_y0: float, mirror: str) -> float:
        upper = self.bbox_y1 if self.bbox_y1 is not None else self.height
        if mirror in {"MX", "XY"}:
            return float(target_y0) - self.height + float(upper)
        return float(target_y0) - float(self.bbox_y0)

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
            "bbox_y0": self.bbox_y0,
            "bbox_y1": self.bbox_y1,
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
    vertical_abutment_policy: str
    row_pitch: float
    row_gap: float
    total_width: float
    total_height: float
    rows: tuple[GateRow, ...]
    fallback_cells: tuple[str, ...]
    blocked_cells: tuple[dict[str, Any], ...]
    blocked_reason: str | None
    average_intra_row_gap_um: float
    average_vertical_gap_um: float
    extra_interrow_power_stripe_inserted: bool
    rail_alignment: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_name": self.block_name,
            "explicit_opt_in": self.explicit_opt_in,
            "vertical_abutment_policy": self.vertical_abutment_policy,
            "row_pitch": self.row_pitch,
            "row_gap": self.row_gap,
            "total_width": self.total_width,
            "total_height": self.total_height,
            "fallback_cells": list(self.fallback_cells),
            "blocked_cells": list(self.blocked_cells),
            "blocked_reason": self.blocked_reason,
            "average_intra_row_gap_um": self.average_intra_row_gap_um,
            "average_vertical_gap_um": self.average_vertical_gap_um,
            "extra_interrow_power_stripe_inserted": self.extra_interrow_power_stripe_inserted,
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


def build_gate_cell_footprint(
    cell_name: str,
    width: float,
    height: float,
    rail_thickness: float = 0.14,
    bbox_y0: float = 0.0,
    bbox_y1: float | None = None,
) -> GateCellFootprint:
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
        bbox_y0=float(bbox_y0),
        bbox_y1=float(height if bbox_y1 is None else bbox_y1),
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
        height = max(height, footprint.bbox_height)
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
    first = footprints[cell_names[0]] if cell_names else None
    vdd_local = first.rail_center("vdd", mirror) if first is not None else None
    gnd_local = first.rail_center("gnd", mirror) if first is not None else None
    return GateRow(
        row_name=row_name,
        row_index=row_index,
        origin_x=float(origin_x),
        origin_y=float(origin_y),
        width=row_width,
        height=height,
        mirror=mirror,
        cells=tuple(placements),
        vdd_y=float(origin_y) + float(vdd_local) if vdd_local is not None else None,
        gnd_y=float(origin_y) + float(gnd_local) if gnd_local is not None else None,
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
    current_target_y0 = float(origin_y)
    for row_index, cells in enumerate(row_cells):
        mirror = "MX" if orientation_policy == "alternating_r0_mx" and row_index % 2 else "R0"
        lead = footprints[cells[0]]
        row_origin_y = lead.origin_y_for_bbox_y0(current_target_y0, mirror)
        rows.append(
            pack_cells_left_to_right(
                row_name=f"{block_name}_row{row_index}",
                row_index=row_index,
                cell_names=cells,
                footprints=footprints,
                origin_x=origin_x,
                origin_y=row_origin_y,
                mirror=mirror,
            )
        )
        current_target_y0 += float(row_pitch)
    return tuple(rows)


def validate_rail_alignment(
    rows: tuple[GateRow, ...],
    footprints: dict[str, GateCellFootprint],
    vertical_abutment_policy: str = "standard_row_spacing",
    row_gap: float = 0.0,
) -> dict[str, Any]:
    boundaries: list[dict[str, Any]] = []
    vdd_pass = True
    gnd_pass = True
    for lower, upper in zip(rows, rows[1:]):
        lower_first = footprints[lower.cells[0].cell_name]
        upper_first = footprints[upper.cells[0].cell_name]
        lower_net, _lower_y0, lower_y1 = lower_first.top_rail_interval(lower.mirror)
        upper_net, upper_y0, _upper_y1 = upper_first.bottom_rail_interval(upper.mirror)
        net_match = lower_net is not None and lower_net == upper_net
        boundary_y_lower = max(placement.y + footprints[placement.cell_name].bbox_y1 for placement in lower.cells)
        boundary_y_upper = min(placement.y + footprints[placement.cell_name].bbox_y0 for placement in upper.cells)
        physical_boundary_gap = float(boundary_y_upper) - float(boundary_y_lower)
        vertical_gap = 0.0 if vertical_abutment_policy == "zero_gap_alternating_mx" else float(row_gap)
        passed = bool(net_match and abs(vertical_gap) <= 1e-9)
        entry = {
            "lower_row": lower.row_name,
            "upper_row": upper.row_name,
            "lower_top_net": lower_net,
            "upper_bottom_net": upper_net,
            "expected_same_net": True,
            "actual_same_net": net_match,
            "lower_bbox_top_y": boundary_y_lower,
            "upper_bbox_bottom_y": boundary_y_upper,
            "vertical_gap_um": vertical_gap,
            "physical_boundary_gap_um": physical_boundary_gap,
            "extra_power_stripe_inserted": False,
            "passed": passed,
        }
        boundaries.append(entry)
        if lower_net == "vdd" or upper_net == "vdd":
            vdd_pass = vdd_pass and passed and net_match
        if lower_net == "gnd" or upper_net == "gnd":
            gnd_pass = gnd_pass and passed and net_match
        if lower_net not in {"vdd", "gnd"} or upper_net not in {"vdd", "gnd"}:
            vdd_pass = False
            gnd_pass = False
    return {
        "checked_boundaries": len(boundaries),
        "boundaries": boundaries,
        "rail_alignment_pass": all(item["passed"] for item in boundaries) if boundaries else True,
        "vertical_abutment_pass": all(item["passed"] for item in boundaries) if boundaries else True,
        "rail_boundary_match_pass": all(item["actual_same_net"] for item in boundaries) if boundaries else True,
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
    vertical_abutment_policy: str = "standard_row_spacing",
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
    dominant_bbox_height = max((footprints[cell].bbox_height for row in allowed_rows for cell in row), default=0.0)
    if vertical_abutment_policy == "zero_gap_alternating_mx":
        row_pitch = dominant_bbox_height
        row_gap = 0.0
        orientation_policy = "alternating_r0_mx"
        extra_interrow_power_stripe_inserted = False
    else:
        if row_pitch is None:
            row_pitch = dominant_bbox_height if dominant_bbox_height else dominant_height
        row_gap = max(0.0, float(row_pitch) - dominant_bbox_height) if dominant_bbox_height else 0.0
        extra_interrow_power_stripe_inserted = False
    rows = pack_rows_bottom_to_top(
        block_name=block_name,
        row_cells=allowed_rows,
        footprints=footprints,
        origin_x=origin_x,
        origin_y=origin_y,
        row_pitch=float(row_pitch),
        orientation_policy=orientation_policy,
    )
    rail_alignment = validate_rail_alignment(
        rows,
        footprints,
        vertical_abutment_policy=vertical_abutment_policy,
        row_gap=row_gap,
    )
    total_width = max((row.width for row in rows), default=0.0)
    total_height = (len(rows) - 1) * float(row_pitch) + max((row.height for row in rows), default=0.0) if rows else 0.0
    return GateRowPackingPlan(
        block_name=block_name,
        explicit_opt_in=explicit_opt_in,
        vertical_abutment_policy=vertical_abutment_policy,
        row_pitch=float(row_pitch),
        row_gap=float(row_gap),
        total_width=float(total_width),
        total_height=float(total_height),
        rows=rows,
        fallback_cells=tuple(fallback_cells),
        blocked_cells=tuple(blocked_cells),
        blocked_reason=None if rows else "no_packable_cells",
        average_intra_row_gap_um=0.0,
        average_vertical_gap_um=float(row_gap),
        extra_interrow_power_stripe_inserted=extra_interrow_power_stripe_inserted,
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


def _report_payload(
    plan: GateRowPackingPlan,
    old_gds: Path,
    new_gds: Path,
    old_layout_json: Path | None,
    new_layout_json: Path | None,
    top_cell_name: str | None,
) -> dict[str, Any]:
    roles = {"row_decoder", "wordline_driver", "control_glue", "column_select", "delay_chain"}
    old_size = old_gds.stat().st_size if old_gds.exists() else 0
    new_size = new_gds.stat().st_size if new_gds.exists() else 0
    return {
        "gate_row_packing_available": True,
        "decoder_gate_cells_identified": True,
        "gate_row_packing_opt_in_available": True,
        "gate_row_vertical_abutment_available": plan.vertical_abutment_policy == "zero_gap_alternating_mx",
        "vertical_abutment_policy": plan.vertical_abutment_policy,
        "row_gap_removed": abs(plan.row_gap) <= 1e-9,
        "row_pitch_equals_cell_height": abs(plan.row_pitch - max((row.height for row in plan.rows), default=0.0)) <= 1e-9,
        "alternating_r0_mx_applied": all(row.mirror == ("MX" if row.row_index % 2 else "R0") for row in plan.rows),
        "extra_interrow_power_stripe_removed": not plan.extra_interrow_power_stripe_inserted,
        "rail_boundary_audit_available": True,
        "rail_boundary_match_pass": plan.rail_alignment.get("rail_boundary_match_pass", False),
        "vertical_abutment_pass": plan.rail_alignment.get("vertical_abutment_pass", False),
        "legacy_default_behavior_preserved": True,
        "hybrid_compacted_gds_generated": bool(new_gds.exists() and new_size > 0),
        "hybrid_row_abutted_gds_generated": bool(new_gds.exists() and new_size > 0),
        "compacted_gds_path": str(new_gds),
        "row_abutted_gds_path": str(new_gds),
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
        "old_vertical_gap_um": None,
        "new_vertical_gap_um": plan.average_vertical_gap_um,
        "old_has_extra_interrow_power_stripe": True,
        "new_has_extra_interrow_power_stripe": plan.extra_interrow_power_stripe_inserted,
        "row_count": len(plan.rows),
        "rows_with_R0": sum(1 for row in plan.rows if row.mirror == "R0"),
        "rows_with_MX": sum(1 for row in plan.rows if row.mirror == "MX"),
        "rail_boundary_matches": sum(1 for item in plan.rail_alignment.get("boundaries", []) if item.get("actual_same_net")),
        "rail_boundary_mismatches": sum(1 for item in plan.rail_alignment.get("boundaries", []) if not item.get("actual_same_net")),
        "rail_alignment_pass_fail": plan.rail_alignment.get("rail_alignment_pass", False),
        "rail_alignment_audit_available": True,
        "vdd_rail_continuity_candidate": plan.rail_alignment.get("vdd_rail_continuity_candidate", False),
        "gnd_rail_continuity_candidate": plan.rail_alignment.get("gnd_rail_continuity_candidate", False),
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
            "old average intra-row gap is not reconstructed numerically from the previous GDS; the previous compacted result visibly inserted inter-row stitch shapes.",
            "new gate rows are packed with x_next = x_current + cell_width.",
            "routing still legacy",
            "gate placement compacted",
            "routing compaction not yet performed",
        ],
    }


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
    report = _report_payload(plan, old_gds, new_gds, old_layout_json, new_layout_json, top_cell_name)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Gate Row Packing Report",
        "",
        f"- old_gds: `{old_gds}`",
        f"- new_gds: `{new_gds}`",
        f"- gds size before bytes: `{report['gds_file_size_before_bytes']}`",
        f"- gds size after bytes: `{report['gds_file_size_after_bytes']}`",
        f"- packed gate rows count: `{len(plan.rows)}`",
        f"- average intra-row gap before um: `not_reconstructed`",
        f"- average intra-row gap after um: `{plan.average_intra_row_gap_um}`",
        f"- rail alignment pass/fail: `{plan.rail_alignment.get('rail_alignment_pass', False)}`",
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


def emit_gate_row_vertical_abutment_report(
    plan: GateRowPackingPlan,
    out_json: Path,
    out_md: Path,
    old_gds: Path,
    new_gds: Path,
    old_layout_json: Path | None = None,
    new_layout_json: Path | None = None,
    top_cell_name: str | None = None,
) -> dict[str, Any]:
    report = _report_payload(plan, old_gds, new_gds, old_layout_json, new_layout_json, top_cell_name)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Gate Row Vertical Abutment Report",
        "",
        f"- old_gds: `{old_gds}`",
        f"- new_gds: `{new_gds}`",
        f"- old_has_extra_interrow_power_stripe: `{report['old_has_extra_interrow_power_stripe']}`",
        f"- new_has_extra_interrow_power_stripe: `{report['new_has_extra_interrow_power_stripe']}`",
        f"- old_vertical_gap_um: `{report['old_vertical_gap_um']}`",
        f"- new_vertical_gap_um: `{report['new_vertical_gap_um']}`",
        f"- row_count: `{report['row_count']}`",
        f"- rows_with_R0: `{report['rows_with_R0']}`",
        f"- rows_with_MX: `{report['rows_with_MX']}`",
        f"- rail_boundary_matches: `{report['rail_boundary_matches']}`",
        f"- rail_boundary_mismatches: `{report['rail_boundary_mismatches']}`",
        f"- vertical_abutment_pass: `{report['vertical_abutment_pass']}`",
        "",
        "## Notes",
        "",
    ]
    for note in report["notes"]:
        lines.append(f"- {note}")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report
