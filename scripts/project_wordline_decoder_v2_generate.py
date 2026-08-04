#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.composite_hierarchy_closure import verify_composite_hierarchy_closure
from sram_layoutgen.openyield_adapter.composite_pin_namespace_verifier import verify_composite_pin_namespace
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import geometry_fingerprint, non_text_geometry_fingerprint, run_cell_drc
from sram_layoutgen.openyield_adapter.teamb_composite_helper import (
    ChildSpec,
    add_top_label,
    annotate_from_bboxes,
    bridge_power_rails,
    clone_children,
    instantiate_children,
    make_review_atlas,
    place_children_single_row,
    read_json,
    write_csv,
    write_gds,
    write_json,
    write_text,
)
from sram_layoutgen.tech import Tech


OUT_DIR = REPO_ROOT / "outputs" / "PROJECT_wordline_decoder_v2_regen" / "current_supported_config"
PRIMARY_REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
TOP_NAME = "wordline_decoder_v2"


def _center(bbox: dict[str, float]) -> tuple[float, float]:
    return (round((bbox["lx"] + bbox["rx"]) * 0.5, 6), round((bbox["by"] + bbox["uy"]) * 0.5, 6))


def _m1_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=11, datatype=0))


def _m2_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=13, datatype=0))


def _via1_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=12, datatype=0))


def _m3_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=15, datatype=0))


def _via2_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=14, datatype=0))


def _snap_box(box: dict[str, float], grid: float) -> dict[str, float]:
    return {k: round(round(float(v) / grid) * grid, 6) for k, v in box.items()}


def _direct_m1_bridge(
    *,
    top: gdstk.Cell,
    tech: Tech,
    left_box: dict[str, float],
    right_box: dict[str, float],
) -> dict[str, float]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    by = max(float(left_box["by"]), float(right_box["by"]))
    uy = min(float(left_box["uy"]), float(right_box["uy"]))
    if uy - by < m1_w:
        cy = round((float(right_box["by"]) + float(right_box["uy"])) * 0.5, 6)
        by = cy - m1_w * 0.5
        uy = cy + m1_w * 0.5
    bridge = _snap_box(
        {
            "lx": float(left_box["lx"]),
            "by": by,
            "rx": float(right_box["rx"]),
            "uy": uy,
        },
        grid,
    )
    _m1_rect(top, bridge)
    return bridge


def _bus_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    endpoint_boxes: list[dict[str, float]],
    track_y: float,
    top_pin_name: str | None = None,
    top_pin_x: float | None = None,
    branch_x_shift: float = 0.0,
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    m3_w = tech.layer("m3").min_width
    via = tech.via_between("m1", "m2")
    via2 = tech.via_between("m2", "m3")
    assert via is not None
    assert via2 is not None
    via_enc = 0.035
    landing_half_w_m1 = max(m1_w * 0.5, via.size * 0.5 + via_enc)
    landing_half_w_m2 = max(m2_w * 0.5, via.size * 0.5 + via_enc)
    landing_half_w_m3 = max(m3_w * 0.5, via2.size * 0.5 + via_enc)
    centers = [_center(box) for box in endpoint_boxes]
    branch_centers = [round(cx + branch_x_shift, 6) for cx, _ in centers]
    min_cx = min(branch_centers)
    max_cx = max(branch_centers)
    route_rows: list[dict[str, Any]] = []
    pin_bbox: dict[str, float] | None = None
    track_y = round(round(track_y / grid) * grid, 6)
    for box, (cx, cy), branch_cx in zip(endpoint_boxes, centers, branch_centers):
        escape_up = track_y >= cy
        via_cy = (
            max(cy, float(box["uy"]) + via.size * 0.5 + via_enc)
            if escape_up
            else min(cy, float(box["by"]) - via.size * 0.5 - via_enc)
        )
        m1_landing = _snap_box(
            {
                "lx": cx - landing_half_w_m1,
                "by": min(float(box["by"]), via_cy - landing_half_w_m1),
                "rx": cx + landing_half_w_m1,
                "uy": max(float(box["uy"]), via_cy + landing_half_w_m1),
            },
            grid,
        )
        m2_lower_pad = _snap_box(
            {
                "lx": branch_cx - landing_half_w_m2,
                "by": via_cy - landing_half_w_m2,
                "rx": branch_cx + landing_half_w_m2,
                "uy": via_cy + landing_half_w_m2,
            },
            grid,
        )
        m2_upper_pad = _snap_box(
            {
                "lx": branch_cx - landing_half_w_m2,
                "by": track_y - landing_half_w_m2,
                "rx": branch_cx + landing_half_w_m2,
                "uy": track_y + landing_half_w_m2,
            },
            grid,
        )
        m2_branch = _snap_box(
            {
                "lx": branch_cx - m2_w * 0.5,
                "by": min(via_cy, track_y),
                "rx": branch_cx + m2_w * 0.5,
                "uy": max(via_cy, track_y),
            },
            grid,
        )
        via_bbox = _snap_box(
            {
                "lx": cx - via.size * 0.5,
                "by": via_cy - via.size * 0.5,
                "rx": cx + via.size * 0.5,
                "uy": via_cy + via.size * 0.5,
            },
            grid,
        )
        _m1_rect(top, m1_landing)
        _m2_rect(top, m2_lower_pad)
        _m2_rect(top, m2_upper_pad)
        _m2_rect(top, m2_branch)
        _via1_rect(top, via_bbox)
        via2_bbox = _snap_box(
            {
                "lx": branch_cx - via2.size * 0.5,
                "by": track_y - via2.size * 0.5,
                "rx": branch_cx + via2.size * 0.5,
                "uy": track_y + via2.size * 0.5,
            },
            grid,
        )
        m3_landing = _snap_box(
            {
                "lx": branch_cx - landing_half_w_m3,
                "by": track_y - landing_half_w_m3,
                "rx": branch_cx + landing_half_w_m3,
                "uy": track_y + landing_half_w_m3,
            },
            grid,
        )
        _m3_rect(top, m3_landing)
        _via2_rect(top, via2_bbox)
        route_rows.append(
            {
                "m1_landing_bbox": m1_landing,
                "m2_lower_pad_bbox": m2_lower_pad,
                "m2_upper_pad_bbox": m2_upper_pad,
                "m2_branch_bbox": m2_branch,
                "via1_bbox": via_bbox,
                "m3_landing_bbox": m3_landing,
                "via2_bbox": via2_bbox,
            }
        )
    if top_pin_name is not None and top_pin_x is not None:
        pin_bbox = _snap_box(
            {
                "lx": top_pin_x - landing_half_w_m2,
                "by": track_y - landing_half_w_m2,
                "rx": top_pin_x + landing_half_w_m2,
                "uy": track_y + landing_half_w_m2,
            },
            grid,
        )
        _m2_rect(top, pin_bbox)
        pin_via2_bbox = _snap_box(
            {
                "lx": top_pin_x - via2.size * 0.5,
                "by": track_y - via2.size * 0.5,
                "rx": top_pin_x + via2.size * 0.5,
                "uy": track_y + via2.size * 0.5,
            },
            grid,
        )
        pin_m3_landing = _snap_box(
            {
                "lx": top_pin_x - landing_half_w_m3,
                "by": track_y - landing_half_w_m3,
                "rx": top_pin_x + landing_half_w_m3,
                "uy": track_y + landing_half_w_m3,
            },
            grid,
        )
        _m3_rect(top, pin_m3_landing)
        _via2_rect(top, pin_via2_bbox)
        route_rows.append({"top_pin_bbox": pin_bbox, "top_pin_via2_bbox": pin_via2_bbox, "top_pin_m3_landing_bbox": pin_m3_landing})
        min_cx = min(min_cx, top_pin_x)
        max_cx = max(max_cx, top_pin_x)
    trunk = _snap_box(
        {
            "lx": min_cx,
            "by": track_y - landing_half_w_m3,
            "rx": max_cx,
            "uy": track_y + landing_half_w_m3,
        },
        grid,
    )
    _m3_rect(top, trunk)
    route_rows.append({"m3_trunk_bbox": trunk})
    return {"route_rows": route_rows, "top_pin_bbox": pin_bbox}


def _child_specs() -> list[ChildSpec]:
    pinv_dir = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/PINV_NW90_PW270_L50"
    and3_dir = PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND3"
    wl_driver_dir = REPO_ROOT / "outputs/PROJECT_wordline_driver_v2_regen/current_supported_config"
    binding = read_json(REPO_ROOT / "docs/WORDLINE_DECODER_V2_SOURCE_BINDING.json")
    specs: list[ChildSpec] = []
    for row in binding["binding_rows"]:
        cell_name = row["resolved_physical_cell_name"]
        if cell_name == "PINV_NW90_PW270_L50":
            specs.append(
                ChildSpec(
                    instance_name=row["instance_name"],
                    logical_module="PINV",
                    physical_cell_name="PINV_NW90_PW270_L50",
                    gds_path=pinv_dir / "PINV_NW90_PW270_L50.gds",
                    pin_map_path=pinv_dir / "PINV_NW90_PW270_L50_pin_map.json",
                )
            )
        elif cell_name == "AND3_PNAND3_PINV_FPDK45":
            specs.append(
                ChildSpec(
                    instance_name=row["instance_name"],
                    logical_module="AND3",
                    physical_cell_name="AND3_PNAND3_PINV_FPDK45",
                    gds_path=and3_dir / "clean.gds",
                    pin_map_path=REPO_ROOT / "outputs/PROJECT_decoder_v2_formal_gate_pinmaps/current_supported_config/AND3_pin_map.json",
                )
            )
        elif cell_name == "wordline_driver_v2":
            specs.append(
                ChildSpec(
                    instance_name=row["instance_name"],
                    logical_module="WORDLINEDRIVER",
                    physical_cell_name="wordline_driver_v2",
                    gds_path=wl_driver_dir / "wordline_driver_v2.gds",
                    pin_map_path=wl_driver_dir / "wordline_driver_v2_pin_map.json",
                )
            )
        else:
            raise ValueError(f"unsupported child cell: {cell_name}")
    return specs


def _build_endpoints(placed_children: list[Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    binding = read_json(REPO_ROOT / "docs/WORDLINE_DECODER_V2_SOURCE_BINDING.json")
    placed_by_name = {item.spec.instance_name: item for item in placed_children}
    endpoints_by_net: dict[str, list[dict[str, Any]]] = {}
    instance_table: dict[str, Any] = {}
    for row in binding["binding_rows"]:
        item = placed_by_name[row["instance_name"]]
        child_pins = json.loads(row["child_pin_order"])
        parent_nets = json.loads(row["parent_net_connections"])
        instance_table[row["instance_name"]] = {
            "logical_child_type": row["logical_child_type"],
            "resolved_physical_cell_name": row["resolved_physical_cell_name"],
            "placement_origin": list(item.placement_origin),
        }
        for pin_name, net_name in zip(child_pins, parent_nets):
            bbox = item.placed_pin_map[pin_name][0]
            endpoints_by_net.setdefault(net_name, []).append(
                {
                    "endpoint_name": f"{row['instance_name']}.{pin_name}",
                    "bbox": bbox,
                }
            )
    return endpoints_by_net, instance_table


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tech = Tech.freepdk45(REPO_ROOT)
    specs = _child_specs()
    lib, placed, clone_rows = clone_children(specs, OUT_DIR / "clones")
    placed = place_children_single_row(placed, start_x=0.0, start_y=0.0, gap=0.35)
    top = instantiate_children(lib, TOP_NAME, placed)
    rails = bridge_power_rails(top, placed, tech)
    endpoints_by_net, instance_table = _build_endpoints(placed)
    placed_by_name = {item.spec.instance_name: item for item in placed}

    child_boxes = [{"label": item.spec.instance_name, "bbox": item.bbox} for item in placed]
    min_x = min(item.bbox[0] for item in placed)

    top_pin_bboxes: dict[str, dict[str, float]] = {"VDD": rails["VDD"], "VSS": rails["VSS"]}
    route_report: dict[str, Any] = {"input_buses": {}, "internal_buses": {}, "pair_routes": {}}
    top_pin_labels = ["A0", "A1", "A2", "EN", "DEC_WL0", "DEC_WL1", "DEC_WL2", "DEC_WL3", "DEC_WL4", "DEC_WL5", "DEC_WL6", "DEC_WL7", "VDD", "VSS"]

    input_tracks = {"EN": 2.15, "A0": 2.40, "A1": 2.65, "A2": 2.90}
    complement_tracks = {"A2b": 3.15, "A0b": 3.40, "A1b": 3.65}
    top_pin_x = min_x - 0.35

    for net_name in ["A0", "A1", "A2", "EN"]:
        route = _bus_route(
            top=top,
            tech=tech,
            endpoint_boxes=[row["bbox"] for row in endpoints_by_net[net_name]],
            track_y=input_tracks[net_name],
            top_pin_name=net_name,
            top_pin_x=top_pin_x,
            branch_x_shift=-0.005 if net_name == "A0" else 0.0,
        )
        route_report["input_buses"][net_name] = route
        assert route["top_pin_bbox"] is not None
        top_pin_bboxes[net_name] = route["top_pin_bbox"]
        add_top_label(top, net_name, route["top_pin_bbox"])

    for net_name in ["A0b", "A1b", "A2b"]:
        route = _bus_route(
            top=top,
            tech=tech,
            endpoint_boxes=[row["bbox"] for row in endpoints_by_net[net_name]],
            track_y=complement_tracks[net_name],
            branch_x_shift=-0.005 if net_name == "A0b" else 0.0,
        )
        route_report["internal_buses"][net_name] = route

    for bit in range(8):
        and3_box = placed_by_name[f"and3_pre_{bit}"].placed_pin_map["Z"][0]
        wl_driver_box = placed_by_name[f"wl_driver_{bit}"].placed_pin_map["A"][0]
        bridge = _direct_m1_bridge(top=top, tech=tech, left_box=and3_box, right_box=wl_driver_box)
        route_report["pair_routes"][f"WL{bit}_pre_to_DEC_WL{bit}"] = {"m1_bridge_bbox": bridge}
        output_box = placed_by_name[f"wl_driver_{bit}"].placed_pin_map["Z"][0]
        top_pin_bboxes[f"DEC_WL{bit}"] = output_box
        add_top_label(top, f"DEC_WL{bit}", output_box)

    add_top_label(top, "VDD", rails["VDD"])
    add_top_label(top, "VSS", rails["VSS"])

    clean_gds = OUT_DIR / f"{TOP_NAME}.gds"
    write_gds(lib, clean_gds)
    pin_map_payload = {name: [bbox] for name, bbox in top_pin_bboxes.items()}
    write_json(OUT_DIR / f"{TOP_NAME}_pin_map.json", pin_map_payload)

    connectivity = verify_hierarchical_connectivity(
        gds_path=clean_gds,
        top_name=TOP_NAME,
        endpoints_by_net=endpoints_by_net,
        top_pin_bboxes=top_pin_bboxes,
    )
    namespace = verify_composite_pin_namespace(clean_gds, TOP_NAME, top_pin_labels)
    hierarchy = verify_composite_hierarchy_closure(clean_gds, TOP_NAME)
    drc = run_cell_drc(
        Path("/usr/bin/klayout"),
        REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc",
        clean_gds,
        TOP_NAME,
        OUT_DIR / "drc",
    )
    annotated = OUT_DIR / f"{TOP_NAME}_annotated.gds"
    review_atlas = OUT_DIR / f"{TOP_NAME}_review_atlas.gds"
    annotate_from_bboxes(clean_gds, TOP_NAME, child_boxes, annotated)
    atlas_meta = make_review_atlas(clean_gds, annotated, TOP_NAME, review_atlas)
    gate = {
        "scope": "project_wordline_decoder_v2_regen",
        "top_name": TOP_NAME,
        "git_head": read_json(REPO_ROOT / "docs/PROJECT_CURRENT_STATUS.json")["current_git_head"],
        "drc_marker_count": drc["marker_count"],
        "connectivity_passed": connectivity["physical_connectivity_verification_passed"],
        "namespace_top_label_set_exact": namespace["top_canonical_label_set_exact"],
        "namespace_internal_child_label_leakage_count": namespace["internal_child_label_leakage_count"],
        "hierarchy_passed": hierarchy["reference_closure_passed"],
        "passed": drc["marker_count"] == 0
        and connectivity["physical_connectivity_verification_passed"]
        and namespace["top_canonical_label_set_exact"]
        and namespace["internal_child_label_leakage_count"] == 0
        and hierarchy["reference_closure_passed"],
        "blocking_reasons": [],
    }
    if drc["marker_count"] != 0:
        gate["blocking_reasons"].append("DRC_NONZERO")
    if not connectivity["physical_connectivity_verification_passed"]:
        gate["blocking_reasons"].append("CONNECTIVITY_FAILED")
    if not namespace["top_canonical_label_set_exact"] or namespace["internal_child_label_leakage_count"] != 0:
        gate["blocking_reasons"].append("PIN_NAMESPACE_FAILED")
    if not hierarchy["reference_closure_passed"]:
        gate["blocking_reasons"].append("HIERARCHY_FAILED")

    write_json(OUT_DIR / "WORDLINE_DECODER_V2_CLONE_ROWS.json", clone_rows)
    write_json(OUT_DIR / "WORDLINE_DECODER_V2_INSTANCE_TABLE.json", instance_table)
    write_json(OUT_DIR / "WORDLINE_DECODER_V2_ROUTE_REPORT.json", route_report)
    write_json(OUT_DIR / "WORDLINE_DECODER_V2_CONNECTIVITY.json", connectivity)
    write_json(OUT_DIR / "WORDLINE_DECODER_V2_PIN_NAMESPACE.json", namespace)
    write_json(OUT_DIR / "WORDLINE_DECODER_V2_HIERARCHY.json", hierarchy)
    write_json(OUT_DIR / "WORDLINE_DECODER_V2_DRC.json", drc)
    write_json(OUT_DIR / "WORDLINE_DECODER_V2_GATE.json", gate)
    write_json(
        OUT_DIR / "WORDLINE_DECODER_V2_FINGERPRINTS.json",
        {
            "geometry_fingerprint": geometry_fingerprint(clean_gds, TOP_NAME),
            "non_text_geometry_fingerprint": non_text_geometry_fingerprint(clean_gds, TOP_NAME),
        },
    )
    write_json(
        OUT_DIR / "WORDLINE_DECODER_V2_MANIFEST.json",
        {
            "clean_gds": str(clean_gds.resolve()),
            "annotated_gds": str(annotated.resolve()),
            "review_atlas_gds": str(review_atlas.resolve()),
            "pin_map": str((OUT_DIR / f"{TOP_NAME}_pin_map.json").resolve()),
            "atlas_meta": atlas_meta,
        },
    )
    write_csv(
        OUT_DIR / "WORDLINE_DECODER_V2_PLACEMENT.csv",
        [
            {
                "instance_name": item.spec.instance_name,
                "logical_module": item.spec.logical_module,
                "x0": item.bbox[0],
                "y0": item.bbox[1],
                "x1": item.bbox[2],
                "y1": item.bbox[3],
            }
            for item in placed
        ],
    )
    write_text(
        OUT_DIR / "WORDLINE_DECODER_V2_SUMMARY.md",
        "\n".join(
            [
                "# Wordline Decoder V2 Regenerated Child Summary",
                "",
                f"- child_count: `{len(placed)}`",
                f"- drc_marker_count: `{drc['marker_count']}`",
                f"- connectivity_passed: `{connectivity['physical_connectivity_verification_passed']}`",
                f"- namespace_top_label_set_exact: `{namespace['top_canonical_label_set_exact']}`",
                f"- namespace_internal_child_label_leakage_count: `{namespace['internal_child_label_leakage_count']}`",
                f"- hierarchy_passed: `{hierarchy['reference_closure_passed']}`",
                f"- gate_passed: `{gate['passed']}`",
                "",
            ]
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
