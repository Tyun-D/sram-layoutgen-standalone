#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import sys
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import _component_for_bbox
from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity
from sram_layoutgen.tech import Tech


OUT_DIR = REPO_ROOT / "outputs" / "PROJECT_decoder_wl_array_integration_shell" / "candidate_true_wl_driver_array_oriented"
DOCS_DIR = REPO_ROOT / "docs"
TOP_DIR = REPO_ROOT / "outputs" / "PROJECT_decoder_top_v3" / "candidate_true_wl_driver_array_oriented"
CHILD_DIR = REPO_ROOT / "outputs" / "PROJECT_decoder_child_v3" / "decoder_gate_cells_v3" / "output_oriented_multiline"
DRIVER_DIR = REPO_ROOT / "outputs" / "PROJECT_wordline_driver_v2_regen" / "current_supported_config"


@dataclass(frozen=True)
class Endpoint:
    instance: str
    cell: str
    orientation: str
    endpoint_net: str
    endpoint_layer: str
    endpoint_bbox: dict[str, float]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _box_center(box: dict[str, float]) -> tuple[float, float]:
    return (round((float(box["lx"]) + float(box["rx"])) * 0.5, 6), round((float(box["by"]) + float(box["uy"])) * 0.5, 6))


def _transform_pin_map(pin_map: dict[str, list[dict[str, float]]], x_shift: float, y_shift: float) -> dict[str, list[dict[str, float]]]:
    out: dict[str, list[dict[str, float]]] = {}
    for name, boxes in pin_map.items():
        out[name] = []
        for box in boxes:
            out[name].append(
                {
                    **({"layer": box["layer"]} if "layer" in box else {}),
                    "lx": round(float(box["lx"]) + x_shift, 6),
                    "by": round(float(box["by"]) + y_shift, 6),
                    "rx": round(float(box["rx"]) + x_shift, 6),
                    "uy": round(float(box["uy"]) + y_shift, 6),
                }
            )
    return out


def _build_array_physical_shell_pin_map() -> tuple[dict[str, list[dict[str, float]]], float]:
    tech = Tech.freepdk45(REPO_ROOT)
    generation = _read_json(REPO_ROOT / "outputs" / "openyield_module_gds" / "bitcell_array" / "generation_report.json")
    bbox = generation["bbox"]
    row_pitch = round(float(bbox["height"]) / int(generation["array_rows"]), 6)
    shell_height = round(row_pitch * 16, 6)
    shell_width = round(float(bbox["width"]), 6)
    m2_width = tech.layer("m2").min_width
    m1_width = tech.layer("m1").min_width
    pin_map: dict[str, list[dict[str, float]]] = {
        "VDD": [{"layer": "m1", "lx": round(shell_width * 0.3 - m1_width * 0.5, 6), "by": round(shell_height - m1_width, 6), "rx": round(shell_width * 0.3 + m1_width * 0.5, 6), "uy": shell_height}],
        "VSS": [{"layer": "m1", "lx": round(shell_width * 0.7 - m1_width * 0.5, 6), "by": 0.0, "rx": round(shell_width * 0.7 + m1_width * 0.5, 6), "uy": round(m1_width, 6)}],
    }
    for wl_index in range(16):
        y = round(wl_index * row_pitch + row_pitch * 0.5, 6)
        x = 0.15
        pin_map[f"WL{wl_index}"] = [{"layer": "m2", "lx": x, "by": round(y - m2_width * 0.5, 6), "rx": round(x + m2_width, 6), "uy": round(y + m2_width * 0.5, 6)}]
    return pin_map, row_pitch


def _shape_to_component(graph: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for component in graph["components"]:
        for member in component["members"]:
            lookup[member] = component["component_id"]
    return lookup


def _build_shape_graph(graph: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    rects: dict[str, dict[str, Any]] = {}
    for layer_name, rows in graph.get("rectangles", {}).items():
        for row in rows:
            rects[row["rect_id"]] = {
                "rect_id": row["rect_id"],
                "layer": layer_name,
                "bbox": row["bbox"],
                "source": row.get("source"),
            }
    adjacency: dict[str, set[str]] = {rect_id: set() for rect_id in rects}
    for link_map_name in ("contact_links", "via1_links", "via2_links"):
        for rect_id, linked in graph.get(link_map_name, {}).items():
            if rect_id not in rects:
                continue
            for other in linked:
                if other not in rects:
                    continue
                adjacency.setdefault(rect_id, set()).add(other)
                adjacency.setdefault(other, set()).add(rect_id)
    for layer_name, rows in graph.get("rectangles", {}).items():
        if layer_name not in {"m1", "m2", "m3", "poly", "active_segments", "contact", "via1", "via2"}:
            continue
        for idx, left in enumerate(rows):
            left_bbox = left["bbox"]
            for right in rows[idx + 1 :]:
                right_bbox = right["bbox"]
                if not (
                    left_bbox[2] < right_bbox[0] - 1e-6
                    or right_bbox[2] < left_bbox[0] - 1e-6
                    or left_bbox[3] < right_bbox[1] - 1e-6
                    or right_bbox[3] < left_bbox[1] - 1e-6
                ):
                    adjacency[left["rect_id"]].add(right["rect_id"])
                    adjacency[right["rect_id"]].add(left["rect_id"])
    return rects, adjacency


def _rect_ids_for_bbox(graph: dict[str, Any], bbox: dict[str, float], layers: set[str]) -> list[str]:
    cx, cy = _box_center(bbox)
    hits: list[str] = []
    for layer_name, rects in graph.get("rectangles", {}).items():
        if layer_name not in layers:
            continue
        for rect in rects:
            lx, by, rx, uy = rect["bbox"]
            if lx - 1e-6 <= cx <= rx + 1e-6 and by - 1e-6 <= cy <= uy + 1e-6:
                hits.append(rect["rect_id"])
    return sorted(hits)


def _shortest_path(adjacency: dict[str, set[str]], start_ids: list[str], target_ids: list[str]) -> list[str]:
    if not start_ids or not target_ids:
        return []
    target_set = set(target_ids)
    queue = deque((start_id, [start_id]) for start_id in start_ids)
    seen = set(start_ids)
    while queue:
        shape_id, path = queue.popleft()
        if shape_id in target_set:
            return path
        for neighbor in sorted(adjacency.get(shape_id, set())):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return []


def _load_instance_endpoints() -> tuple[list[Endpoint], dict[str, dict[str, float]], float]:
    child_pin_map = _read_json(CHILD_DIR / "pin_map.json")
    top_pin_map = _read_json(TOP_DIR / "pin_map.json")
    driver_pin_map = _read_json(DRIVER_DIR / "wordline_driver_v2_pin_map.json")
    shell_pin_map, row_pitch = _build_array_physical_shell_pin_map()
    top_place_rows = list(csv.DictReader((TOP_DIR / "placement.csv").open(encoding="utf-8", newline="")))
    integration_rows = list(csv.DictReader((OUT_DIR / "placement.csv").open(encoding="utf-8", newline="")))

    endpoints: list[Endpoint] = []
    for row in top_place_rows:
        placed = _transform_pin_map(child_pin_map, float(row["x0"]), float(row["y0"]))
        for net_name in ("VDD", "VSS"):
            for box in placed[net_name]:
                endpoints.append(
                    Endpoint(
                        instance=str(row["instance_name"]),
                        cell=str(row["module"]),
                        orientation=str(row["orientation"]),
                        endpoint_net=net_name,
                        endpoint_layer=str(box.get("layer", "m1")),
                        endpoint_bbox=box,
                    )
                )
    for row in integration_rows:
        name = str(row["instance_name"])
        if name.startswith("wl_driver_"):
            placed = _transform_pin_map(driver_pin_map, float(row["x0"]), float(row["y0"]))
            for net_name in ("VDD", "VSS"):
                endpoints.append(
                    Endpoint(
                        instance=name,
                        cell=str(row["module"]),
                        orientation=str(row["orientation"]),
                        endpoint_net=net_name,
                        endpoint_layer=str(placed[net_name][0].get("layer", "m1")),
                        endpoint_bbox=placed[net_name][0],
                    )
                )
        elif name.startswith("approved_array_physical_shell_"):
            placed = _transform_pin_map(shell_pin_map, float(row["x0"]), float(row["y0"]))
            for net_name in ("VDD", "VSS"):
                endpoints.append(
                    Endpoint(
                        instance=name,
                        cell=str(row["module"]),
                        orientation=str(row["orientation"]),
                        endpoint_net=net_name,
                        endpoint_layer=str(placed[net_name][0].get("layer", "m1")),
                        endpoint_bbox=placed[net_name][0],
                    )
                )
    top_power_pins = {
        "VDD": _read_json(OUT_DIR / "pin_map.json")["VDD"][0],
        "VSS": _read_json(OUT_DIR / "pin_map.json")["VSS"][0],
    }
    return endpoints, top_power_pins, row_pitch


def _route_metrics(route: dict[str, Any], tech: Tech) -> dict[str, Any]:
    layer_lengths = {"m1": 0.0, "m2": 0.0, "m3": 0.0}
    via_count = 0
    shape_count = 0
    bend_count = 0
    ordered = [
        "source_m1_landing_bbox",
        "source_m2_vertical_bbox",
        "source_m2_top_landing_bbox",
        "source_via2_bbox",
        "source_m3_landing_bbox",
        "m3_trunk_bbox",
        "dest_m3_landing_bbox",
        "dest_top_via2_bbox",
        "dest_m2_top_landing_bbox",
        "dest_m2_vertical_bbox",
        "dest_m2_landing_bbox",
    ]
    last_axis: str | None = None
    for key in ordered:
        box = route.get(key)
        if not isinstance(box, dict) or not {"lx", "by", "rx", "uy"} <= set(box):
            continue
        shape_count += 1
        width = abs(float(box["rx"]) - float(box["lx"]))
        height = abs(float(box["uy"]) - float(box["by"]))
        if "via" in key:
            via_count += 1
            continue
        if "m1" in key:
            layer = "m1"
        elif "m2" in key:
            layer = "m2"
        else:
            layer = "m3"
        length = max(width, height)
        layer_lengths[layer] += length
        axis = "vertical" if height > width else "horizontal"
        if last_axis is not None and axis != last_axis:
            bend_count += 1
        last_axis = axis
    via2 = tech.via_between("m2", "m3")
    via_cost = via2.cost if via2 is not None else 1.0
    normalized_r = sum(layer_lengths[layer] / max(tech.layer(layer).min_width, 1e-9) for layer in ("m1", "m2", "m3")) + via_count * via_cost
    normalized_c = sum(layer_lengths[layer] * tech.layer(layer).pitch for layer in ("m1", "m2", "m3"))
    return {
        "m1_length": round(layer_lengths["m1"], 6),
        "m2_length": round(layer_lengths["m2"], 6),
        "m3_length": round(layer_lengths["m3"], 6),
        "via_count": via_count,
        "bend_count": bend_count,
        "shape_count": shape_count,
        "normalized_route_r_proxy": round(normalized_r, 6),
        "normalized_route_c_proxy": round(normalized_c, 6),
        "normalized_rc_proxy": round(normalized_r * normalized_c, 6),
        "rc_model_kind": "NORMALIZED_GEOMETRY_RC_PROXY",
    }


def _build_power_witness_atlas(rows: list[dict[str, Any]], graph_rects: dict[str, dict[str, Any]], top_power_pins: dict[str, dict[str, float]], target: Path) -> None:
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    top = lib.new_cell("POWER_WITNESS_ATLAS")
    layer_by_name = {"m1": 11, "m2": 13, "m3": 15, "via1": 12, "via2": 14, "poly": 9, "active_segments": 1, "contact": 10}
    for row in rows:
        if not row["passed"]:
            continue
        for shape_id in row["witness_path_shape_ids"]:
            rect = graph_rects.get(shape_id)
            if rect is None:
                continue
            bbox = rect["bbox"]
            layer = layer_by_name.get(rect["layer"], 201)
            top.add(gdstk.rectangle((bbox[0], bbox[1]), (bbox[2], bbox[3]), layer=layer, datatype=0))
        endpoint = row["endpoint_bbox_raw"]
        top.add(gdstk.rectangle((endpoint["lx"], endpoint["by"]), (endpoint["rx"], endpoint["uy"]), layer=210, datatype=0))
        top.add(gdstk.Label(f"{row['instance']}::{row['endpoint_net']}", _box_center(endpoint), layer=239, texttype=0))
    for net_name, bbox in top_power_pins.items():
        top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=211, datatype=0))
        top.add(gdstk.Label(f"TOP::{net_name}", _box_center(bbox), layer=239, texttype=0))
    lib.write_gds(target)


def main() -> int:
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    graph = extract_physical_connectivity(OUT_DIR / "integration_shell_clean.gds", "candidate_true_wl_driver_array_oriented_integration_shell")
    rects, adjacency = _build_shape_graph(graph)
    endpoints, top_power_pins, row_pitch = _load_instance_endpoints()
    shape_to_component = _shape_to_component(graph)
    top_power_components = {
        net_name: _component_for_bbox(graph, bbox, {"m1", "m2", "m3"})
        for net_name, bbox in top_power_pins.items()
    }

    coverage_rows: list[dict[str, Any]] = []
    missing_vdd = 0
    missing_vss = 0
    witness_failures = 0
    for endpoint in endpoints:
        endpoint_component = _component_for_bbox(graph, endpoint.endpoint_bbox, {"m1", "m2", "m3"})
        endpoint_shapes = _rect_ids_for_bbox(graph, endpoint.endpoint_bbox, {"m1", "m2", "m3"})
        target_shapes = _rect_ids_for_bbox(graph, top_power_pins[endpoint.endpoint_net], {"m1", "m2", "m3"})
        witness_path = _shortest_path(adjacency, endpoint_shapes, target_shapes) if endpoint_component == top_power_components.get(endpoint.endpoint_net) else []
        witness_vias = sum(1 for shape_id in witness_path if rects.get(shape_id, {}).get("layer") in {"via1", "via2"})
        passed = bool(endpoint_component) and endpoint_component == top_power_components.get(endpoint.endpoint_net) and bool(witness_path)
        if endpoint.endpoint_net == "VDD" and not passed:
            missing_vdd += 1
        if endpoint.endpoint_net == "VSS" and not passed:
            missing_vss += 1
        if not passed:
            witness_failures += 1
        coverage_rows.append(
            {
                "instance": endpoint.instance,
                "cell": endpoint.cell,
                "orientation": endpoint.orientation,
                "endpoint_net": endpoint.endpoint_net,
                "endpoint_layer": endpoint.endpoint_layer,
                "endpoint_bbox": json.dumps(endpoint.endpoint_bbox, sort_keys=True),
                "endpoint_bbox_raw": endpoint.endpoint_bbox,
                "top_component_id": top_power_components.get(endpoint.endpoint_net),
                "witness_path_shape_count": len(witness_path),
                "witness_path_via_count": witness_vias,
                "passed": passed,
                "endpoint_component_id": endpoint_component,
                "witness_path_shape_ids": json.dumps(witness_path),
            }
        )
    csv_rows = [{key: value for key, value in row.items() if key != "endpoint_bbox_raw"} for row in coverage_rows]
    _write_csv(
        OUT_DIR / "POWER_ENDPOINT_COVERAGE.csv",
        csv_rows,
        [
            "instance",
            "cell",
            "orientation",
            "endpoint_net",
            "endpoint_layer",
            "endpoint_bbox",
            "top_component_id",
            "witness_path_shape_count",
            "witness_path_via_count",
            "passed",
            "endpoint_component_id",
            "witness_path_shape_ids",
        ],
    )
    _build_power_witness_atlas(coverage_rows, rects, top_power_pins, OUT_DIR / "POWER_WITNESS_ATLAS.gds")

    route_geometry = _read_json(OUT_DIR / "route_geometry.json")
    tech = Tech.freepdk45(REPO_ROOT)
    wl_rows: list[dict[str, Any]] = []
    y_alignment_rows: list[dict[str, Any]] = []
    for wl_name, route in sorted(route_geometry["wl_routes"].items(), key=lambda item: int(item[0][2:])):
        metrics = _route_metrics(route, tech)
        src_cx, src_cy = _box_center(route["source_bbox"])
        dst_cx, dst_cy = _box_center(route["dest_bbox"])
        wl_rows.append(
            {
                "wl": wl_name,
                "driver_output_center_x": src_cx,
                "driver_output_center_y": src_cy,
                "array_wl_center_x": dst_cx,
                "array_wl_center_y": dst_cy,
                "driver_array_abs_delta_y": round(abs(src_cy - dst_cy), 6),
                "driver_array_abs_delta_y_over_row_pitch": round(abs(src_cy - dst_cy) / row_pitch, 6),
                "driver_to_array_crossing_proxy": src_cy != dst_cy,
                **metrics,
            }
        )
        y_alignment_rows.append({"wl": wl_name, "delta_y": abs(src_cy - dst_cy)})
    _write_csv(
        OUT_DIR / "WL_GEOMETRY_RC.csv",
        wl_rows,
        [
            "wl",
            "driver_output_center_x",
            "driver_output_center_y",
            "array_wl_center_x",
            "array_wl_center_y",
            "driver_array_abs_delta_y",
            "driver_array_abs_delta_y_over_row_pitch",
            "driver_to_array_crossing_proxy",
            "m1_length",
            "m2_length",
            "m3_length",
            "via_count",
            "bend_count",
            "shape_count",
            "normalized_route_r_proxy",
            "normalized_route_c_proxy",
            "normalized_rc_proxy",
            "rc_model_kind",
        ],
    )

    placement_rows = list(csv.DictReader((OUT_DIR / "placement.csv").open(encoding="utf-8", newline="")))
    driver_rows = [row for row in placement_rows if row["instance_name"].startswith("wl_driver_")]
    unique_driver_y = sorted({round(float(row["y0"]), 6) for row in driver_rows})
    array_row_pitch = row_pitch
    wl_metric_summary = {
        "row_pitch": row_pitch,
        "driver_unique_y0": unique_driver_y,
        "driver_column_count": len(driver_rows),
        "driver_row_count": len(unique_driver_y),
        "driver_layout_pattern": f"{len(driver_rows)}x{len(unique_driver_y)}",
        "max_wl_length_proxy": max(row["normalized_rc_proxy"] for row in wl_rows),
        "min_wl_length_proxy": min(row["normalized_rc_proxy"] for row in wl_rows),
        "max_via_count": max(row["via_count"] for row in wl_rows),
        "min_via_count": min(row["via_count"] for row in wl_rows),
        "max_bend_count": max(row["bend_count"] for row in wl_rows),
        "min_bend_count": min(row["bend_count"] for row in wl_rows),
    }

    forensic = {
        "generated_at": created_at,
        "candidate_id": "candidate_true_wl_driver_array_oriented",
        "clean_gds_opened": str((OUT_DIR / "integration_shell_clean.gds").resolve()),
        "atlas_opened_for_truth": False,
        "opened_artifact_kind": "Level_A_final_clean_gds",
        "classification": [
            "INTERFACE_ROUTING_HARNESS_MACHINE_PASS",
            "FINAL_SRAM_PHYSICAL_ARCHITECTURE_NOT_APPROVED",
            "POWER_VISUAL_AND_GEOMETRY_WITNESS_REVIEW_PENDING",
            "WL_TIMING_BALANCE_NOT_PROVEN",
            "PLACEMENT_SEARCH_NOT_EXHAUSTED",
            "ARRAY_INTEGRATION_LEVEL=FLOORPLAN_FEASIBILITY_SHELL",
            "FULL_BITCELL_ARRAY_GDS_INTEGRATION=PENDING",
        ],
        "machine_gate_classification_demoted_from_final_pass": True,
        "array_object_type": "approved_nonzero_physical_shell",
        "full_bitcell_array_gds_included": False,
        "actual_array_object_from_manifest": _read_json(OUT_DIR / "manifest.json")["real_module_evidence"]["bitcell_array_gds"],
        "power_endpoint_summary": {
            "total_endpoints": len(coverage_rows),
            "missing_vdd_endpoint_count": missing_vdd,
            "missing_vss_endpoint_count": missing_vss,
            "vdd_component_count": len({row["top_component_id"] for row in coverage_rows if row["endpoint_net"] == "VDD" and row["top_component_id"]}),
            "vss_component_count": len({row["top_component_id"] for row in coverage_rows if row["endpoint_net"] == "VSS" and row["top_component_id"]}),
            "vdd_vss_merged": top_power_components["VDD"] == top_power_components["VSS"],
            "power_endpoint_coverage_passed": witness_failures == 0 and top_power_components["VDD"] != top_power_components["VSS"],
        },
        "wl_driver_placement": {
            "driver_instance_count": len(driver_rows),
            "driver_unique_y0": unique_driver_y,
            "driver_is_single_horizontal_row": len(unique_driver_y) == 1,
            "driver_layout_pattern": f"{len(driver_rows)}x{len(unique_driver_y)}",
        },
        "wl_route_geometry_summary": wl_metric_summary,
        "level_a_evidence": {
            "final_clean_gds": str((OUT_DIR / "integration_shell_clean.gds").resolve()),
            "power_endpoint_coverage_csv": str((OUT_DIR / "POWER_ENDPOINT_COVERAGE.csv").resolve()),
            "power_witness_atlas": str((OUT_DIR / "POWER_WITNESS_ATLAS.gds").resolve()),
            "wl_geometry_rc_csv": str((OUT_DIR / "WL_GEOMETRY_RC.csv").resolve()),
            "drc_database": str((OUT_DIR / "integration_drc.lyrdb").resolve()),
        },
    }
    if not forensic["power_endpoint_summary"]["power_endpoint_coverage_passed"]:
        forensic["current_candidate_power_status"] = "CURRENT_CANDIDATE_POWER_FAILED"
    else:
        forensic["current_candidate_power_status"] = "CURRENT_CANDIDATE_POWER_WITNESS_PROVEN"
    _write_json(DOCS_DIR / "CURRENT_CANDIDATE_FORENSIC_AUDIT.json", forensic)

    md_lines = [
        "# Current Candidate Forensic Audit",
        "",
        f"- generated_at: `{created_at}`",
        f"- candidate_id: `{forensic['candidate_id']}`",
        f"- opened_artifact_kind: `{forensic['opened_artifact_kind']}`",
        f"- classification: `{', '.join(forensic['classification'])}`",
        f"- array_object_type: `{forensic['array_object_type']}`",
        f"- full_bitcell_array_gds_included: `{str(forensic['full_bitcell_array_gds_included']).lower()}`",
        f"- driver_layout_pattern: `{forensic['wl_driver_placement']['driver_layout_pattern']}`",
        f"- driver_is_single_horizontal_row: `{forensic['wl_driver_placement']['driver_is_single_horizontal_row']}`",
        f"- missing_vdd_endpoint_count: `{forensic['power_endpoint_summary']['missing_vdd_endpoint_count']}`",
        f"- missing_vss_endpoint_count: `{forensic['power_endpoint_summary']['missing_vss_endpoint_count']}`",
        f"- power_endpoint_coverage_passed: `{forensic['power_endpoint_summary']['power_endpoint_coverage_passed']}`",
        f"- current_candidate_power_status: `{forensic['current_candidate_power_status']}`",
        "",
        "## Findings",
        "",
        "- The current integrated artifact is a machine-passing interface routing harness, not an approved final SRAM physical architecture.",
        "- The array object is `approved_nonzero_physical_shell`, so the integration level is capped at `FLOORPLAN_FEASIBILITY_SHELL`.",
        "- All 16 WL drivers are placed in one horizontal row, which violates the preferred row-aligned vertical-driver architecture.",
        "- WL routes use unequal lengths, bend counts, and via counts; `WL_GEOMETRY_RC.csv` is the controlling Level B evidence for that imbalance.",
        "- Power witness results are derived from the final clean GDS conductive graph and recorded in `POWER_ENDPOINT_COVERAGE.csv` and `POWER_WITNESS_ATLAS.gds`.",
    ]
    _write_text(DOCS_DIR / "CURRENT_CANDIDATE_FORENSIC_AUDIT.md", "\n".join(md_lines) + "\n")

    contract = {
        "generated_at": created_at,
        "array_side": "right",
        "array_object_type": "approved_nonzero_physical_shell",
        "row_pitch": row_pitch,
        "wl_y_coordinates": {row["wl"]: row["array_wl_center_y"] for row in wl_rows},
        "driver_size": {"width": 2.16, "height": 1.8875},
        "driver_output_pin": "Z",
        "driver_input_pins": ["A", "B"],
        "legal_driver_orientations": ["R0"],
        "decoder_stage_legal_orientations": ["R0"],
        "allowed_placement_regions": {
            "decoder_control_side": {"x0": 0.0, "x1": 54.2525},
            "driver_channel": {"x0": 59.2525, "x1": 120.8125},
            "array_boundary_side": {"x0": 126.6125, "x1": 130.1925},
        },
        "power_rail_directions": {"m1": "horizontal", "m2": "vertical", "m3": "horizontal"},
        "routing_layer_preferences": {
            "driver_output_to_array": ["m1", "via1", "m2", "via2", "m3", "via2", "m2"],
            "power": ["m1"],
        },
        "timing_proxy_thresholds": {
            "arrival_skew_fraction_of_active_window_max": 0.10,
            "arrival_skew_fraction_of_clock_period_max": 0.05,
            "slew_ratio_max": 1.20,
            "normalized_rc_proxy_over_median_max": 1.25,
            "timing_budget_authority": "TIMING_BUDGET_AUTHORITY_PENDING",
        },
    }
    _write_json(DOCS_DIR / "DECODER_WL_ARRAY_PHYSICAL_ARCHITECTURE_CONTRACT.json", contract)
    contract_md = [
        "# Decoder WL Array Physical Architecture Contract",
        "",
        f"- generated_at: `{created_at}`",
        f"- array_side: `{contract['array_side']}`",
        f"- array_object_type: `{contract['array_object_type']}`",
        f"- row_pitch: `{row_pitch}`",
        f"- driver_size: `{contract['driver_size']['width']} x {contract['driver_size']['height']}`",
        f"- legal_driver_orientations: `{', '.join(contract['legal_driver_orientations'])}`",
        f"- decoder_stage_legal_orientations: `{', '.join(contract['decoder_stage_legal_orientations'])}`",
        "",
        "## WL Contract",
        "",
        "- WL0-WL15 must remain monotonic and bit-exact.",
        "- Driver outputs should align to array row Y centers and avoid staircase routing as a final architecture.",
        "- Timing proxy thresholds are engineering limits only until authoritative timing contracts exist.",
    ]
    _write_text(DOCS_DIR / "DECODER_WL_ARRAY_PHYSICAL_ARCHITECTURE_CONTRACT.md", "\n".join(contract_md) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
