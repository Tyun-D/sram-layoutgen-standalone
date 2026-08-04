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


OUT_DIR = REPO_ROOT / "outputs" / "PROJECT_wordline_driver_v2_regen" / "current_supported_config"
PRIMARY_REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
TOP_NAME = "wordline_driver_v2"


def _center(bbox: dict[str, float]) -> tuple[float, float]:
    return (round((bbox["lx"] + bbox["rx"]) * 0.5, 6), round((bbox["by"] + bbox["uy"]) * 0.5, 6))


def _m1_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=11, datatype=0))


def _m2_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=13, datatype=0))


def _via1_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=12, datatype=0))


def _snap_box(box: dict[str, float], grid: float) -> dict[str, float]:
    return {k: round(round(float(v) / grid) * grid, 6) for k, v in box.items()}


def _bus_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    endpoint_boxes: list[dict[str, float]],
    track_y: float,
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    via = tech.via_between("m1", "m2")
    assert via is not None
    via_enc = 0.035
    landing_half_w_m1 = max(m1_w * 0.5, via.size * 0.5 + via_enc)
    landing_half_w_m2 = max(m2_w * 0.5, via.size * 0.5 + via_enc)
    centers = [_center(box) for box in endpoint_boxes]
    min_cx = min(cx for cx, _ in centers)
    max_cx = max(cx for cx, _ in centers)
    route_rows: list[dict[str, Any]] = []
    track_y = round(round(track_y / grid) * grid, 6)
    for box, (cx, cy) in zip(endpoint_boxes, centers):
        via_cy = track_y
        m1_landing = _snap_box(
            {
                "lx": cx - landing_half_w_m1,
                "by": min(float(box["by"]), via_cy - landing_half_w_m1),
                "rx": cx + landing_half_w_m1,
                "uy": max(float(box["uy"]), via_cy + landing_half_w_m1),
            },
            grid,
        )
        m2_landing = _snap_box(
            {
                "lx": cx - landing_half_w_m2,
                "by": track_y - landing_half_w_m2,
                "rx": cx + landing_half_w_m2,
                "uy": track_y + landing_half_w_m2,
            },
            grid,
        )
        via_bbox = _snap_box(
            {
                "lx": cx - via.size * 0.5,
                "by": track_y - via.size * 0.5,
                "rx": cx + via.size * 0.5,
                "uy": track_y + via.size * 0.5,
            },
            grid,
        )
        _m1_rect(top, m1_landing)
        _m2_rect(top, m2_landing)
        _via1_rect(top, via_bbox)
        route_rows.append({"m1_landing_bbox": m1_landing, "m2_landing_bbox": m2_landing, "via1_bbox": via_bbox})
    trunk = _snap_box(
        {
            "lx": min_cx,
            "by": track_y - landing_half_w_m2,
            "rx": max_cx,
            "uy": track_y + landing_half_w_m2,
        },
        grid,
    )
    _m2_rect(top, trunk)
    route_rows.append({"m2_trunk_bbox": trunk})
    return {"route_rows": route_rows}


def _child_specs() -> list[ChildSpec]:
    pinv_dir = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/PINV_NW90_PW270_L50"
    pnand2_dir = PRIMARY_REPO_ROOT / "outputs/TeamB_PNAND2_reference_demo/current_supported_config"
    return [
        ChildSpec(
            instance_name="pnand2_stage",
            logical_module="PNAND2",
            physical_cell_name="PNAND2_NW180_PW270_L50_FPDK45",
            gds_path=pnand2_dir / "PNAND2_NW180_PW270_L50_FPDK45.gds",
            pin_map_path=pnand2_dir / "PNAND2_pin_map.json",
        ),
        ChildSpec(
            instance_name="inv_stage",
            logical_module="PINV",
            physical_cell_name="PINV_NW90_PW270_L50",
            gds_path=pinv_dir / "PINV_NW90_PW270_L50.gds",
            pin_map_path=pinv_dir / "PINV_NW90_PW270_L50_pin_map.json",
        ),
    ]


def _build_endpoints(placed_children: list[Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    binding = read_json(REPO_ROOT / "docs/WORDLINE_DRIVER_V2_SOURCE_BINDING.json")
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
            endpoints_by_net.setdefault(net_name, []).append({"endpoint_name": f"{row['instance_name']}.{pin_name}", "bbox": bbox})
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

    top_pin_bboxes: dict[str, dict[str, float]] = {
        "VDD": rails["VDD"],
        "VSS": rails["VSS"],
        "A": placed_by_name["pnand2_stage"].placed_pin_map["A"][0],
        "B": placed_by_name["pnand2_stage"].placed_pin_map["B"][0],
        "Z": placed_by_name["inv_stage"].placed_pin_map["Z"][0],
    }

    route_report = {
        "internal_net": _bus_route(
            top=top,
            tech=tech,
            endpoint_boxes=[
                placed_by_name["pnand2_stage"].placed_pin_map["Z"][0],
                placed_by_name["inv_stage"].placed_pin_map["A"][0],
            ],
            track_y=1.10,
        )
    }

    for pin_name in ["A", "B", "Z", "VDD", "VSS"]:
        add_top_label(top, pin_name, top_pin_bboxes[pin_name])

    clean_gds = OUT_DIR / f"{TOP_NAME}.gds"
    write_gds(lib, clean_gds)
    write_json(OUT_DIR / f"{TOP_NAME}_pin_map.json", {name: [bbox] for name, bbox in top_pin_bboxes.items()})

    connectivity = verify_hierarchical_connectivity(
        gds_path=clean_gds,
        top_name=TOP_NAME,
        endpoints_by_net=endpoints_by_net,
        top_pin_bboxes=top_pin_bboxes,
    )
    namespace = verify_composite_pin_namespace(clean_gds, TOP_NAME, ["A", "B", "Z", "VDD", "VSS"])
    hierarchy = verify_composite_hierarchy_closure(clean_gds, TOP_NAME)
    drc = run_cell_drc(Path("/usr/bin/klayout"), REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc", clean_gds, TOP_NAME, OUT_DIR / "drc")
    annotated = OUT_DIR / f"{TOP_NAME}_annotated.gds"
    review_atlas = OUT_DIR / f"{TOP_NAME}_review_atlas.gds"
    annotate_from_bboxes(clean_gds, TOP_NAME, child_boxes, annotated)
    atlas_meta = make_review_atlas(clean_gds, annotated, TOP_NAME, review_atlas)
    gate = {
        "scope": "project_wordline_driver_v2_regen",
        "top_name": TOP_NAME,
        "git_head": read_json(REPO_ROOT / "docs/PROJECT_CURRENT_STATUS.json")["current_git_head"],
        "drc_marker_count": drc["marker_count"],
        "connectivity_passed": connectivity["physical_connectivity_verification_passed"],
        "namespace_top_label_set_exact": namespace["top_canonical_label_set_exact"],
        "namespace_internal_child_label_leakage_count": namespace["internal_child_label_leakage_count"],
        "hierarchy_passed": hierarchy["reference_closure_passed"],
        "passed": drc["marker_count"] == 0 and connectivity["physical_connectivity_verification_passed"] and namespace["top_canonical_label_set_exact"] and namespace["internal_child_label_leakage_count"] == 0 and hierarchy["reference_closure_passed"],
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

    write_json(OUT_DIR / "WORDLINE_DRIVER_V2_CLONE_ROWS.json", clone_rows)
    write_json(OUT_DIR / "WORDLINE_DRIVER_V2_INSTANCE_TABLE.json", instance_table)
    write_json(OUT_DIR / "WORDLINE_DRIVER_V2_ROUTE_REPORT.json", route_report)
    write_json(OUT_DIR / "WORDLINE_DRIVER_V2_CONNECTIVITY.json", connectivity)
    write_json(OUT_DIR / "WORDLINE_DRIVER_V2_PIN_NAMESPACE.json", namespace)
    write_json(OUT_DIR / "WORDLINE_DRIVER_V2_HIERARCHY.json", hierarchy)
    write_json(OUT_DIR / "WORDLINE_DRIVER_V2_DRC.json", drc)
    write_json(OUT_DIR / "WORDLINE_DRIVER_V2_GATE.json", gate)
    write_json(OUT_DIR / "WORDLINE_DRIVER_V2_FINGERPRINTS.json", {"geometry_fingerprint": geometry_fingerprint(clean_gds, TOP_NAME), "non_text_geometry_fingerprint": non_text_geometry_fingerprint(clean_gds, TOP_NAME)})
    write_json(OUT_DIR / "WORDLINE_DRIVER_V2_MANIFEST.json", {"clean_gds": str(clean_gds.resolve()), "annotated_gds": str(annotated.resolve()), "review_atlas_gds": str(review_atlas.resolve()), "pin_map": str((OUT_DIR / f"{TOP_NAME}_pin_map.json").resolve()), "atlas_meta": atlas_meta})
    write_csv(OUT_DIR / "WORDLINE_DRIVER_V2_PLACEMENT.csv", [{"instance_name": item.spec.instance_name, "logical_module": item.spec.logical_module, "x0": item.bbox[0], "y0": item.bbox[1], "x1": item.bbox[2], "y1": item.bbox[3]} for item in placed])
    write_text(
        OUT_DIR / "WORDLINE_DRIVER_V2_SUMMARY.md",
        "\n".join(
            [
                "# Wordline Driver V2 Regenerated Child Summary",
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
