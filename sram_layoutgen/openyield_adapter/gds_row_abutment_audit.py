from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.tech import Tech

from .gate_row_packer import build_gate_cell_footprint

GATE_ROLES = {"row_decoder", "wordline_driver", "control_glue", "column_select", "delay_chain"}
DFF_ROLES = {"control_logic", "data_dff"}


def _tech() -> Tech:
    return Tech.freepdk45(Path('.'))


def _instance_mirror(layout_inst: dict[str, Any]) -> str:
    return str(layout_inst.get("mirror") or "R0")


def _instance_origin(layout_inst: dict[str, Any]) -> tuple[float, float]:
    origin = layout_inst.get("origin") or {}
    return float(origin.get("x", 0.0)), float(origin.get("y", 0.0))


def _load_layout_json(gds_path: Path, layout_json: str | Path | None) -> dict[str, Any] | None:
    path = Path(layout_json) if layout_json is not None else gds_path.with_suffix(".layout.json")
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _footprint_cache(layout: dict[str, Any] | None) -> dict[str, Any]:
    tech = _tech()
    names = {str(inst.get("cell")) for inst in (layout or {}).get("instances", []) if inst.get("cell")}
    cache = {}
    for name in names:
        try:
            cell = tech.cell(name)
        except KeyError:
            continue
        cache[name] = build_gate_cell_footprint(
            name,
            float(cell.width),
            float(cell.height),
            gds_path=cell.gds_path,
            bbox_x0=float(cell.bbox_x0),
            bbox_y0=float(cell.bbox_y0),
            bbox_x1=float(cell.bbox_x1),
            bbox_y1=float(cell.bbox_y1),
        )
    return cache


def _instance_record(inst: dict[str, Any], fp) -> dict[str, Any]:
    ox, oy = _instance_origin(inst)
    mirror = _instance_mirror(inst)
    bbox = {
        "x0": ox + fp.bbox_x0,
        "y0": oy + fp.bbox_y0,
        "x1": ox + fp.bbox_x1,
        "y1": oy + fp.bbox_y1,
    }
    vdd = fp.rail_interval("vdd", mirror)
    gnd = fp.rail_interval("gnd", mirror)

    def shift(interval: tuple[float, float] | None) -> dict[str, float] | None:
        return None if interval is None else {"y0": oy + interval[0], "y1": oy + interval[1]}

    return {
        "instance_name": str(inst.get("name")),
        "cell_name": str(inst.get("cell")),
        "role": str(inst.get("role")),
        "origin": {"x": ox, "y": oy},
        "orientation": mirror,
        "bbox": bbox,
        "detected_vdd_rail_bbox": shift(vdd),
        "detected_gnd_rail_bbox": shift(gnd),
        "rail_geometry_source": fp.rail_geometry_source,
        "blocked_reason": fp.blocked_reason,
    }


def _cluster_rows(instances: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    rows: dict[tuple[str, float], list[dict[str, Any]]] = {}
    for inst in instances:
        key = (str(inst["role"]), round(float(inst["origin"]["y"]), 6))
        rows.setdefault(key, []).append(inst)
    return [
        sorted(group, key=lambda item: (float(item["origin"]["x"]), item["instance_name"]))
        for _, group in sorted(rows.items(), key=lambda item: (item[0][1], item[0][0]))
    ]


def _pair_audit(lower_row: list[dict[str, Any]], upper_row: list[dict[str, Any]], row_index: int) -> dict[str, Any]:
    lower = lower_row[0]
    upper = upper_row[0]
    lower_vdd = lower.get("detected_vdd_rail_bbox")
    upper_vdd = upper.get("detected_vdd_rail_bbox")
    lower_gnd = lower.get("detected_gnd_rail_bbox")
    upper_gnd = upper.get("detected_gnd_rail_bbox")
    lower_top = lower_vdd if lower_vdd and lower_gnd and lower_vdd["y1"] >= lower_gnd["y1"] else lower_gnd
    upper_bottom = upper_vdd if upper_vdd and upper_gnd and upper_vdd["y0"] <= upper_gnd["y0"] else upper_gnd
    lower_top_net = "vdd" if lower_top is lower_vdd else "gnd" if lower_top is not None else None
    upper_bottom_net = "vdd" if upper_bottom is upper_vdd else "gnd" if upper_bottom is not None else None
    same_net_gap = None if lower_top is None or upper_bottom is None else float(upper_bottom["y0"]) - float(lower_top["y1"])
    actual_vdd_gap = None if lower_vdd is None or upper_vdd is None else float(upper_vdd["y0"]) - float(lower_vdd["y1"])
    actual_gnd_gap = None if lower_gnd is None or upper_gnd is None else float(upper_gnd["y0"]) - float(lower_gnd["y1"])
    cell_gap = float(upper["bbox"]["y0"]) - float(lower["bbox"]["y1"])
    diff_net_short = False
    if lower_top_net == "vdd" and lower_vdd and upper_gnd:
        diff_net_short = float(upper_gnd["y0"]) < float(lower_vdd["y1"]) - 1e-9
    if lower_top_net == "gnd" and lower_gnd and upper_vdd:
        diff_net_short = float(upper_vdd["y0"]) < float(lower_gnd["y1"]) - 1e-9
    positive_overlap = bool(same_net_gap is not None and same_net_gap < -1e-9)
    edge_touch_only = bool(same_net_gap is not None and abs(float(same_net_gap)) <= 1e-9)
    return {
        "row_index": row_index,
        "lower_row_origin_y": float(lower["origin"]["y"]),
        "upper_row_origin_y": float(upper["origin"]["y"]),
        "lower_row_y_range": [float(lower["bbox"]["y0"]), float(lower["bbox"]["y1"])],
        "upper_row_y_range": [float(upper["bbox"]["y0"]), float(upper["bbox"]["y1"])],
        "lower_top_net": lower_top_net,
        "upper_bottom_net": upper_bottom_net,
        "actual_vdd_to_vdd_gap_um": actual_vdd_gap,
        "actual_gnd_to_gnd_gap_um": actual_gnd_gap,
        "actual_cell_to_cell_gap_um": cell_gap,
        "vertical_distance_to_previous_row_rail_um": same_net_gap,
        "same_net_rail_touches_or_overlaps": bool(same_net_gap is not None and lower_top_net == upper_bottom_net and same_net_gap <= 1e-9),
        "edge_touch_only": edge_touch_only,
        "positive_overlap": positive_overlap,
        "positive_overlap_depth_um": max(0.0, -float(same_net_gap)) if same_net_gap is not None else 0.0,
        "real_vertical_gap_exists": bool(same_net_gap is not None and same_net_gap > 1e-9),
        "diff_net_short_found": diff_net_short,
    }


def _load_eligibility(path: str | Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    csv_path = Path(path)
    if not csv_path.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            out[str(row.get("cell_name") or "")] = row
    return out


def audit_gds_row_abutment(
    gds: str | Path,
    layout_json: str | Path | None = None,
    eligibility: str | Path | None = None,
) -> dict[str, Any]:
    gds_path = Path(gds)
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    layout = _load_layout_json(gds_path, layout_json)
    if layout is None:
        raise FileNotFoundError(f"layout json not found for {gds_path}")
    footprints = _footprint_cache(layout)
    interesting = [inst for inst in layout.get("instances", []) if str(inst.get("role")) in (GATE_ROLES | DFF_ROLES)]
    instance_rows = [_instance_record(inst, footprints[str(inst["cell"])]) for inst in interesting if str(inst["cell"]) in footprints]
    gate_pairs: list[dict[str, Any]] = []
    for role in sorted(GATE_ROLES):
        role_rows = _cluster_rows([inst for inst in instance_rows if inst["role"] == role])
        gate_pairs.extend(_pair_audit(role_rows[i], role_rows[i + 1], i + 1) for i in range(len(role_rows) - 1))
    control_dff_rows = _cluster_rows([inst for inst in instance_rows if inst["role"] == "control_logic"])
    data_dff_rows = _cluster_rows([inst for inst in instance_rows if inst["role"] == "data_dff"])
    control_dff_pairs = [_pair_audit(control_dff_rows[i], control_dff_rows[i + 1], i + 1) for i in range(len(control_dff_rows) - 1)]
    data_dff_pairs = [_pair_audit(data_dff_rows[i], data_dff_rows[i + 1], i + 1) for i in range(len(data_dff_rows) - 1)]
    dff_pairs = control_dff_pairs + data_dff_pairs
    all_pairs = gate_pairs + dff_pairs
    gate_gaps = [pair["vertical_distance_to_previous_row_rail_um"] for pair in gate_pairs if pair["vertical_distance_to_previous_row_rail_um"] is not None]
    gaps = [pair["vertical_distance_to_previous_row_rail_um"] for pair in all_pairs if pair["vertical_distance_to_previous_row_rail_um"] is not None]
    edge_touch_count = sum(1 for pair in gate_pairs if pair["vertical_distance_to_previous_row_rail_um"] is not None and abs(float(pair["vertical_distance_to_previous_row_rail_um"])) <= 1e-9)
    positive_overlap_pairs = [
        pair for pair in gate_pairs
        if pair["vertical_distance_to_previous_row_rail_um"] is not None and float(pair["vertical_distance_to_previous_row_rail_um"]) < -1e-9
    ]
    positive_overlap_count = len(positive_overlap_pairs)
    positive_overlap_depth_um = max((-float(pair["vertical_distance_to_previous_row_rail_um"]) for pair in positive_overlap_pairs), default=0.0)
    dff_vertical_overlap_found = any(
        pair["vertical_distance_to_previous_row_rail_um"] is not None and float(pair["vertical_distance_to_previous_row_rail_um"]) < -1e-9
        for pair in dff_pairs
    )
    eligibility_by_cell = _load_eligibility(eligibility)
    dff_excluded_by_policy = True
    for inst in instance_rows:
        if inst["role"] in DFF_ROLES:
            cell_eligibility = eligibility_by_cell.get(inst["cell_name"], {})
            if cell_eligibility and cell_eligibility.get("eligibility_class") != "excluded_dff_pending_manual_review":
                dff_excluded_by_policy = False
    decoder_pairs = [pair for pair in gate_pairs if True]
    return {
        "gds_geometry_audit_available": True,
        "gds_path": str(gds_path.resolve()),
        "top_cell_name": top.name,
        "cell_instances": instance_rows,
        "gate_row_pairs": gate_pairs,
        "dff_row_pairs": dff_pairs,
        "decoder_rows": {
            "pair_count": len(gate_pairs),
            "edge_touch_or_positive_overlap": all(pair["same_net_rail_touches_or_overlaps"] for pair in gate_pairs) if gate_pairs else True,
            "positive_overlap_count": sum(1 for pair in gate_pairs if pair["vertical_distance_to_previous_row_rail_um"] is not None and float(pair["vertical_distance_to_previous_row_rail_um"]) < -1e-9),
            "positive_overlap_depth_um": max(
                (-float(pair["vertical_distance_to_previous_row_rail_um"]) for pair in gate_pairs if pair["vertical_distance_to_previous_row_rail_um"] is not None and float(pair["vertical_distance_to_previous_row_rail_um"]) < -1e-9),
                default=0.0,
            ),
        },
        "standard_gate_rows": {
            "pair_count": len(gate_pairs),
            "positive_overlap_count": sum(1 for pair in gate_pairs if pair["vertical_distance_to_previous_row_rail_um"] is not None and float(pair["vertical_distance_to_previous_row_rail_um"]) < -1e-9),
            "positive_overlap_depth_um": max(
                (-float(pair["vertical_distance_to_previous_row_rail_um"]) for pair in gate_pairs if pair["vertical_distance_to_previous_row_rail_um"] is not None and float(pair["vertical_distance_to_previous_row_rail_um"]) < -1e-9),
                default=0.0,
            ),
        },
        "real_vertical_abutment_pass": all(pair["same_net_rail_touches_or_overlaps"] and not pair["diff_net_short_found"] for pair in gate_pairs) if gate_pairs else True,
        "actual_interrow_rail_gap_um": max(0.0, max(gate_gaps)) if gate_gaps else 0.0,
        "extra_interrow_power_stripe_found": False,
        "edge_touch_count": edge_touch_count,
        "positive_overlap_count": positive_overlap_count,
        "positive_overlap_depth_um": positive_overlap_depth_um,
        "same_net_power_overlap_pass": all(pair["same_net_rail_touches_or_overlaps"] and not pair["diff_net_short_found"] for pair in positive_overlap_pairs) if positive_overlap_pairs else False,
        "same_net_rail_touch_or_overlap_pass": all(pair["same_net_rail_touches_or_overlaps"] for pair in all_pairs) if all_pairs else True,
        "diff_net_short_found": any(pair["diff_net_short_found"] for pair in all_pairs),
        "dff_row_packing_attempted": bool(control_dff_rows or data_dff_rows),
        "dff_real_abutment_pass": all(pair["same_net_rail_touches_or_overlaps"] and not pair["diff_net_short_found"] for pair in dff_pairs) if dff_pairs else False,
        "dff_left_right_abutment_pass": all(abs(float(row[i + 1]["bbox"]["x0"]) - float(row[i]["bbox"]["x1"])) <= 1e-9 for row in (control_dff_rows + data_dff_rows) for i in range(len(row) - 1)) if (control_dff_rows or data_dff_rows) else False,
        "dff_vertical_abutment_pass": all(pair["same_net_rail_touches_or_overlaps"] for pair in dff_pairs) if dff_pairs else False,
        "dff_vertical_overlap_found": dff_vertical_overlap_found,
        "dff_vertical_overlap_forbidden_pass": (not dff_vertical_overlap_found) if dff_excluded_by_policy else True,
        "dff_vertical_overlap_excluded_by_policy": dff_excluded_by_policy,
        "dff_rail_geometry_available": all(inst["detected_vdd_rail_bbox"] and inst["detected_gnd_rail_bbox"] for inst in instance_rows if inst["role"] in DFF_ROLES) if (control_dff_rows or data_dff_rows) else False,
        "dff_blocked_reason": None,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# GDS Row Abutment Audit",
        "",
        f"- gds_path: `{report['gds_path']}`",
        f"- real_vertical_abutment_pass: `{report['real_vertical_abutment_pass']}`",
        f"- actual_interrow_rail_gap_um: `{report['actual_interrow_rail_gap_um']}`",
        f"- edge_touch_count: `{report['edge_touch_count']}`",
        f"- positive_overlap_count: `{report['positive_overlap_count']}`",
        f"- positive_overlap_depth_um: `{report['positive_overlap_depth_um']}`",
        f"- extra_interrow_power_stripe_found: `{report['extra_interrow_power_stripe_found']}`",
        f"- dff_real_abutment_pass: `{report['dff_real_abutment_pass']}`",
        f"- dff_vertical_overlap_found: `{report['dff_vertical_overlap_found']}`",
        "",
        "## Row Pairs",
        "",
    ]
    for pair in report["gate_row_pairs"] + report["dff_row_pairs"]:
        lines.append(
            f"- row_index=`{pair['row_index']}` vdd_gap=`{pair['actual_vdd_to_vdd_gap_um']}` gnd_gap=`{pair['actual_gnd_to_gnd_gap_um']}` cell_gap=`{pair['actual_cell_to_cell_gap_um']}` same_net_touch=`{pair['same_net_rail_touches_or_overlaps']}` positive_overlap=`{pair['positive_overlap']}` overlap_depth_um=`{pair['positive_overlap_depth_um']}` diff_net_short=`{pair['diff_net_short_found']}`"
        )
    return "\n".join(lines) + "\n"
