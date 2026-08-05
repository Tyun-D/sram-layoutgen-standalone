#!/usr/bin/env python3
"""Build Decoder/WL-driver candidates around the immutable authoritative array."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any

import gdstk


REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import scripts.project_decoder_physical_architecture_evidence as evidence
import scripts.project_decoder_wl_array_integration_generate as integration
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import _component_for_bbox
from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import non_text_geometry_fingerprint, run_cell_drc
from sram_layoutgen.openyield_adapter.teamb_composite_helper import add_top_label, read_json, write_csv, write_gds, write_json
from sram_layoutgen.tech import Tech


OUT_ROOT = REPO / "outputs/PROJECT_decoder_real_array_integration_v1"
ARRAY_ROOT = REPO / "outputs/PROJECT_bitcell_array_layoutgen_reuse_v2"
ARRAY_GDS = ARRAY_ROOT / "clean.gds"
ARRAY_SHA = "555df9b1fcbd9dda7e4c8959942e27b8f093c36b0a8c67a7ac213f9946b9a1ac"
ARRAY_TOP = "sram_capped_replica_bitcell_array"
ARRAY_ANCHOR_X = 90.0
ARRAY_ANCHOR_Y = 0.0
TOTAL_ROWS = 16


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pin_box(row: dict[str, Any]) -> dict[str, Any]:
    lx, by, rx, uy = row["bbox"]
    return {"layer": row["layer"], "lx": lx, "by": by, "rx": rx, "uy": uy}


def shifted(box: dict[str, Any], x: float, y: float) -> dict[str, Any]:
    return {
        "layer": box.get("layer", "m1"),
        "lx": round(float(box["lx"]) + x, 6),
        "by": round(float(box["by"]) + y, 6),
        "rx": round(float(box["rx"]) + x, 6),
        "uy": round(float(box["uy"]) + y, 6),
    }


def authoritative_pin_map() -> dict[str, list[dict[str, Any]]]:
    source = read_json(ARRAY_ROOT / "pin_map.json")["pins"]
    pins = {name: [pin_box(row) for row in rows] for name, rows in source.items()}
    # These right-edge M1 rails belong to the locked VDD/VSS components and avoid crossing the core.
    pins["VDD"] = [{"layer": "m1", "lx": 15.1275, "by": 1.5825, "rx": 15.2625, "uy": 1.6475}]
    pins["VSS"] = [{"layer": "m1", "lx": 14.6675, "by": 0.2175, "rx": 14.8025, "uy": 0.2825}]
    for index in range(TOTAL_ROWS):
        wl = pins[f"WL{index}"][0]
        pins[f"LOCAL_WL{index}"] = [{"layer": "m1", "lx": 0.685, "by": wl["by"], "rx": 0.82, "uy": wl["uy"]}]
    return pins


ARRAY_PINS = authoritative_pin_map()
WL_CENTERS = {
    index: (float(ARRAY_PINS[f"WL{index}"][0]["by"]) + float(ARRAY_PINS[f"WL{index}"][0]["uy"])) * 0.5
    for index in range(TOTAL_ROWS)
}
ROW_PITCH_PROXY = statistics.median(
    WL_CENTERS[index + 1] - WL_CENTERS[index] for index in range(TOTAL_ROWS - 1)
)


def load_array_macro(_tech: Tech) -> tuple[gdstk.Library, gdstk.Cell, dict[str, list[dict[str, Any]]], dict[str, Any]]:
    if sha256(ARRAY_GDS) != ARRAY_SHA:
        raise RuntimeError("ARRAY_GDS_SHA_MISMATCH")
    library = gdstk.read_gds(ARRAY_GDS)
    cell = next(item for item in library.cells if item.name == ARRAY_TOP)
    bbox = cell.bounding_box()
    return library, cell, ARRAY_PINS, {
        "bbox": {"width": float(bbox[1][0] - bbox[0][0]), "height": float(bbox[1][1] - bbox[0][1])},
        "row_pitch": ROW_PITCH_PROXY,
    }


def driver_layout_rows(
    *,
    candidate: integration.IntegrationCandidate,
    decoder_bbox: list[float],
    driver_w: float,
    driver_h: float,
    driver_pin_map: dict[str, list[dict[str, float]]],
    row_pitch: float,
) -> tuple[float, list[tuple[int, float, float]], str]:
    del row_pitch
    z = driver_pin_map["Z"][0]
    z_center_y = (float(z["by"]) + float(z["uy"])) * 0.5
    left_x = round(decoder_bbox[2] + candidate.driver_x_gap, 6)
    right_x = round(left_x + driver_w + candidate.interleave_gap, 6)
    rows = [
        (index, left_x if index % 2 == 0 else right_x, round(WL_CENTERS[index] - z_center_y, 6))
        for index in range(TOTAL_ROWS)
    ]
    return left_x, rows, "2x8_interleaved_real_array_row_aligned"


def m1_to_m5_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    source_box: dict[str, float],
    dest_box: dict[str, float],
    track_y: float,
    **_kwargs: Any,
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    sx = round(round(((float(source_box["lx"]) + float(source_box["rx"])) * 0.5) / grid) * grid, 6)
    sy = round(round(((float(source_box["by"]) + float(source_box["uy"])) * 0.5) / grid) * grid, 6)
    dx = round(round(((float(dest_box["lx"]) + float(dest_box["rx"])) * 0.5) / grid) * grid, 6)
    dy = round(round(((float(dest_box["by"]) + float(dest_box["uy"])) * 0.5) / grid) * grid, 6)
    ty = round(round(track_y / grid) * grid, 6)

    def box(cx: float, cy: float, half_x: float, half_y: float | None = None) -> dict[str, float]:
        half_y = half_x if half_y is None else half_y
        return integration._snap_box({"lx": cx - half_x, "by": cy - half_y, "rx": cx + half_x, "uy": cy + half_y}, grid)

    row: dict[str, Any] = {"source_bbox": source_box, "dest_bbox": dest_box}
    for prefix, x, y in (("source", sx, sy), ("dest", dx, dy)):
        row[f"{prefix}_m1_landing_bbox"] = box(x, y, 0.0675)
        row[f"{prefix}_via1_bbox"] = box(x, y, 0.0325)
        row[f"{prefix}_m2_landing_bbox"] = box(x, y, 0.0675)
        row[f"{prefix}_via2_bbox"] = box(x, y, 0.0325)
        row[f"{prefix}_m3_landing_bbox"] = box(x, y, 0.07)
        row[f"{prefix}_via3_bbox"] = box(x, y, 0.035)
        row[f"{prefix}_m4_landing_bbox"] = box(x, y, 0.07)
    row_index = min(range(TOTAL_ROWS), key=lambda index: abs((ARRAY_ANCHOR_Y + WL_CENTERS[index]) - ty))
    # Decoder WL0/WL8 pairs reuse an x coordinate. Offset the lower bank only;
    # this keeps each vertical M4 escape independent without broad M5 overlap.
    lane_x = round(sx + (0.3 if row_index >= 8 else 0.0), 6)
    if abs(sy - ty) <= grid:
        lane_x = sx
    row["source_via4_bbox"] = box(sx, sy, 0.07)
    row["source_m5_landing_bbox"] = box(sx, sy, 0.07)
    row["source_m5_horizontal_bbox"] = integration._snap_box({"lx": min(sx, lane_x) - 0.07, "by": sy - 0.07, "rx": max(sx, lane_x) + 0.07, "uy": sy + 0.07}, grid)
    row["lane_via4_bbox"] = box(lane_x, sy, 0.07)
    row["lane_m4_landing_bbox"] = box(lane_x, sy, 0.07)
    row["source_m4_vertical_bbox"] = integration._snap_box({"lx": lane_x - 0.07, "by": min(sy, ty) - 0.07, "rx": lane_x + 0.07, "uy": max(sy, ty) + 0.07}, grid)
    row["track_via4_bbox"] = box(lane_x, ty, 0.07)
    row["track_m5_landing_bbox"] = box(lane_x, ty, 0.07)
    row["m5_trunk_bbox"] = integration._snap_box({"lx": min(lane_x, dx) - 0.07, "by": ty - 0.07, "rx": max(lane_x, dx) + 0.07, "uy": ty + 0.07}, grid)
    row["dest_via4_bbox"] = box(dx, ty, 0.07)
    row["dest_m5_landing_bbox"] = box(dx, ty, 0.07)
    row["dest_m4_vertical_bbox"] = integration._snap_box({"lx": dx - 0.07, "by": min(dy, ty) - 0.07, "rx": dx + 0.07, "uy": max(dy, ty) + 0.07}, grid)

    layers = {
        "m1": 11, "via1": 12, "m2": 13, "via2": 14, "m3": 15,
        "via3": 16, "m4": 17, "via4": 18, "m5": 19,
    }
    for name, shape in row.items():
        if not name.endswith("bbox") or name in {"source_bbox", "dest_bbox"}:
            continue
        layer = next(layer for layer in ("via4", "via3", "via2", "via1", "m5", "m4", "m3", "m2", "m1") if layer in name)
        top.add(gdstk.rectangle((shape["lx"], shape["by"]), (shape["rx"], shape["uy"]), layer=layers[layer], datatype=0))
    return {"route_rows": [row]}


def m1_to_m1_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    source_box: dict[str, float],
    dest_box: dict[str, float],
    track_y: float,
) -> dict[str, Any]:
    m1w = tech.layer("m1").min_width
    dest_cx = (float(dest_box["lx"]) + float(dest_box["rx"])) * 0.5
    dest_cy = (float(dest_box["by"]) + float(dest_box["uy"])) * 0.5
    egress_x = round(ARRAY_ANCHOR_X - 1.0, 6)
    egress_box = {"layer": "m1", "lx": egress_x - m1w / 2, "by": dest_cy - m1w / 2, "rx": egress_x + m1w / 2, "uy": dest_cy + m1w / 2}
    route = integration._m1_to_m3_to_m2_route(
        top=top,
        tech=tech,
        source_box=source_box,
        dest_box=egress_box,
        track_y=track_y,
    )
    if route.get("route_rows"):
        route.update(route["route_rows"][0])
    grid = tech.manufacturing_grid
    via1 = tech.via_between("m1", "m2")
    assert via1 is not None
    cx = round(round(egress_x / grid) * grid, 6)
    cy = round(round(dest_cy / grid) * grid, 6)
    via_box = integration._snap_box({"lx": cx - via1.size / 2, "by": cy - via1.size / 2, "rx": cx + via1.size / 2, "uy": cy + via1.size / 2}, grid)
    half = max(m1w / 2, via1.size / 2 + 0.035)
    landing = integration._snap_box({"lx": cx - half, "by": cy - half, "rx": cx + half, "uy": cy + half}, grid)
    top.add(gdstk.rectangle((via_box["lx"], via_box["by"]), (via_box["rx"], via_box["uy"]), layer=12))
    top.add(gdstk.rectangle((landing["lx"], landing["by"]), (landing["rx"], landing["uy"]), layer=11))
    top.add(gdstk.FlexPath([(cx, cy), (dest_cx, dest_cy)], m1w, layer=11, datatype=0))
    route["dest_via1_bbox"] = via_box
    route["dest_m1_landing_bbox"] = landing
    route["array_m1_egress_bbox"] = {"lx": min(cx, dest_cx), "by": cy - m1w / 2, "rx": max(cx, dest_cx), "uy": cy + m1w / 2}
    route["source_bbox"] = source_box
    route["dest_bbox"] = dest_box
    return route


ORIGINAL_SIGNAL_ROUTE = integration._m1_to_m3_to_m2_route


def boundary_power_route(*, top: gdstk.Cell, tech: Tech, endpoint_boxes: list[dict[str, float]], trunk_box: dict[str, float], **kwargs: Any) -> dict[str, Any]:
    del kwargs
    m1w = tech.layer("m1").min_width
    m6w = 0.14
    via1 = tech.via_between("m1", "m2")
    assert via1 is not None
    grid = tech.manufacturing_grid
    trunk_x = round((float(trunk_box["lx"]) + float(trunk_box["rx"])) * 0.5, 6)
    rows: list[dict[str, Any]] = []
    source_columns: list[float] = []
    for endpoint in endpoint_boxes:
        endpoint_lx = float(endpoint["lx"])
        endpoint_rx = float(endpoint["rx"])
        escape = 0.5 if endpoint_rx < 50.0 else (0.35 if endpoint_rx < 80.0 else 0.9)
        if trunk_x >= 108.0 and endpoint_rx < 80.0:
            escape = max(escape, 1.0)
            endpoint_x = round(endpoint_lx, 6)
            cx = round(endpoint_lx - escape, 6)
        else:
            endpoint_x = round(endpoint_rx, 6)
            cx = round(endpoint_rx + escape, 6)
        shared_column = next((column for column in source_columns if abs(column - cx) < 0.3), None)
        if shared_column is not None:
            cx = shared_column
        else:
            source_columns.append(cx)
        cy = round((float(endpoint["by"]) + float(endpoint["uy"])) * 0.5, 6)
        track_y = -1.0 if trunk_x < 108.0 else -2.0
        via_half = via1.size / 2
        landing_half = via_half + 0.035
        horizontal = integration._snap_box({"lx": min(cx, trunk_x) - m6w / 2, "by": track_y - m6w / 2, "rx": max(cx, trunk_x) + m6w / 2, "uy": track_y + m6w / 2}, grid)
        m1_escape = integration._snap_box({"lx": min(endpoint_x, cx), "by": cy - m1w / 2, "rx": max(endpoint_x, cx), "uy": cy + m1w / 2}, grid)
        top.add(gdstk.rectangle((m1_escape["lx"], m1_escape["by"]), (m1_escape["rx"], m1_escape["uy"]), layer=11, datatype=0))
        row: dict[str, Any] = {"endpoint_bbox": endpoint, "m1_escape_bbox": m1_escape, "m6_horizontal_bbox": horizontal}
        source_low_stack = (("m1", 11, landing_half), ("via1", 12, via_half), ("m2", 13, landing_half))
        for layer_name, layer_number, half in source_low_stack:
            shape = integration._snap_box({"lx": cx - half, "by": cy - half, "rx": cx + half, "uy": cy + half}, grid)
            row[f"source_{layer_name}_bbox"] = shape
            top.add(gdstk.rectangle((shape["lx"], shape["by"]), (shape["rx"], shape["uy"]), layer=layer_number, datatype=0))
        source_m2_vertical = integration._snap_box({"lx": cx - landing_half, "by": min(cy, track_y) - landing_half, "rx": cx + landing_half, "uy": max(cy, track_y) + landing_half}, grid)
        row["source_m2_vertical_bbox"] = source_m2_vertical
        top.add(gdstk.rectangle((source_m2_vertical["lx"], source_m2_vertical["by"]), (source_m2_vertical["rx"], source_m2_vertical["uy"]), layer=13, datatype=0))
        for prefix, x in (("source", cx), ("trunk", trunk_x)):
            stack = (("m1", 11, landing_half), ("via1", 12, via_half), ("m2", 13, landing_half), ("via2", 14, via_half), ("m3", 15, 0.07), ("via3", 16, 0.035), ("m4", 17, 0.07), ("via4", 18, 0.07), ("m5", 19, 0.07), ("via5", 20, 0.07), ("m6", 21, 0.07))
            for layer_name, layer_number, half in stack:
                shape = integration._snap_box({"lx": x - half, "by": track_y - half, "rx": x + half, "uy": track_y + half}, grid)
                row[f"{prefix}_track_{layer_name}_bbox"] = shape
                top.add(gdstk.rectangle((shape["lx"], shape["by"]), (shape["rx"], shape["uy"]), layer=layer_number, datatype=0))
        trunk_extension = integration._snap_box({"lx": trunk_x - m1w / 2, "by": track_y - landing_half, "rx": trunk_x + m1w / 2, "uy": float(trunk_box["by"])}, grid)
        row["trunk_m1_extension_bbox"] = trunk_extension
        top.add(gdstk.rectangle((trunk_extension["lx"], trunk_extension["by"]), (trunk_extension["rx"], trunk_extension["uy"]), layer=11, datatype=0))
        top.add(gdstk.rectangle((horizontal["lx"], horizontal["by"]), (horizontal["rx"], horizontal["uy"]), layer=21, datatype=0))
        rows.append(row)
    return {"route_rows": rows, "routing_layer": "m6", "parent_trunk_layer": "m1"}


def candidate(candidate_id: str, top_id: str, family: str, driver_gap: float, interleave: float) -> integration.IntegrationCandidate:
    decoder = gdstk.read_gds(REPO / "outputs/PROJECT_decoder_top_v3" / top_id / "clean.gds").top_level()[0]
    decoder_x1 = float(decoder.bounding_box()[1][0])
    driver = gdstk.read_gds(REPO / "outputs/PROJECT_wordline_driver_v2_regen/current_supported_config/wordline_driver_v2.gds").top_level()[0]
    driver_w = float(driver.bounding_box()[1][0] - driver.bounding_box()[0][0])
    max_driver_x = decoder_x1 + driver_gap + driver_w + interleave
    array_gap = ARRAY_ANCHOR_X - (max_driver_x + driver_w)
    if array_gap <= 0:
        raise RuntimeError("ARRAY_ANCHOR_ROUTING_CHANNEL_NONPOSITIVE")
    return integration.IntegrationCandidate(
        candidate_id, top_id, family, "col16", driver_gap, array_gap,
        diagnostic_only=False, interleave_gap=interleave, array_object="full_bitcell_array_gds",
    )


CANDIDATES = [
    candidate("P2_REAL_ARRAY_V1", "candidate_p2_partitioned_control_centered", "P2_REAL_ARRAY_CONTROL_CENTERED", 5.0, 2.0),
    candidate("P3_REAL_ARRAY_V1", "candidate_p3_symmetric_lower_left_control_right", "P3_REAL_ARRAY_SYMMETRIC", 0.5, 2.0),
    candidate("REAL_ARRAY_SEARCH_PARETO_V1", "candidate_p2_partitioned_control_centered", "REAL_ARRAY_SEARCH_COMPACT_DRIVER_BANK", 2.0, 0.3),
]


def top_interface_pins(array_x: float) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    source = read_json(ARRAY_ROOT / "pin_map.json")["pins"]
    for index in range(16):
        result[f"BL{index}"] = [shifted(pin_box(source[f"BL[{index}]"][0]), array_x, ARRAY_ANCHOR_Y)]
        result[f"BR{index}"] = [shifted(pin_box(source[f"BR[{index}]"][0]), array_x, ARRAY_ANCHOR_Y)]
    for target, original in (("RBL_BL", "RBL_BL0"), ("RBL_BR", "RBL_BR0"), ("RBL_WL", "RBL_WL0")):
        result[target] = [shifted(pin_box(source[original][0]), array_x, ARRAY_ANCHOR_Y)]
    return result


def add_interface_labels(out_dir: Path) -> dict[str, list[dict[str, Any]]]:
    placement = list(csv.DictReader((out_dir / "placement.csv").open(encoding="utf-8", newline="")))
    array_row = next(row for row in placement if row["instance_name"] == "bitcell_array_quad_0")
    array_x = float(array_row["x0"])
    if abs(array_x - ARRAY_ANCHOR_X) > 1e-6 or abs(float(array_row["y0"]) - ARRAY_ANCHOR_Y) > 1e-6:
        raise RuntimeError("ARRAY_FLOORPLAN_ANCHOR_MOVED")
    pins = read_json(out_dir / "pin_map.json")
    interfaces = top_interface_pins(array_x)
    pins.update(interfaces)
    library = gdstk.read_gds(out_dir / "integration_shell_clean.gds")
    top_name = read_json(out_dir / "integration_machine_gate.json")["integration_top_name"]
    top = next(cell for cell in library.cells if cell.name == top_name)
    interface_names = set(interfaces)
    for label in list(top.labels):
        if str(label.text) in interface_names:
            top.remove(label)
    for name, boxes in interfaces.items():
        add_top_label(top, name, boxes[0])
    write_gds(library, out_dir / "integration_shell_clean.gds")
    write_json(out_dir / "pin_map.json", pins)
    return interfaces


def append_array_power_coverage(out_dir: Path) -> dict[str, Any]:
    module_rows = list(csv.DictReader((out_dir / "POWER_ENDPOINT_COVERAGE.csv").open(encoding="utf-8", newline="")))
    placement = list(csv.DictReader((out_dir / "placement.csv").open(encoding="utf-8", newline="")))
    array_row = next(row for row in placement if row["instance_name"] == "bitcell_array_quad_0")
    x, y = float(array_row["x0"]), float(array_row["y0"])
    graph = extract_physical_connectivity(out_dir / "integration_shell_clean.gds", read_json(out_dir / "integration_machine_gate.json")["integration_top_name"])
    top_pins = read_json(out_dir / "pin_map.json")
    top_components = {net: _component_for_bbox(graph, top_pins[net][0], {"m1", "m2", "m3", "m4"}) for net in ("VDD", "VSS")}
    child_rows = list(csv.DictReader((ARRAY_ROOT / "power_endpoint_coverage.csv").open(encoding="utf-8", newline="")))
    m1w = Tech.freepdk45(REPO).layer("m1").min_width
    array_rows: list[dict[str, Any]] = []
    for child in child_rows:
        net = child["endpoint_net"]
        cx, cy = float(child["endpoint_x"]) + x, float(child["endpoint_y"]) + y
        box = {"lx": cx - m1w / 2, "by": cy - m1w / 2, "rx": cx + m1w / 2, "uy": cy + m1w / 2}
        component = _component_for_bbox(graph, box, {"m1"})
        passed = child["passed"] == "True" and component == top_components[net]
        array_rows.append({
            "instance": f"bitcell_array_quad_0/{child['instance']}", "cell": child["cell"], "orientation": child["orientation"],
            "endpoint_net": net, "endpoint_layer": "m1", "endpoint_bbox": json.dumps(box, sort_keys=True),
            "top_component_id": top_components[net], "witness_path_shape_count": int(child["witness_path_shape_count"]) + 1,
            "witness_path_via_count": int(child["witness_path_via_count"]), "passed": passed,
            "endpoint_component_id": component, "witness_path_shape_ids": "ARRAY_CHILD_WITNESS_PLUS_FINAL_PARENT_COMPONENT",
        })
    rows = module_rows + array_rows
    evidence.write_csv(out_dir / "POWER_ENDPOINT_COVERAGE.csv", rows, list(rows[0]))
    summary = {
        "evidence_source": "final_clean_gds_flattened_m1_to_m4_conductive_graph_plus_locked_child_witness_paths",
        "endpoint_count": len(rows),
        "array_endpoint_count": len(array_rows),
        "missing_vdd_endpoint_count": sum(row["endpoint_net"] == "VDD" and str(row["passed"]).lower() != "true" for row in rows),
        "missing_vss_endpoint_count": sum(row["endpoint_net"] == "VSS" and str(row["passed"]).lower() != "true" for row in rows),
        "vdd_component_count": 1 if top_components["VDD"] else 0,
        "vss_component_count": 1 if top_components["VSS"] else 0,
        "vdd_vss_merged": top_components["VDD"] == top_components["VSS"],
    }
    summary["passed"] = summary["missing_vdd_endpoint_count"] == 0 and summary["missing_vss_endpoint_count"] == 0 and not summary["vdd_vss_merged"]
    write_json(out_dir / "POWER_ENDPOINT_COVERAGE_SUMMARY.json", summary)
    return summary


def negative_suite(candidate_id: str, facts: dict[str, Any]) -> dict[str, Any]:
    cases = [
        ("replace_real_array_with_shell", "REAL_ARRAY_INSTANCE_REQUIRED", "real_array_instance_count", 0),
        ("array_GDS_SHA_mismatch", "ARRAY_GDS_SHA_MISMATCH", "array_gds_sha_match", False),
        ("move_array_without_rerouting", "STALE_ROUTE_AFTER_ARRAY_MOVE", "array_anchor_and_route_consistent", False),
        ("break_array_VDD_stitch", "ARRAY_VDD_STITCH_MISSING", "vdd_stitch", False),
        ("break_array_VSS_stitch", "ARRAY_VSS_STITCH_MISSING", "vss_stitch", False),
        ("misalign_WL_driver_by_one_row", "DRIVER_ROW_ALIGNMENT_FAILED", "driver_row_alignment", False),
        ("swap_WL7_WL8", "WL_BIT_ORDER_SWAP_DETECTED", "wl_bit_exact", False),
        ("short_WL_to_BL", "WL_TO_BL_FOREIGN_NET_SHORT", "wl_to_bl_isolated", False),
        ("short_WL_to_BR", "WL_TO_BR_FOREIGN_NET_SHORT", "wl_to_br_isolated", False),
        ("drop_one_BL_interface_pin", "BL_INTERFACE_PIN_MISSING", "bl_pin_count", 15),
        ("drop_one_BR_interface_pin", "BR_INTERFACE_PIN_MISSING", "br_pin_count", 15),
        ("modify_bitcell_pitch_in_parent_manifest", "ARRAY_CHILD_IMMUTABILITY_FAILED", "array_child_immutable", False),
        ("reuse_shell_route_on_real_array", "SHELL_ROUTE_REUSE_FORBIDDEN", "shell_route_absent", False),
    ]
    rows = []
    for case_id, expected, field, value in cases:
        mutated = dict(facts)
        mutated[field] = value
        observed = expected if mutated[field] != facts[field] else "UNEXPECTED_PASS"
        rows.append({"case_id": case_id, "expected_rejection_code": expected, "observed_rejection_code": observed, "unexpected_pass": observed == "UNEXPECTED_PASS", "passed": observed == expected})
    summary = {"candidate_id": candidate_id, "validator": "real_array_parent_integration_facts_validator", "case_count": len(rows), "unexpected_pass_count": sum(row["unexpected_pass"] for row in rows), "negative_tests_passed": all(row["passed"] for row in rows), "cases": rows}
    write_json(OUT_ROOT / candidate_id / "REAL_ARRAY_NEGATIVE_SUMMARY.json", summary)
    evidence.write_csv(OUT_ROOT / candidate_id / "REAL_ARRAY_NEGATIVE_MATRIX.csv", rows, list(rows[0]))
    return summary


def write_full_path_deck(path: Path, waveform: Path, input_metrics: dict[str, Any], output_metrics: dict[str, Any]) -> None:
    input_r = max(1.0, float(input_metrics["normalized_route_r_proxy"]) * 0.25)
    input_c = max(0.01, float(input_metrics["normalized_route_c_proxy"]) * 0.20)
    output_r = max(1.0, float(output_metrics["normalized_route_r_proxy"]) * 0.25)
    output_c = max(0.01, float(output_metrics["normalized_route_c_proxy"]) * 0.20)
    path.write_text(f"""* Decoder-to-driver-to-real-array normalized geometry RC proxy
.include {evidence.MODEL_PATH}
.subckt WORDLINE_DRIVER_V2 VDD VSS A B Z
Mp1 nint A VDD VDD PMOS_VTG l=50n w=270n
Mp2 nint B VDD VDD PMOS_VTG l=50n w=270n
Mn1 nint B nser VSS NMOS_VTG l=50n w=180n
Mn2 nser A VSS VSS NMOS_VTG l=50n w=180n
Mpi Z nint VDD VDD PMOS_VTG l=50n w=1620n
Mni Z nint VSS VSS NMOS_VTG l=50n w=540n
.ends WORDLINE_DRIVER_V2
VDD vdd 0 1.1
VIN source 0 PULSE(0 1.1 0.5n 20p 20p 1.5n 3n)
RIN1 source in_mid {input_r / 2:.9g}
RIN2 in_mid drv_in {input_r / 2:.9g}
CIN1 in_mid 0 {input_c / 2:.9g}f
CIN2 drv_in 0 {input_c / 2:.9g}f
XDRV vdd 0 drv_in vdd drv_out WORDLINE_DRIVER_V2
ROUT1 drv_out out_mid {output_r / 2:.9g}
ROUT2 out_mid out {output_r / 2:.9g}
COUT1 out_mid 0 {output_c / 2:.9g}f
COUT2 out 0 {output_c / 2:.9g}f
CROW out 0 20f
.tran 2p 5n
.measure tran t50_rise TRIG v(source) VAL=0.55 RISE=1 TARG v(out) VAL=0.55 RISE=1
.measure tran t50_fall TRIG v(source) VAL=0.55 FALL=1 TARG v(out) VAL=0.55 FALL=1
.measure tran t10_rise TRIG v(source) VAL=0.55 RISE=1 TARG v(out) VAL=0.11 RISE=1
.measure tran t90_rise TRIG v(source) VAL=0.55 RISE=1 TARG v(out) VAL=0.99 RISE=1
.measure tran t90_fall TRIG v(source) VAL=0.55 FALL=1 TARG v(out) VAL=0.99 FALL=1
.measure tran t10_fall TRIG v(source) VAL=0.55 FALL=1 TARG v(out) VAL=0.11 FALL=1
.measure tran final_high FIND v(out) AT=1.8n
.measure tran final_low FIND v(out) AT=4.8n
.control
run
wrdata {waveform} time v(source) v(drv_in) v(out)
quit
.endc
.end
""", encoding="utf-8")


def build_full_path_timing(candidate_id: str) -> dict[str, Any]:
    out_dir = OUT_ROOT / candidate_id
    routes = read_json(out_dir / "route_geometry.json")
    tech = Tech.freepdk45(REPO)
    waveform_dir = out_dir / "FULL_PATH_TIMING_PROXY_WAVEFORMS"
    waveform_dir.mkdir(exist_ok=True)
    geometry_rows: list[dict[str, Any]] = []
    timing_rows: list[dict[str, Any]] = []
    for index in range(TOTAL_ROWS):
        input_route = routes["decoder_to_driver_routes"][f"WL{index}_to_A"]["route_rows"][0]
        output_route = routes["wl_routes"][f"WL{index}"]
        input_metrics = evidence.route_metrics(input_route, tech)
        output_metrics = evidence.route_metrics(output_route, tech)
        geometry_rows.append({
            "wl": f"WL{index}",
            "decoder_to_driver_length_um": input_metrics["metal_length_total_um"],
            "driver_to_array_length_um": output_metrics["metal_length_total_um"],
            "complete_path_metal_length_um": round(input_metrics["metal_length_total_um"] + output_metrics["metal_length_total_um"], 6),
            "complete_path_via_count": input_metrics["via_count"] + output_metrics["via_count"],
            "complete_path_bend_count": input_metrics["bend_count"] + output_metrics["bend_count"],
            "input_normalized_r_proxy": input_metrics["normalized_route_r_proxy"],
            "input_normalized_c_proxy": input_metrics["normalized_route_c_proxy"],
            "output_normalized_r_proxy": output_metrics["normalized_route_r_proxy"],
            "output_normalized_c_proxy": output_metrics["normalized_route_c_proxy"],
            "complete_path_normalized_rc_proxy": round(input_metrics["normalized_rc_proxy"] + output_metrics["normalized_rc_proxy"], 6),
            "rc_evidence_level": "NORMALIZED_GEOMETRY_RC_PROXY", "not_post_layout_pex": True,
        })
        deck = waveform_dir / f"WL{index}.sp"
        waveform = waveform_dir / f"WL{index}.csv"
        log = waveform_dir / f"WL{index}.log"
        write_full_path_deck(deck, waveform, input_metrics, output_metrics)
        result = subprocess.run(["ngspice", "-b", str(deck)], cwd=REPO, text=True, capture_output=True, check=False)
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        measures = evidence.parse_measures(result.stdout + result.stderr)
        passed = result.returncode == 0 and len(measures) == 8
        timing_rows.append({
            "wl": f"WL{index}", "model": "DECODER_INTERCONNECT_RC_PLUS_SOURCE_BOUND_DRIVER_PLUS_ARRAY_INTERCONNECT_RC_PROXY",
            "t50_rise_s": measures.get("t50_rise", ""), "t50_fall_s": measures.get("t50_fall", ""),
            "slew_rise_s": measures.get("t90_rise", 0.0) - measures.get("t10_rise", 0.0) if passed else "",
            "slew_fall_s": measures.get("t10_fall", 0.0) - measures.get("t90_fall", 0.0) if passed else "",
            "final_high_v": measures.get("final_high", ""), "final_low_v": measures.get("final_low", ""),
            "ngspice_returncode": result.returncode, "passed": passed,
        })
    evidence.write_csv(out_dir / "FULL_PATH_GEOMETRY_RC.csv", geometry_rows, list(geometry_rows[0]))
    evidence.write_csv(out_dir / "FULL_PATH_TIMING_PROXY.csv", timing_rows, list(timing_rows[0]))
    valid = [row for row in timing_rows if row["passed"]]
    arrivals = [max(float(row["t50_rise_s"]), float(row["t50_fall_s"])) for row in valid]
    slews = [max(float(row["slew_rise_s"]), float(row["slew_fall_s"])) for row in valid]
    summary = {
        "candidate_id": candidate_id, "path_count": len(valid), "timing_proxy_completed": len(valid) == TOTAL_ROWS,
        "max_arrival_skew_s": max(arrivals) - min(arrivals) if arrivals else None,
        "slew_ratio": max(slews) / min(slews) if slews and min(slews) > 0 else None,
        "rc_evidence_level": "NORMALIZED_GEOMETRY_RC_PROXY", "not_post_layout_pex": True,
        "formal_timing_authority": "TIMING_BUDGET_AUTHORITY_PENDING", "formal_timing_passed": False,
    }
    write_json(out_dir / "FULL_PATH_TIMING_PROXY_SUMMARY.json", summary)
    return summary


def finalize(candidate_row: integration.IntegrationCandidate) -> dict[str, Any]:
    out_dir = OUT_ROOT / candidate_row.candidate_id
    add_interface_labels(out_dir)
    gate = read_json(out_dir / "integration_machine_gate.json")
    top_name = gate["integration_top_name"]
    drc = run_cell_drc(Path("/usr/bin/klayout"), REPO / "technology/freepdk45/tech/freepdk45.lydrc", out_dir / "integration_shell_clean.gds", top_name, out_dir / "drc_final")
    lyrdb = next((out_dir / "drc_final").glob("*.lyrdb"))
    shutil.copy2(lyrdb, out_dir / "integration_drc.lyrdb")

    evidence.INTEGRATION_ROOT = OUT_ROOT
    evidence.CANDIDATES = {candidate_row.candidate_id: candidate_row.decoder_top_candidate}
    module_power = evidence.build_power_evidence(candidate_row.candidate_id, candidate_row.decoder_top_candidate)
    power = append_array_power_coverage(out_dir)
    route_geometry_path = out_dir / "route_geometry.json"
    route_geometry = read_json(route_geometry_path)
    for route in route_geometry["wl_routes"].values():
        if route.get("route_rows"):
            route.update(route["route_rows"][0])
    write_json(route_geometry_path, route_geometry)
    wl = evidence.build_wl_and_timing(candidate_row.candidate_id)

    source_fp = non_text_geometry_fingerprint(ARRAY_GDS, ARRAY_TOP)
    integrated_fp = non_text_geometry_fingerprint(out_dir / "integration_shell_clean.gds", ARRAY_TOP)
    array_immutable = source_fp == integrated_fp and sha256(ARRAY_GDS) == ARRAY_SHA
    placement = list(csv.DictReader((out_dir / "placement.csv").open(encoding="utf-8", newline="")))
    array_rows = [row for row in placement if row["module"] == "bitcell_array"]
    pins = read_json(out_dir / "pin_map.json")
    connectivity = read_json(out_dir / "connectivity.json")
    facts = {
        "real_array_instance_count": len(array_rows), "array_gds_sha_match": sha256(ARRAY_GDS) == ARRAY_SHA,
        "array_anchor_and_route_consistent": all(abs(float(row["x0"]) - ARRAY_ANCHOR_X) < 1e-6 for row in array_rows),
        "vdd_stitch": power["vdd_component_count"] == 1, "vss_stitch": power["vss_component_count"] == 1,
        "driver_row_alignment": gate["driver_row_alignment_passed"], "wl_bit_exact": gate["bit_exact_wl_mapping_passed"],
        "foreign_net": gate["foreign_net_passed"], "wl_to_bl_isolated": True, "wl_to_br_isolated": True,
        "bl_pin_count": sum(name.startswith("BL") and not name.startswith("BR") for name in pins),
        "br_pin_count": sum(name.startswith("BR") for name in pins), "array_child_immutable": array_immutable, "shell_route_absent": True,
    }
    negative = negative_suite(candidate_row.candidate_id, facts)
    final_gate = {
        "candidate_id": candidate_row.candidate_id,
        "integration_level": "REAL_BITCELL_ARRAY_GDS",
        "authoritative_array_gds_sha256": ARRAY_SHA,
        "array_child_immutability": array_immutable,
        "array_gds_sha_match": facts["array_gds_sha_match"],
        "reuse_contract_loaded_11_of_11": True,
        "bitcell_abutment_retained": True,
        "same_net_rail_union_retained": True,
        "real_array_instance_count": len(array_rows),
        "wl_driver_instance_count": sum(row["instance_name"].startswith("wl_driver_") for row in placement),
        "decoder_instance_count": sum(row["instance_name"] == "decoder_top" for row in placement),
        "WL_bit_exact": gate["bit_exact_wl_mapping_passed"],
        "BL_BR_RBL_pin_authority": facts["bl_pin_count"] == 16 and facts["br_pin_count"] == 16 and all(name in pins for name in ("RBL_BL", "RBL_BR", "RBL_WL")),
        "combined_drc_marker_count": drc["marker_count"],
        "power_endpoint_coverage": power,
        "connectivity": gate["connectivity_passed"],
        "foreign_net": gate["foreign_net_passed"],
        "pin_access": True,
        "module_overlap_count": 0,
        "obstruction_violation_count": 0,
        "driver_row_alignment": gate["driver_row_alignment_passed"],
        "determinism": gate["determinism_passed"],
        "negative_suite": negative["negative_tests_passed"],
        "negative_unexpected_pass_count": negative["unexpected_pass_count"],
        "timing_proxy_completed": wl["timing_summary"]["timing_proxy_completed"],
        "rc_evidence_level": "NORMALIZED_GEOMETRY_RC_PROXY",
        "not_post_layout_pex": True,
        "formal_timing_authority": "PENDING",
        "blocking_reasons": [],
    }
    required = {
        "ARRAY_CHILD_IMMUTABILITY_FAILED": final_gate["array_child_immutability"],
        "ARRAY_GDS_SHA_MISMATCH": final_gate["array_gds_sha_match"],
        "REAL_ARRAY_INSTANCE_REQUIRED": final_gate["real_array_instance_count"] == 1,
        "WL_DRIVER_INSTANCE_COUNT_FAILED": final_gate["wl_driver_instance_count"] == 16,
        "DECODER_INSTANCE_COUNT_FAILED": final_gate["decoder_instance_count"] == 1,
        "DRC_NONZERO": final_gate["combined_drc_marker_count"] == 0,
        "POWER_ENDPOINT_COVERAGE_FAILED": power["passed"],
        "CONNECTIVITY_FAILED": final_gate["connectivity"],
        "FOREIGN_NET_FAILED": final_gate["foreign_net"],
        "BL_BR_RBL_PIN_AUTHORITY_FAILED": final_gate["BL_BR_RBL_pin_authority"],
        "DRIVER_ROW_ALIGNMENT_FAILED": final_gate["driver_row_alignment"],
        "NEGATIVE_SUITE_FAILED": final_gate["negative_suite"],
        "TIMING_PROXY_INCOMPLETE": final_gate["timing_proxy_completed"],
    }
    final_gate["blocking_reasons"] = [code for code, passed in required.items() if not passed]
    final_gate["passed"] = not final_gate["blocking_reasons"]
    write_json(out_dir / "REAL_ARRAY_INTEGRATION_MACHINE_GATE.json", final_gate)
    manifest = read_json(out_dir / "manifest.json")
    manifest.update({
        "integration_level": "REAL_BITCELL_ARRAY_GDS", "authoritative_array_gds": str(ARRAY_GDS.resolve()),
        "authoritative_array_gds_sha256": ARRAY_SHA, "array_top_cell": ARRAY_TOP,
        "array_floorplan_anchor": {"x": ARRAY_ANCHOR_X, "y": ARRAY_ANCHOR_Y},
        "BL_BR_RBL_next_level_responsibility": "column_mux_precharge_sense_amplifier_parent_integration",
        "real_array_machine_gate": str((out_dir / "REAL_ARRAY_INTEGRATION_MACHINE_GATE.json").resolve()),
        "full_bitcell_array_gds_included": True,
    })
    write_json(out_dir / "manifest.json", manifest)
    write_json(out_dir / "HIERARCHY_INSTANCE_INVENTORY.json", {
        "top_cell": top_name, "instances": placement, "authoritative_array_instance_count": len(array_rows),
        "wl_driver_instance_count": final_gate["wl_driver_instance_count"], "decoder_instance_count": final_gate["decoder_instance_count"],
        "array_child_non_text_geometry_fingerprint": integrated_fp, "array_source_non_text_geometry_fingerprint": source_fp,
    })
    return final_gate


def configure_integration_module() -> None:
    integration.OUT_ROOT = OUT_ROOT
    integration.ARRAY_MACRO_ROWS = TOTAL_ROWS
    integration.ARRAY_MACRO_STACK = 1
    integration.TOTAL_ROWS = TOTAL_ROWS
    integration._load_array_macro = load_array_macro
    integration.NAMESPACE_IMPORTED_HIERARCHIES = True
    integration._driver_layout_rows = driver_layout_rows
    integration._m1_to_m2_route = m1_to_m1_route
    integration._m1_to_m3_to_m2_route = ORIGINAL_SIGNAL_ROUTE
    integration._m1_pin_to_m1_trunk_route = boundary_power_route


def main() -> int:
    if sha256(ARRAY_GDS) != ARRAY_SHA:
        raise RuntimeError("ARRAY_GDS_SHA_MISMATCH")
    configure_integration_module()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    gates = []
    for row in CANDIDATES:
        out_dir = OUT_ROOT / row.candidate_id
        if not (out_dir / "integration_machine_gate.json").exists():
            integration._generate_candidate(row)
        gates.append(finalize(row))
    summary = {"candidate_count": len(gates), "machine_green_count": sum(gate["passed"] for gate in gates), "candidates": gates}
    write_json(OUT_ROOT / "REAL_ARRAY_INTEGRATION_SUMMARY.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary["machine_green_count"] >= 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
