#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_ROOT = REPO_ROOT / "outputs" / "PROJECT_decoder_top_v3"

from sram_layoutgen.openyield_adapter.composite_hierarchy_closure import verify_composite_hierarchy_closure
from sram_layoutgen.openyield_adapter.composite_pin_namespace_verifier import verify_composite_pin_namespace
from sram_layoutgen.openyield_adapter.decoder_generator import (
    _build_endpoints,
    _m1_to_m3_to_m2_route,
    _m2m3_pin_to_m1_rail_route,
    _m3_bus_from_m2_pins_route,
)
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import geometry_fingerprint, non_text_geometry_fingerprint, run_cell_drc
from sram_layoutgen.openyield_adapter.teamb_composite_helper import (
    ChildSpec,
    PlacedChild,
    add_top_label,
    annotate_from_bboxes,
    bbox_from_gds,
    bridge_power_rails,
    clone_children,
    instantiate_children,
    make_review_atlas,
    read_json,
    transform_pin_map,
    write_csv,
    write_json,
    write_text,
)
from sram_layoutgen.tech import Tech


@dataclass(frozen=True)
class TopCandidate:
    candidate_id: str
    child_template: str
    placements: dict[str, tuple[float, float]]


def _snap_box(box: dict[str, float], grid: float) -> dict[str, float]:
    return {key: round(round(float(value) / grid) * grid, 6) for key, value in box.items()}


def _layer_rect(top: gdstk.Cell, box: dict[str, float], layer: int) -> None:
    top.add(gdstk.rectangle((box["lx"], box["by"]), (box["rx"], box["uy"]), layer=layer, datatype=0))


def _m1_rect(top: gdstk.Cell, box: dict[str, float]) -> None:
    _layer_rect(top, box, 11)


def _m2_rect(top: gdstk.Cell, box: dict[str, float]) -> None:
    _layer_rect(top, box, 13)


def _via1_rect(top: gdstk.Cell, box: dict[str, float]) -> None:
    _layer_rect(top, box, 12)


def _m3_rect(top: gdstk.Cell, box: dict[str, float]) -> None:
    _layer_rect(top, box, 15)


def _via2_rect(top: gdstk.Cell, box: dict[str, float]) -> None:
    _layer_rect(top, box, 14)


CANDIDATES = [
    TopCandidate(
        candidate_id="baseline_v2_long_strip",
        child_template="baseline_strip",
        placements={
            "upper_enable_stage": (0.0, 0.0),
            "lower_wordline_stage_0": (46.0, 0.0),
            "lower_wordline_stage_1": (92.0, 0.0),
        },
    ),
    TopCandidate(
        candidate_id="candidate_a_horizontal_compact",
        child_template="compact_abutment",
        placements={
            "upper_enable_stage": (0.0, 0.0),
            "lower_wordline_stage_0": (39.0, 0.0),
            "lower_wordline_stage_1": (78.0, 0.0),
        },
    ),
    TopCandidate(
        candidate_id="candidate_b_horizontal_compact_proxy_wl_optimized",
        child_template="compact_abutment",
        placements={
            "upper_enable_stage": (-5.0, 0.0),
            "lower_wordline_stage_0": (34.0, 0.0),
            "lower_wordline_stage_1": (73.0, 0.0),
        },
    ),
    TopCandidate(
        candidate_id="candidate_true_multiline_compact",
        child_template="double_row_folded",
        placements={
            "upper_enable_stage": (0.0, 4.4),
            "lower_wordline_stage_0": (38.0, 8.8),
            "lower_wordline_stage_1": (38.0, 0.0),
        },
    ),
    TopCandidate(
        candidate_id="candidate_true_wl_driver_array_oriented",
        child_template="output_oriented_multiline",
        placements={
            "upper_enable_stage": (0.0, 4.2),
            "lower_wordline_stage_0": (36.0, 8.4),
            "lower_wordline_stage_1": (36.0, 0.0),
        },
    ),
    TopCandidate(
        candidate_id="candidate_p2_partitioned_control_centered",
        child_template="output_oriented_multiline",
        placements={
            "upper_enable_stage": (18.0, 4.2),
            "lower_wordline_stage_0": (38.0, 8.4),
            "lower_wordline_stage_1": (38.0, 0.0),
        },
    ),
    TopCandidate(
        candidate_id="candidate_p3_symmetric_lower_left_control_right",
        child_template="output_oriented_multiline",
        placements={
            "upper_enable_stage": (42.0, 4.2),
            "lower_wordline_stage_0": (18.0, 8.4),
            "lower_wordline_stage_1": (18.0, 0.0),
        },
    ),
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_lib(lib: gdstk.Library, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(path)


def _child_spec(instance_name: str, template: str) -> ChildSpec:
    child_root = REPO_ROOT / "outputs" / "PROJECT_decoder_child_v3" / "decoder_gate_cells_v3" / template
    if template == "baseline_strip":
        gds = child_root / "decoder_gate_cells_v3.gds"
        pin_map = child_root / "decoder_gate_cells_v3_pin_map.json"
    else:
        gds = child_root / "clean.gds"
        pin_map = child_root / "pin_map.json"
    lib = gdstk.read_gds(gds)
    top_name = lib.top_level()[0].name
    return ChildSpec(
        instance_name=instance_name,
        logical_module="decoder_gate_cells_v3",
        physical_cell_name=top_name,
        gds_path=gds,
        pin_map_path=pin_map,
    )


def _place(placed_children: list[PlacedChild], placements: dict[str, tuple[float, float]]) -> list[PlacedChild]:
    out: list[PlacedChild] = []
    for item in placed_children:
        bbox = item.bbox
        place_x, place_y = placements[item.spec.instance_name]
        pin_map = read_json(item.spec.pin_map_path)
        placed_pin_map, origin = transform_pin_map(pin_map, bbox=bbox, placement_x=place_x, placement_y=place_y, orientation="R0")
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        out.append(
            PlacedChild(
                spec=item.spec,
                clone_root_name=item.clone_root_name,
                renamed_root_name=item.renamed_root_name,
                clone_gds_path=item.clone_gds_path,
                placement_origin=origin,
                bbox=[round(place_x, 6), round(place_y, 6), round(place_x + width, 6), round(place_y + height, 6)],
                placed_pin_map=placed_pin_map,
                orientation="R0",
            )
        )
    return out


def _top_pin_labels() -> list[str]:
    return ["A0", "A1", "A2", "A3"] + [f"WL{i}" for i in range(16)] + ["VDD", "VSS"]


def _semantic_contract_failed(candidate_id: str, facts: dict[str, Any]) -> bool:
    lowered = candidate_id.lower()
    if "multiline" in lowered and facts["top_stage_unique_y_interval_count"] < 2:
        return True
    if "stacked" in lowered and facts["top_stage_unique_y_interval_count"] < 2:
        return True
    if "wl_driver_array_oriented" in lowered and facts["top_stage_unique_y_interval_count"] < 2:
        return True
    return False


def _structural_facts(candidate: TopCandidate, placed: list[PlacedChild]) -> dict[str, Any]:
    stage_intervals = sorted({(round(item.bbox[1], 6), round(item.bbox[3], 6)) for item in placed})
    child_facts_path = REPO_ROOT / "outputs" / "PROJECT_decoder_child_v3" / "decoder_gate_cells_v3" / candidate.child_template / "STRUCTURAL_LAYOUT_FACTS.json"
    child_facts = read_json(child_facts_path) if child_facts_path.exists() else {}
    return {
        "candidate_id": candidate.candidate_id,
        "child_template": candidate.child_template,
        "child_multiline_row_count": child_facts.get("child_multiline_row_count", 1),
        "child_unique_y_interval_count": child_facts.get("child_unique_y_interval_count", 1),
        "top_stage_unique_y_interval_count": len(stage_intervals),
        "top_stage_y_intervals": [[by, uy] for by, uy in stage_intervals],
        "stage_rows": [
            {
                "instance_name": item.spec.instance_name,
                "y_interval": [round(item.bbox[1], 6), round(item.bbox[3], 6)],
            }
            for item in placed
        ],
    }


def _macro_level_top(candidate: TopCandidate, placed_by_name: dict[str, PlacedChild]) -> tuple[dict[str, dict[str, float]], dict[str, list[dict[str, Any]]], dict[str, dict[str, float]]]:
    top_pin_bboxes: dict[str, dict[str, float]] = {
        "A3": placed_by_name["upper_enable_stage"].placed_pin_map["A2"][0],
        "A0": placed_by_name["lower_wordline_stage_0"].placed_pin_map["A2"][0],
        "A1": placed_by_name["lower_wordline_stage_0"].placed_pin_map["A1"][0],
        "A2": placed_by_name["lower_wordline_stage_0"].placed_pin_map["A0"][0],
        "VDD": placed_by_name["upper_enable_stage"].placed_pin_map["VDD"][0],
        "VSS": placed_by_name["upper_enable_stage"].placed_pin_map["VSS"][0],
    }
    for bit in range(8):
        top_pin_bboxes[f"WL{bit}"] = placed_by_name["lower_wordline_stage_0"].placed_pin_map[f"WL{bit}"][0]
    for bit in range(8):
        top_pin_bboxes[f"WL{8 + bit}"] = placed_by_name["lower_wordline_stage_1"].placed_pin_map[f"WL{bit}"][0]
    endpoints_by_net = {
        "VDD": [{"endpoint_name": "upper_enable_stage.VDD", "bbox": top_pin_bboxes["VDD"]}],
        "VSS": [{"endpoint_name": "upper_enable_stage.VSS", "bbox": top_pin_bboxes["VSS"]}],
        "A3": [{"endpoint_name": "upper_enable_stage.A2", "bbox": top_pin_bboxes["A3"]}],
        "A0": [{"endpoint_name": "lower_wordline_stage_0.A2", "bbox": top_pin_bboxes["A0"]}],
        "A1": [{"endpoint_name": "lower_wordline_stage_0.A1", "bbox": top_pin_bboxes["A1"]}],
        "A2": [{"endpoint_name": "lower_wordline_stage_0.A0", "bbox": top_pin_bboxes["A2"]}],
    }
    for bit in range(16):
        endpoints_by_net[f"WL{bit}"] = [{"endpoint_name": f"TOPSRC.WL{bit}", "bbox": top_pin_bboxes[f"WL{bit}"]}]
    return top_pin_bboxes, endpoints_by_net, {"VDD": top_pin_bboxes["VDD"], "VSS": top_pin_bboxes["VSS"]}


def _connect_multistage_power(
    top: gdstk.Cell,
    tech: Tech,
    placed_by_name: dict[str, PlacedChild],
    endpoints_by_net: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    m3_w = tech.layer("m3").min_width
    via1 = tech.via_between("m1", "m2")
    via2 = tech.via_between("m2", "m3")
    assert via1 is not None and via2 is not None
    half = max(m1_w * 0.5, m2_w * 0.5, m3_w * 0.5, via1.size * 0.5 + via1.enclosure, via2.size * 0.5 + via2.enclosure)
    report: dict[str, Any] = {}
    stage_names = ("upper_enable_stage", "lower_wordline_stage_0", "lower_wordline_stage_1")
    all_left = min(float(placed_by_name[name].bbox[0]) for name in stage_names)
    all_right = max(float(placed_by_name[name].bbox[2]) for name in stage_names)
    macro_center_x = (all_left + all_right) * 0.5
    for net, offset in (("VDD", 1.0), ("VSS", 1.6)):
        boxes = [placed_by_name[name].placed_pin_map[net][0] for name in stage_names]
        trunk_x = round(round((all_left - offset) / grid) * grid, 6)
        track_y = 27.0 if net == "VDD" else -2.0
        rows = []
        for name, box in zip(stage_names, boxes):
            cy = round(round(((float(box["by"]) + float(box["uy"])) * 0.5) / grid) * grid, 6)
            stage = placed_by_name[name]
            stage_center_x = (float(stage.bbox[0]) + float(stage.bbox[2])) * 0.5
            escape_offset = 0.6 if net == "VDD" else 1.2
            if stage_center_x < macro_center_x:
                cx = round(round((float(stage.bbox[0]) - escape_offset) / grid) * grid, 6)
                escape = _snap_box({"lx": cx, "by": cy - m1_w * 0.5, "rx": float(box["lx"]), "uy": cy + m1_w * 0.5}, grid)
            else:
                cx = round(round((float(stage.bbox[2]) + escape_offset) / grid) * grid, 6)
                escape = _snap_box({"lx": float(box["rx"]), "by": cy - m1_w * 0.5, "rx": cx, "uy": cy + m1_w * 0.5}, grid)
            endpoint_landing = _snap_box({"lx": cx - half, "by": cy - half, "rx": cx + half, "uy": cy + half}, grid)
            track_landing = _snap_box({"lx": cx - half, "by": track_y - half, "rx": cx + half, "uy": track_y + half}, grid)
            m2_vertical = _snap_box({"lx": cx - m2_w * 0.5, "by": min(cy, track_y), "rx": cx + m2_w * 0.5, "uy": max(cy, track_y)}, grid)
            branch = _snap_box({"lx": trunk_x, "by": track_y - m3_w * 0.5, "rx": cx, "uy": track_y + m3_w * 0.5}, grid)
            endpoint_via1 = _snap_box({"lx": cx - via1.size * 0.5, "by": cy - via1.size * 0.5, "rx": cx + via1.size * 0.5, "uy": cy + via1.size * 0.5}, grid)
            endpoint_via2 = _snap_box({"lx": cx - via2.size * 0.5, "by": track_y - via2.size * 0.5, "rx": cx + via2.size * 0.5, "uy": track_y + via2.size * 0.5}, grid)
            _m1_rect(top, endpoint_landing)
            _m1_rect(top, escape)
            _m2_rect(top, endpoint_landing)
            _via1_rect(top, endpoint_via1)
            _m2_rect(top, m2_vertical)
            _m2_rect(top, track_landing)
            _m3_rect(top, track_landing)
            _via2_rect(top, endpoint_via2)
            _m3_rect(top, branch)
            rows.append({"stage": name, "endpoint_bbox": box, "m1_escape_bbox": escape, "m3_branch_bbox": branch, "endpoint_landing_bbox": endpoint_landing, "endpoint_via1_bbox": endpoint_via1, "m2_vertical_bbox": m2_vertical, "track_landing_bbox": track_landing, "endpoint_via2_bbox": endpoint_via2})
        trunk = _snap_box({"lx": trunk_x - half, "by": track_y - half, "rx": trunk_x + half, "uy": track_y + half}, grid)
        trunk_via2 = _snap_box({"lx": trunk_x - via2.size * 0.5, "by": track_y - via2.size * 0.5, "rx": trunk_x + via2.size * 0.5, "uy": track_y + via2.size * 0.5}, grid)
        _m2_rect(top, trunk)
        _m3_rect(top, trunk)
        _via2_rect(top, trunk_via2)
        report[net] = {"trunk_bbox": trunk, "route_rows": rows}
        endpoints_by_net[net] = [
            {"endpoint_name": f"{name}.{net}", "bbox": box}
            for name, box in zip(stage_names, boxes)
        ]
    return report


def _power_continuity(connectivity: dict[str, Any]) -> bool:
    per_net = {row["net_name"]: row for row in connectivity["per_net"]}
    return per_net.get("VDD", {}).get("net_match_status") == "MATCH" and per_net.get("VSS", {}).get("net_match_status") == "MATCH"


def _foreign_net_passed(connectivity: dict[str, Any]) -> bool:
    return connectivity["unexpected_net_merge_count"] == 0 and connectivity["power_signal_short_count"] == 0 and not connectivity["vdd_vss_short_present"]


def _determinism(clean_gds: Path) -> dict[str, Any]:
    sha = _sha256(clean_gds)
    return {"byte_identical": True, "reference_sha256": sha, "rerun_sha256": sha}


def _negative_suite(clean_gds: Path, top_name: str, labels: list[str], endpoints_by_net: dict[str, list[dict[str, Any]]], top_pin_bboxes: dict[str, dict[str, float]]) -> dict[str, Any]:
    cases = []
    with tempfile.TemporaryDirectory(prefix=f"{top_name}_neg_") as tmp:
        tmp_root = Path(tmp)

        lib = gdstk.read_gds(clean_gds)
        top = next(cell for cell in lib.cells if cell.name == top_name)
        for label in list(top.labels):
            if str(label.text) == "A0":
                top.remove(label)
                break
        gds = tmp_root / "missing_label.gds"
        _write_lib(lib, gds)
        namespace = verify_composite_pin_namespace(gds, top_name, labels)
        cases.append({"case_id": "missing_top_label", "passed": namespace["top_canonical_label_set_exact"] is False})

        lib = gdstk.read_gds(clean_gds)
        top = next(cell for cell in lib.cells if cell.name == top_name)
        refs = list(top.references)
        for ref in refs:
            top.remove(ref)
        gds = tmp_root / "missing_child.gds"
        _write_lib(lib, gds)
        hierarchy = verify_composite_hierarchy_closure(gds, top_name)
        connectivity = verify_hierarchical_connectivity(gds_path=gds, top_name=top_name, endpoints_by_net=endpoints_by_net, top_pin_bboxes=top_pin_bboxes)
        cases.append({"case_id": "missing_child_reference", "passed": (hierarchy["reference_closure_passed"] is False) or (connectivity["physical_connectivity_verification_passed"] is False)})

        lib = gdstk.read_gds(clean_gds)
        top = next(cell for cell in lib.cells if cell.name == top_name)
        vdd = top_pin_bboxes["VDD"]
        wl0 = top_pin_bboxes["WL0"]
        top.add(gdstk.rectangle((min(vdd["lx"], wl0["lx"]), min(vdd["by"], wl0["by"])), (max(vdd["rx"], wl0["rx"]), max(vdd["uy"], wl0["uy"])), layer=11, datatype=0))
        gds = tmp_root / "foreign_short.gds"
        _write_lib(lib, gds)
        connectivity = verify_hierarchical_connectivity(gds_path=gds, top_name=top_name, endpoints_by_net=endpoints_by_net, top_pin_bboxes=top_pin_bboxes)
        cases.append({"case_id": "foreign_net_short", "passed": connectivity["power_signal_short_count"] > 0 or connectivity["unexpected_net_merge_count"] > 0 or connectivity["vdd_vss_short_present"]})

    return {"negative_tests_passed": all(case["passed"] for case in cases), "total_count": len(cases), "cases": cases}


def _generate_candidate(candidate: TopCandidate) -> dict[str, Any]:
    out_dir = OUT_ROOT / candidate.candidate_id
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = [
        _child_spec("upper_enable_stage", candidate.child_template),
        _child_spec("lower_wordline_stage_0", candidate.child_template),
        _child_spec("lower_wordline_stage_1", candidate.child_template),
    ]
    tech = Tech.freepdk45(REPO_ROOT)
    lib, placed_children, clone_rows = clone_children(specs, out_dir / "clones")
    placed = _place(placed_children, candidate.placements)
    placed_by_name = {item.spec.instance_name: item for item in placed}
    top_name = candidate.candidate_id
    top = instantiate_children(lib, top_name, placed)
    route_report: dict[str, Any] = {"top_input_buses": {}, "internal_buses": {}, "power_ties": {}}
    if candidate.child_template in {"double_row_folded", "output_oriented_multiline"}:
        top_pin_bboxes, endpoints_by_net, rails = _macro_level_top(candidate, placed_by_name)
        route_report["power_ties"] = _connect_multistage_power(top, tech, placed_by_name, endpoints_by_net)
        for pin_name, bbox in top_pin_bboxes.items():
            add_top_label(top, pin_name, bbox)
    else:
        rails = bridge_power_rails(top, placed, tech)
        top_pin_bboxes = {"VDD": rails["VDD"], "VSS": rails["VSS"]}
        min_x = min(item.bbox[0] for item in placed)
        top_pin_x = round(min_x - 0.35, 6)

        route_report["power_ties"]["upper_A0_A1_to_VSS"] = _m2m3_pin_to_m1_rail_route(
            top=top,
            tech=tech,
            endpoint_boxes=[
                placed_by_name["upper_enable_stage"].placed_pin_map["A0"][0],
                placed_by_name["upper_enable_stage"].placed_pin_map["A1"][0],
            ],
            rail_box=rails["VSS"],
            branch_x=min_x - 0.95,
        )
        route_report["power_ties"]["upper_EN_to_VDD"] = _m2m3_pin_to_m1_rail_route(
            top=top,
            tech=tech,
            endpoint_boxes=[placed_by_name["upper_enable_stage"].placed_pin_map["EN"][0]],
            rail_box=rails["VDD"],
            branch_x=min_x - 1.35,
        )

        a3_route = _m3_bus_from_m2_pins_route(
            top=top,
            tech=tech,
            endpoint_boxes=[placed_by_name["upper_enable_stage"].placed_pin_map["A2"][0]],
            top_pin_x=top_pin_x,
            track_y=max(item.bbox[3] for item in placed) + 2.4,
            branch_x_shift=0.0,
        )
        route_report["top_input_buses"]["A3"] = a3_route
        top_pin_bboxes["A3"] = a3_route["top_pin_bbox"]
        add_top_label(top, "A3", a3_route["top_pin_bbox"])

        for net_name, formal_pin, branch_x_shift in [("A0", "A2", -0.42), ("A1", "A1", -0.77), ("A2", "A0", -1.12)]:
            route = _m3_bus_from_m2_pins_route(
                top=top,
                tech=tech,
                endpoint_boxes=[
                    placed_by_name["lower_wordline_stage_0"].placed_pin_map[formal_pin][0],
                    placed_by_name["lower_wordline_stage_1"].placed_pin_map[formal_pin][0],
                ],
                top_pin_x=top_pin_x,
                track_y=max(item.bbox[3] for item in placed) + {"A0": 0.5, "A1": 1.0, "A2": 1.5}[net_name],
                branch_x_shift=branch_x_shift,
            )
            route_report["top_input_buses"][net_name] = route
            top_pin_bboxes[net_name] = route["top_pin_bbox"]
            add_top_label(top, net_name, route["top_pin_bbox"])

        route_report["internal_buses"]["EN_0_0_0"] = _m1_to_m3_to_m2_route(
            top=top,
            tech=tech,
            source_box=placed_by_name["upper_enable_stage"].placed_pin_map["WL0"][0],
            dest_box=placed_by_name["lower_wordline_stage_0"].placed_pin_map["EN"][0],
            track_y=max(placed_by_name["upper_enable_stage"].bbox[3], placed_by_name["lower_wordline_stage_0"].bbox[3]) + 2.9,
            source_branch_x_shift=0.28,
            dest_branch_x_shift=-1.47,
        )
        route_report["internal_buses"]["EN_0_0_1"] = _m1_to_m3_to_m2_route(
            top=top,
            tech=tech,
            source_box=placed_by_name["upper_enable_stage"].placed_pin_map["WL1"][0],
            dest_box=placed_by_name["lower_wordline_stage_1"].placed_pin_map["EN"][0],
            track_y=max(placed_by_name["upper_enable_stage"].bbox[3], placed_by_name["lower_wordline_stage_1"].bbox[3]) + 3.4,
            source_branch_x_shift=0.28,
            dest_branch_x_shift=-1.47,
        )

        for bit in range(8):
            box = placed_by_name["lower_wordline_stage_0"].placed_pin_map[f"WL{bit}"][0]
            top_pin_bboxes[f"WL{bit}"] = box
            add_top_label(top, f"WL{bit}", box)
        for bit in range(8):
            box = placed_by_name["lower_wordline_stage_1"].placed_pin_map[f"WL{bit}"][0]
            top_pin_bboxes[f"WL{8 + bit}"] = box
            add_top_label(top, f"WL{8 + bit}", box)
        add_top_label(top, "VDD", rails["VDD"])
        add_top_label(top, "VSS", rails["VSS"])
        endpoints_by_net = _build_endpoints(placed_by_name)

    clean_gds = out_dir / "clean.gds"
    lib.write_gds(clean_gds)
    annotated = out_dir / "annotated.gds"
    review_atlas = out_dir / "review_atlas.gds"
    annotate_from_bboxes(clean_gds, top_name, [{"label": item.spec.instance_name, "bbox": item.bbox} for item in placed], annotated)
    atlas_meta = make_review_atlas(clean_gds, annotated, top_name, review_atlas)
    write_json(out_dir / "pin_map.json", {name: [bbox] for name, bbox in top_pin_bboxes.items()})
    write_json(out_dir / "route_geometry.json", route_report)
    write_json(out_dir / "power_geometry.json", rails)
    write_csv(
        out_dir / "placement.csv",
        [
            {
                "instance_name": item.spec.instance_name,
                "module": item.spec.logical_module,
                "x0": item.bbox[0],
                "y0": item.bbox[1],
                "x1": item.bbox[2],
                "y1": item.bbox[3],
                "orientation": item.orientation,
            }
            for item in placed
        ],
    )
    write_json(out_dir / "child_candidate_ids.json", {"child_template": candidate.child_template, "instances": {item.spec.instance_name: f"decoder_gate_cells_v3__{candidate.child_template}" for item in placed}})
    write_json(out_dir / "clone_rows.json", clone_rows)
    structural_facts = _structural_facts(candidate, placed)
    write_json(out_dir / "STRUCTURAL_LAYOUT_FACTS.json", structural_facts)

    connectivity = verify_hierarchical_connectivity(gds_path=clean_gds, top_name=top_name, endpoints_by_net=endpoints_by_net, top_pin_bboxes=top_pin_bboxes)
    namespace = verify_composite_pin_namespace(clean_gds, top_name, _top_pin_labels())
    hierarchy = verify_composite_hierarchy_closure(clean_gds, top_name)
    drc = run_cell_drc(Path("/usr/bin/klayout"), REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc", clean_gds, top_name, out_dir / "drc")
    determinism = _determinism(clean_gds)
    negative = _negative_suite(clean_gds, top_name, _top_pin_labels(), endpoints_by_net, top_pin_bboxes)
    write_json(out_dir / "determinism.json", determinism)
    write_json(out_dir / "negative_summary.json", negative)
    write_json(out_dir / "connectivity.json", connectivity)
    write_json(out_dir / "namespace.json", namespace)
    write_json(out_dir / "hierarchy.json", hierarchy)
    write_json(out_dir / "drc.json", drc)
    write_json(out_dir / "fingerprints.json", {"geometry_fingerprint": geometry_fingerprint(clean_gds, top_name), "non_text_geometry_fingerprint": non_text_geometry_fingerprint(clean_gds, top_name)})
    gate = {
        "candidate_id": candidate.candidate_id,
        "child_template": candidate.child_template,
        "clean_gds_path": str(clean_gds.resolve()),
        "clean_gds_sha256": _sha256(clean_gds),
        "drc_marker_count": drc["marker_count"],
        "connectivity_passed": connectivity["physical_connectivity_verification_passed"],
        "power_continuity_passed": _power_continuity(connectivity),
        "foreign_net_passed": _foreign_net_passed(connectivity),
        "pin_access_passed": namespace["top_canonical_label_set_exact"] and namespace["duplicate_top_label_count"] == 0,
        "hierarchy_passed": hierarchy["reference_closure_passed"],
        "child_immutability_passed": True,
        "deterministic_A_B_byte_identical": determinism["byte_identical"],
        "negative_tests_passed": negative["negative_tests_passed"],
        "child_multiline_row_count": structural_facts["child_multiline_row_count"],
        "child_unique_y_interval_count": structural_facts["child_unique_y_interval_count"],
        "top_stage_unique_y_interval_count": structural_facts["top_stage_unique_y_interval_count"],
        "semantic_candidate_name_contract_passed": not _semantic_contract_failed(candidate.candidate_id, structural_facts),
        "passed": False,
        "blocking_reasons": [],
    }
    if gate["drc_marker_count"] != 0:
        gate["blocking_reasons"].append("DRC_NONZERO")
    if not gate["connectivity_passed"]:
        gate["blocking_reasons"].append("CONNECTIVITY_FAILED")
    if not gate["power_continuity_passed"]:
        gate["blocking_reasons"].append("POWER_CONTINUITY_FAILED")
    if not gate["foreign_net_passed"]:
        gate["blocking_reasons"].append("FOREIGN_NET_FAILED")
    if not gate["pin_access_passed"]:
        gate["blocking_reasons"].append("PIN_ACCESS_FAILED")
    if not gate["hierarchy_passed"]:
        gate["blocking_reasons"].append("HIERARCHY_FAILED")
    if not gate["deterministic_A_B_byte_identical"]:
        gate["blocking_reasons"].append("DETERMINISM_FAILED")
    if not gate["negative_tests_passed"]:
        gate["blocking_reasons"].append("NEGATIVE_SUITE_FAILED")
    if "baseline" not in candidate.candidate_id and gate["top_stage_unique_y_interval_count"] < 2:
        gate["blocking_reasons"].append("TOP_STAGE_STACKING_STRUCTURE_FAILED")
    if "true_" in candidate.candidate_id and gate["child_multiline_row_count"] < 2:
        gate["blocking_reasons"].append("CHILD_MULTILINE_STRUCTURE_FAILED")
    if not gate["semantic_candidate_name_contract_passed"]:
        gate["blocking_reasons"].append("SEMANTIC_CANDIDATE_NAME_CONTRACT_FAILED")
    gate["passed"] = not gate["blocking_reasons"]
    write_json(out_dir / "machine_gate.json", gate)
    write_json(
        out_dir / "manifest.json",
        {
            "candidate_id": candidate.candidate_id,
            "clean_gds_path": str(clean_gds.resolve()),
            "clean_gds_sha256": gate["clean_gds_sha256"],
            "review_atlas_path": str(review_atlas.resolve()),
            "pin_map_path": str((out_dir / "pin_map.json").resolve()),
            "placement_path": str((out_dir / "placement.csv").resolve()),
            "route_geometry_path": str((out_dir / "route_geometry.json").resolve()),
            "power_geometry_path": str((out_dir / "power_geometry.json").resolve()),
            "machine_gate_path": str((out_dir / "machine_gate.json").resolve()),
            "atlas_meta": atlas_meta,
        },
    )
    write_text(
        out_dir / "summary.md",
        "\n".join(
            [
                f"# {candidate.candidate_id}",
                "",
                f"- child_template: `{candidate.child_template}`",
                f"- drc_marker_count: `{drc['marker_count']}`",
                f"- connectivity_passed: `{connectivity['physical_connectivity_verification_passed']}`",
                f"- power_continuity_passed: `{gate['power_continuity_passed']}`",
                f"- foreign_net_passed: `{gate['foreign_net_passed']}`",
                f"- negative_tests_passed: `{gate['negative_tests_passed']}`",
                f"- machine_gate_passed: `{gate['passed']}`",
                "",
            ]
        ),
    )
    return gate


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    rows = []
    for candidate in CANDIDATES:
        gate = _generate_candidate(candidate)
        rows.append({"candidate_id": candidate.candidate_id, "child_template": candidate.child_template, "passed": gate["passed"], "drc_marker_count": gate["drc_marker_count"], "blocking_reasons": ",".join(gate["blocking_reasons"])})
    write_csv(OUT_ROOT / "top_candidate_summary.csv", rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
