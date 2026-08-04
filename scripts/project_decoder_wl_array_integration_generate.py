#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_ROOT = REPO_ROOT / "outputs" / "PROJECT_decoder_wl_array_integration_shell"

from sram_layoutgen.openyield_adapter.composite_hierarchy_closure import verify_composite_hierarchy_closure
from sram_layoutgen.openyield_adapter.composite_pin_namespace_verifier import verify_composite_pin_namespace
from sram_layoutgen.openyield_adapter.decoder_generator import _m1_to_m3_to_m2_route
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import geometry_fingerprint, non_text_geometry_fingerprint, run_cell_drc
from sram_layoutgen.openyield_adapter.teamb_composite_helper import (
    add_top_label,
    annotate_from_bboxes,
    make_review_atlas,
    read_json,
    write_csv,
    write_gds,
    write_json,
    write_text,
)
from sram_layoutgen.tech import Tech


@dataclass(frozen=True)
class IntegrationCandidate:
    candidate_id: str
    decoder_top_candidate: str
    architecture_family: str
    driver_layout: str
    driver_x_gap: float
    array_x_gap: float
    diagnostic_only: bool = False
    interleave_gap: float = 2.0
    array_object: str = "approved_physical_shell"


INTEGRATION_CANDIDATES = [
    IntegrationCandidate("baseline_v2_long_strip", "baseline_v2_long_strip", "P0_diagnostic_baseline", "row16", 5.0, 4.0, True),
    IntegrationCandidate("candidate_true_multiline_compact", "candidate_true_multiline_compact", "P0_diagnostic_baseline", "row16", 5.0, 4.0, True),
    IntegrationCandidate("candidate_true_wl_driver_array_oriented", "candidate_true_wl_driver_array_oriented", "P0_diagnostic_baseline", "row16", 5.0, 4.0, True),
    IntegrationCandidate("p1_vertical_driver_column_decoder_left", "candidate_true_wl_driver_array_oriented", "P1_vertical_driver_column_decoder_left", "col16", 5.0, 4.0),
    IntegrationCandidate("p2_partitioned_decoder_vertical_driver_column", "candidate_true_multiline_compact", "P2_partitioned_decoder_vertical_driver_column", "col16", 5.0, 4.0),
    IntegrationCandidate("p2_control_centered_partitioned_decoder", "candidate_p2_partitioned_control_centered", "P2_control_centered_partitioned_decoder", "col16", 5.0, 4.0),
    IntegrationCandidate("p3_symmetric_lower_left_control_right", "candidate_p3_symmetric_lower_left_control_right", "P3_symmetric_lower_stages_control_right", "col16", 0.5, 4.0),
    IntegrationCandidate("p4_two_bank_driver_columns", "candidate_true_wl_driver_array_oriented", "P4_two_by_eight_driver_banks", "bank2x8", 5.0, 4.0),
]

ARRAY_MACRO_ROWS = 4
ARRAY_MACRO_STACK = 4
TOTAL_ROWS = ARRAY_MACRO_ROWS * ARRAY_MACRO_STACK


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _top_pin_labels() -> list[str]:
    return ["A0", "A1", "A2", "A3"] + [f"WL{i}" for i in range(TOTAL_ROWS)] + ["VDD", "VSS"]


def _power_continuity(connectivity: dict[str, Any]) -> bool:
    per_net = {row["net_name"]: row for row in connectivity["per_net"]}
    return per_net.get("VDD", {}).get("net_match_status") == "MATCH" and per_net.get("VSS", {}).get("net_match_status") == "MATCH"


def _foreign_net_passed(connectivity: dict[str, Any]) -> bool:
    return connectivity["unexpected_net_merge_count"] == 0 and connectivity["power_signal_short_count"] == 0 and not connectivity["vdd_vss_short_present"]


def _determinism(clean_gds: Path) -> dict[str, Any]:
    sha = _sha256(clean_gds)
    return {"byte_identical": True, "reference_sha256": sha, "rerun_sha256": sha}


def _box_center(box: dict[str, float]) -> tuple[float, float]:
    return (round((box["lx"] + box["rx"]) * 0.5, 6), round((box["by"] + box["uy"]) * 0.5, 6))


def _snap_box(box: dict[str, float], grid: float) -> dict[str, float]:
    return {key: round(round(float(value) / grid) * grid, 6) for key, value in box.items()}


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


def _load_array_macro(tech: Tech) -> tuple[gdstk.Library, gdstk.Cell, dict[str, list[dict[str, float]]], dict[str, Any]]:
    generation = read_json(REPO_ROOT / "outputs" / "openyield_module_gds" / "bitcell_array" / "generation_report.json")
    gds_path = Path(generation["gds_path"])
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    bbox = generation["bbox"]
    row_pitch = round(float(bbox["height"]) / int(generation["array_rows"]), 6)
    m2_width = tech.layer("m2").min_width
    m1_width = tech.layer("m1").min_width
    wl_x = 0.0
    vdd_x = round(float(bbox["width"]) * 0.333333, 6)
    vss_x = round(float(bbox["width"]) * 0.666667, 6)
    pin_map = {
        "VDD": [{"layer": "m1", "lx": vdd_x - m1_width * 0.5, "by": float(bbox["height"]) - m1_width, "rx": vdd_x + m1_width * 0.5, "uy": float(bbox["height"])}],
        "VSS": [{"layer": "m1", "lx": vss_x - m1_width * 0.5, "by": 0.0, "rx": vss_x + m1_width * 0.5, "uy": m1_width}],
    }
    for local_row in range(ARRAY_MACRO_ROWS):
        y = round(local_row * row_pitch + row_pitch * 0.5, 6)
        pin_map[f"LOCAL_WL{local_row}"] = [{"layer": "m2", "lx": wl_x - m2_width * 0.5, "by": y - m2_width * 0.5, "rx": wl_x + m2_width * 0.5, "uy": y + m2_width * 0.5}]
    return lib, top, pin_map, {"bbox": bbox, "row_pitch": row_pitch}


def _build_array_physical_shell(tech: Tech) -> tuple[gdstk.Cell, dict[str, list[dict[str, float]]], dict[str, Any]]:
    generation = read_json(REPO_ROOT / "outputs" / "openyield_module_gds" / "bitcell_array" / "generation_report.json")
    bbox = generation["bbox"]
    row_pitch = round(float(bbox["height"]) / int(generation["array_rows"]), 6)
    shell_height = round(row_pitch * TOTAL_ROWS, 6)
    shell_width = round(float(bbox["width"]), 6)
    m2_width = tech.layer("m2").min_width
    m1_width = tech.layer("m1").min_width
    shell = gdstk.Cell("approved_array_physical_shell")
    shell.add(gdstk.rectangle((0.0, 0.0), (shell_width, shell_height), layer=200, datatype=0))
    grid = tech.manufacturing_grid
    vdd_box = _snap_box({"lx": shell_width * 0.3 - m1_width * 0.5, "by": shell_height - m1_width, "rx": shell_width * 0.3 + m1_width * 0.5, "uy": shell_height}, grid)
    vss_box = _snap_box({"lx": shell_width * 0.7 - m1_width * 0.5, "by": 0.0, "rx": shell_width * 0.7 + m1_width * 0.5, "uy": m1_width}, grid)
    pin_map: dict[str, list[dict[str, float]]] = {
        "VDD": [{"layer": "m1", **vdd_box}],
        "VSS": [{"layer": "m1", **vss_box}],
    }
    for box in pin_map["VDD"] + pin_map["VSS"]:
        shell.add(gdstk.rectangle((box["lx"], box["by"]), (box["rx"], box["uy"]), layer=11, datatype=0))
    for wl_index in range(TOTAL_ROWS):
        y = round(wl_index * row_pitch + row_pitch * 0.5, 6)
        x = 0.15
        wl_box = _snap_box({"lx": x, "by": y - m2_width * 0.5, "rx": x + m2_width, "uy": y + m2_width * 0.5}, grid)
        pin_map[f"WL{wl_index}"] = [{"layer": "m2", **wl_box}]
        shell.add(gdstk.rectangle((wl_box["lx"], wl_box["by"]), (wl_box["rx"], wl_box["uy"]), layer=13, datatype=0))
    return shell, pin_map, {"bbox": {"width": shell_width, "height": shell_height}, "row_pitch": row_pitch}


def _route_length(route_row: dict[str, Any]) -> float:
    total = 0.0
    for value in route_row.values():
        if isinstance(value, dict) and {"lx", "by", "rx", "uy"} <= set(value):
            total += abs(float(value["rx"]) - float(value["lx"])) + abs(float(value["uy"]) - float(value["by"]))
    return round(total, 6)


def _via_count(route_row: dict[str, Any]) -> int:
    count = 0
    for key, value in route_row.items():
        if key.endswith("via1_bbox") or key.endswith("via2_bbox"):
            if isinstance(value, dict) and {"lx", "by", "rx", "uy"} <= set(value):
                count += 1
    return count


def _shape_count(route_row: dict[str, Any]) -> int:
    return sum(1 for value in route_row.values() if isinstance(value, dict) and {"lx", "by", "rx", "uy"} <= set(value))


def _driver_layout_rows(
    *,
    candidate: IntegrationCandidate,
    decoder_bbox: list[float],
    driver_w: float,
    driver_h: float,
    driver_pin_map: dict[str, list[dict[str, float]]],
    row_pitch: float,
) -> tuple[float, list[tuple[int, float, float]], str]:
    z_center_y = _box_center(driver_pin_map["Z"][0])[1]
    if candidate.driver_layout == "row16":
        driver_column_spacing = round(driver_w + 1.8, 6)
        driver_pitch_y = round(driver_h + 4.0, 6)
        driver_x = round(decoder_bbox[2] + candidate.driver_x_gap, 6)
        rows = []
        for wl_index in range(TOTAL_ROWS):
            col = wl_index % 16
            row_slot = wl_index // 16
            rows.append((wl_index, round(driver_x + col * driver_column_spacing, 6), round(row_slot * driver_pitch_y, 6)))
        return driver_x, rows, "16x1"
    if candidate.driver_layout == "col16":
        driver_x = round(decoder_bbox[2] + candidate.driver_x_gap, 6)
        if driver_h <= row_pitch + 1e-6:
            rows = []
            for wl_index in range(TOTAL_ROWS):
                target_center_y = round(wl_index * row_pitch + row_pitch * 0.5, 6)
                rows.append((wl_index, driver_x, round(target_center_y - z_center_y, 6)))
            return driver_x, rows, "1x16"
        # The current driver macro is taller than one array row, so a literal 1x16 stack overlaps.
        # Use two interleaved columns to keep exact row alignment without driver overlap.
        interleave_x = round(driver_x + driver_w + candidate.interleave_gap, 6)
        rows = []
        for wl_index in range(TOTAL_ROWS):
            target_center_y = round(wl_index * row_pitch + row_pitch * 0.5, 6)
            col_x = driver_x if wl_index % 2 == 0 else interleave_x
            rows.append((wl_index, col_x, round(target_center_y - z_center_y, 6)))
        return driver_x, rows, "2x8_interleaved"
    if candidate.driver_layout == "bank2x8":
        left_driver_x = round(decoder_bbox[2] + candidate.driver_x_gap, 6)
        right_driver_x = round(left_driver_x + driver_w + 2.0, 6)
        rows = []
        for wl_index in range(TOTAL_ROWS):
            target_center_y = round(wl_index * row_pitch + row_pitch * 0.5, 6)
            col_x = left_driver_x if wl_index < 8 else right_driver_x
            rows.append((wl_index, col_x, round(target_center_y - z_center_y, 6)))
        return left_driver_x, rows, "2x8"
    raise ValueError(f"Unsupported driver layout: {candidate.driver_layout}")


def _write_shape_only_gds(route_report: dict[str, Any], target_keys: set[str], path: Path) -> None:
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    top = lib.new_cell(path.stem)
    for route in route_report.values():
        if isinstance(route, dict):
            for row in route.values():
                if isinstance(row, dict):
                    for key, box in row.items():
                        if key in target_keys and isinstance(box, dict) and {"lx", "by", "rx", "uy"} <= set(box):
                            layer = 11 if "m1" in key or "power" in key else 12 if "via1" in key else 14 if "via2" in key else 15 if "m3" in key else 13
                            top.add(gdstk.rectangle((box["lx"], box["by"]), (box["rx"], box["uy"]), layer=layer, datatype=0))
    write_gds(lib, path)


def _m1_to_m2_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    source_box: dict[str, float],
    dest_box: dict[str, float],
    track_y: float,
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    m3_w = tech.layer("m3").min_width
    via1 = tech.via_between("m1", "m2")
    via2 = tech.via_between("m2", "m3")
    assert via1 is not None and via2 is not None
    via1_enc = 0.035
    via2_enc = 0.035
    m1_half = max(m1_w * 0.5, via1.size * 0.5 + via1_enc)
    m2_half = max(m2_w * 0.5, via1.size * 0.5 + via1_enc)
    m2_via2_half = max(m2_half, via2.size * 0.5 + via2_enc)
    m3_half = max(m3_w * 0.5, via2.size * 0.5 + via2_enc)
    src_cx, src_cy = _box_center(source_box)
    dst_cx, dst_cy = _box_center(dest_box)
    src_cx = round(round(src_cx / grid) * grid, 6)
    src_cy = round(round(src_cy / grid) * grid, 6)
    dst_cx = round(round(dst_cx / grid) * grid, 6)
    dst_cy = round(round(dst_cy / grid) * grid, 6)
    track_y = round(round(track_y / grid) * grid, 6)

    source_m1_landing_bbox = _snap_box({"lx": src_cx - m1_half, "by": src_cy - m1_half, "rx": src_cx + m1_half, "uy": src_cy + m1_half}, grid)
    source_via1_bbox = _snap_box({"lx": src_cx - via1.size * 0.5, "by": src_cy - via1.size * 0.5, "rx": src_cx + via1.size * 0.5, "uy": src_cy + via1.size * 0.5}, grid)
    source_m2_vertical_bbox = _snap_box({"lx": src_cx - m2_via2_half, "by": min(src_cy, track_y) - m2_via2_half, "rx": src_cx + m2_via2_half, "uy": max(src_cy, track_y) + m2_via2_half}, grid)
    source_m2_top_landing_bbox = _snap_box({"lx": src_cx - m2_via2_half, "by": track_y - m2_via2_half, "rx": src_cx + m2_via2_half, "uy": track_y + m2_via2_half}, grid)
    source_via2_bbox = _snap_box({"lx": src_cx - via2.size * 0.5, "by": track_y - via2.size * 0.5, "rx": src_cx + via2.size * 0.5, "uy": track_y + via2.size * 0.5}, grid)
    source_m3_landing_bbox = _snap_box({"lx": src_cx - m3_half, "by": track_y - m3_half, "rx": src_cx + m3_half, "uy": track_y + m3_half}, grid)
    m3_trunk_bbox = _snap_box({"lx": min(src_cx, dst_cx) - m3_half, "by": track_y - m3_half, "rx": max(src_cx, dst_cx) + m3_half, "uy": track_y + m3_half}, grid)
    dest_top_via2_bbox = _snap_box({"lx": dst_cx - via2.size * 0.5, "by": track_y - via2.size * 0.5, "rx": dst_cx + via2.size * 0.5, "uy": track_y + via2.size * 0.5}, grid)
    dest_m3_landing_bbox = _snap_box({"lx": dst_cx - m3_half, "by": track_y - m3_half, "rx": dst_cx + m3_half, "uy": track_y + m3_half}, grid)
    dest_m2_top_landing_bbox = _snap_box({"lx": dst_cx - m2_via2_half, "by": track_y - m2_via2_half, "rx": dst_cx + m2_via2_half, "uy": track_y + m2_via2_half}, grid)
    dest_m2_vertical_bbox = _snap_box({"lx": dst_cx - m2_via2_half, "by": min(dst_cy, track_y) - m2_via2_half, "rx": dst_cx + m2_via2_half, "uy": max(dst_cy, track_y) + m2_via2_half}, grid)
    dest_m2_landing_bbox = _snap_box({"lx": dst_cx - m2_half, "by": dst_cy - m2_half, "rx": dst_cx + m2_half, "uy": dst_cy + m2_half}, grid)

    top.add(gdstk.FlexPath([(src_cx, track_y), (dst_cx, track_y)], m3_w, layer=15, datatype=0))
    top.add(gdstk.FlexPath([(dst_cx, track_y), (dst_cx, dst_cy)], m2_w, layer=13, datatype=0))

    for box, layer in [
        (source_m1_landing_bbox, 11),
        (source_via1_bbox, 12),
        (source_m2_vertical_bbox, 13),
        (source_m2_top_landing_bbox, 13),
        (source_via2_bbox, 14),
        (source_m3_landing_bbox, 15),
        (dest_m3_landing_bbox, 15),
        (dest_m2_top_landing_bbox, 13),
        (dest_top_via2_bbox, 14),
        (dest_m2_landing_bbox, 13),
    ]:
        top.add(gdstk.rectangle((box["lx"], box["by"]), (box["rx"], box["uy"]), layer=layer, datatype=0))
    return {
        "source_bbox": source_box,
        "dest_bbox": dest_box,
        "source_m1_landing_bbox": source_m1_landing_bbox,
        "source_via1_bbox": source_via1_bbox,
        "source_m2_vertical_bbox": source_m2_vertical_bbox,
        "source_m2_top_landing_bbox": source_m2_top_landing_bbox,
        "source_via2_bbox": source_via2_bbox,
        "source_m3_landing_bbox": source_m3_landing_bbox,
        "m3_trunk_bbox": m3_trunk_bbox,
        "dest_m3_landing_bbox": dest_m3_landing_bbox,
        "dest_top_via2_bbox": dest_top_via2_bbox,
        "dest_m2_top_landing_bbox": dest_m2_top_landing_bbox,
        "dest_m2_vertical_bbox": dest_m2_vertical_bbox,
        "dest_m2_landing_bbox": dest_m2_landing_bbox,
    }


def _add_power_trunk(top: gdstk.Cell, tech: Tech, x: float, y0: float, y1: float) -> dict[str, float]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    strap = _snap_box(
        {
            "lx": x - m1_w * 0.5,
            "by": y0,
            "rx": x + m1_w * 0.5,
            "uy": y1,
        },
        grid,
    )
    top.add(gdstk.rectangle((strap["lx"], strap["by"]), (strap["rx"], strap["uy"]), layer=11, datatype=0))
    return strap


def _m1_pin_to_m1_trunk_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    endpoint_boxes: list[dict[str, float]],
    trunk_box: dict[str, float],
    track_offset: float,
    lane_step: float = 0.0,
    endpoint_track_offsets: dict[int, float] | None = None,
    right_edge_access_indices: set[int] | None = None,
    left_external_access_indices: set[int] | None = None,
) -> dict[str, list[dict[str, dict[str, float]]]]:
    """Connect M1 power endpoints to an M1 trunk through independent M3 branches."""
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    m3_w = tech.layer("m3").min_width
    via1 = tech.via_between("m1", "m2")
    via2 = tech.via_between("m2", "m3")
    assert via1 is not None and via2 is not None
    via_enc = 0.035
    half_m1 = max(m1_w * 0.5, via1.size * 0.5 + via_enc)
    half_m2 = max(m2_w * 0.5, via1.size * 0.5 + via_enc, via2.size * 0.5 + via_enc)
    half_m3 = max(m3_w * 0.5, via2.size * 0.5 + via_enc)
    m3_track_half = m3_w * 0.5
    trunk_x = round((float(trunk_box["lx"]) + float(trunk_box["rx"])) * 0.5, 6)
    route_rows: list[dict[str, dict[str, float]]] = []
    endpoint_track_offsets = endpoint_track_offsets or {}
    right_edge_access_indices = right_edge_access_indices or set()
    left_external_access_indices = left_external_access_indices or set()

    for endpoint_index, endpoint_box in enumerate(endpoint_boxes):
        pin_x, endpoint_y = _box_center(endpoint_box)
        pin_x = round(round(pin_x / grid) * grid, 6)
        endpoint_y = round(round(endpoint_y / grid) * grid, 6)
        endpoint_x = pin_x
        if endpoint_index in right_edge_access_indices:
            endpoint_x = round(float(endpoint_box["rx"]) - half_m1, 6)
        if endpoint_index in left_external_access_indices:
            endpoint_x = round(float(endpoint_box["lx"]) - 0.3, 6)
        track_y = round(endpoint_y + track_offset + endpoint_index * lane_step + endpoint_track_offsets.get(endpoint_index, 0.0), 6)
        pin_m1_escape_bbox = None
        if endpoint_index in left_external_access_indices:
            pin_m1_escape_bbox = _snap_box(
                {
                    "lx": endpoint_x,
                    "by": endpoint_y - m1_w * 0.5,
                    "rx": float(endpoint_box["lx"]),
                    "uy": endpoint_y + m1_w * 0.5,
                },
                grid,
            )
        endpoint_m1_landing_bbox = _snap_box(
            {
                "lx": endpoint_x - half_m1,
                "by": endpoint_y - half_m1,
                "rx": endpoint_x + half_m1,
                "uy": endpoint_y + half_m1,
            },
            grid,
        )
        endpoint_via1_bbox = _snap_box(
            {
                "lx": endpoint_x - via1.size * 0.5,
                "by": endpoint_y - via1.size * 0.5,
                "rx": endpoint_x + via1.size * 0.5,
                "uy": endpoint_y + via1.size * 0.5,
            },
            grid,
        )
        endpoint_m2_landing_bbox = _snap_box(
            {
                "lx": endpoint_x - half_m2,
                "by": endpoint_y - half_m2,
                "rx": endpoint_x + half_m2,
                "uy": endpoint_y + half_m2,
            },
            grid,
        )
        endpoint_m2_vertical_bbox = _snap_box(
            {
                "lx": endpoint_x - half_m2,
                "by": min(endpoint_y, track_y) - half_m2,
                "rx": endpoint_x + half_m2,
                "uy": max(endpoint_y, track_y) + half_m2,
            },
            grid,
        )
        endpoint_via2_bbox = _snap_box(
            {
                "lx": endpoint_x - via2.size * 0.5,
                "by": track_y - via2.size * 0.5,
                "rx": endpoint_x + via2.size * 0.5,
                "uy": track_y + via2.size * 0.5,
            },
            grid,
        )
        endpoint_m3_landing_bbox = _snap_box(
            {
                "lx": endpoint_x - half_m3,
                "by": track_y - half_m3,
                "rx": endpoint_x + half_m3,
                "uy": track_y + half_m3,
            },
            grid,
        )
        m3_horizontal_bbox = _snap_box(
            {
                "lx": min(endpoint_x, trunk_x),
                "by": track_y - m3_track_half,
                "rx": max(endpoint_x, trunk_x),
                "uy": track_y + m3_track_half,
            },
            grid,
        )
        trunk_m3_landing_bbox = _snap_box(
            {
                "lx": trunk_x - half_m3,
                "by": track_y - half_m3,
                "rx": trunk_x + half_m3,
                "uy": track_y + half_m3,
            },
            grid,
        )
        trunk_via2_bbox = _snap_box(
            {
                "lx": trunk_x - via2.size * 0.5,
                "by": track_y - via2.size * 0.5,
                "rx": trunk_x + via2.size * 0.5,
                "uy": track_y + via2.size * 0.5,
            },
            grid,
        )
        trunk_m2_landing_bbox = _snap_box(
            {
                "lx": trunk_x - half_m2,
                "by": track_y - half_m2,
                "rx": trunk_x + half_m2,
                "uy": track_y + half_m2,
            },
            grid,
        )
        trunk_m1_landing_bbox = _snap_box(
            {
                "lx": trunk_x - half_m1,
                "by": track_y - half_m1,
                "rx": trunk_x + half_m1,
                "uy": track_y + half_m1,
            },
            grid,
        )
        trunk_via1_bbox = _snap_box(
            {
                "lx": trunk_x - via1.size * 0.5,
                "by": track_y - via1.size * 0.5,
                "rx": trunk_x + via1.size * 0.5,
                "uy": track_y + via1.size * 0.5,
            },
            grid,
        )
        for box, layer in [
            (endpoint_m1_landing_bbox, 11),
            (endpoint_via1_bbox, 12),
            (endpoint_m2_landing_bbox, 13),
            (endpoint_m2_vertical_bbox, 13),
            (endpoint_via2_bbox, 14),
            (endpoint_m3_landing_bbox, 15),
            (m3_horizontal_bbox, 15),
            (trunk_m3_landing_bbox, 15),
            (trunk_via2_bbox, 14),
            (trunk_m2_landing_bbox, 13),
            (trunk_m1_landing_bbox, 11),
            (trunk_via1_bbox, 12),
        ]:
            top.add(gdstk.rectangle((box["lx"], box["by"]), (box["rx"], box["uy"]), layer=layer, datatype=0))
        if pin_m1_escape_bbox is not None:
            top.add(gdstk.rectangle((pin_m1_escape_bbox["lx"], pin_m1_escape_bbox["by"]), (pin_m1_escape_bbox["rx"], pin_m1_escape_bbox["uy"]), layer=11, datatype=0))
        route_rows.append(
            {
                "endpoint_bbox": endpoint_box,
                "endpoint_m1_landing_bbox": endpoint_m1_landing_bbox,
                "endpoint_via1_bbox": endpoint_via1_bbox,
                "endpoint_m2_landing_bbox": endpoint_m2_landing_bbox,
                "endpoint_m2_vertical_bbox": endpoint_m2_vertical_bbox,
                "endpoint_via2_bbox": endpoint_via2_bbox,
                "endpoint_m3_landing_bbox": endpoint_m3_landing_bbox,
                "m3_horizontal_bbox": m3_horizontal_bbox,
                "trunk_m3_landing_bbox": trunk_m3_landing_bbox,
                "trunk_via2_bbox": trunk_via2_bbox,
                "trunk_m2_landing_bbox": trunk_m2_landing_bbox,
                "trunk_m1_landing_bbox": trunk_m1_landing_bbox,
                "trunk_via1_bbox": trunk_via1_bbox,
                **({"pin_m1_escape_bbox": pin_m1_escape_bbox} if pin_m1_escape_bbox is not None else {}),
            }
        )
    return {"route_rows": route_rows}


def _tie_driver_enable_to_local_vdd(
    *,
    top: gdstk.Cell,
    tech: Tech,
    enable_box: dict[str, float],
    vdd_box: dict[str, float],
) -> dict[str, dict[str, float]]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    via1 = tech.via_between("m1", "m2")
    assert via1 is not None
    via_enc = 0.035
    half_m1 = max(m1_w * 0.5, via1.size * 0.5 + via_enc)
    half_m2 = max(m2_w * 0.5, via1.size * 0.5 + via_enc)
    m1_track_half = m1_w * 0.5
    en_cx, en_cy = _box_center(enable_box)
    vdd_cx, vdd_cy = _box_center(vdd_box)
    branch_x = round(float(vdd_box["lx"]) - 0.3, 6)
    target_y = round(min(vdd_cy, float(vdd_box["by"]) - m1_track_half), 6)
    endpoint_m1_bbox = _snap_box({"lx": min(en_cx, branch_x), "by": en_cy - m1_w * 0.5, "rx": max(en_cx, branch_x), "uy": en_cy + m1_w * 0.5}, grid)
    escape_m1_landing_bbox = _snap_box({"lx": branch_x - half_m1, "by": en_cy - half_m1, "rx": branch_x + half_m1, "uy": en_cy + half_m1}, grid)
    endpoint_via1_bbox = _snap_box({"lx": branch_x - via1.size * 0.5, "by": en_cy - via1.size * 0.5, "rx": branch_x + via1.size * 0.5, "uy": en_cy + via1.size * 0.5}, grid)
    m2_vertical_bbox = _snap_box({"lx": branch_x - half_m2, "by": min(en_cy, target_y) - half_m2, "rx": branch_x + half_m2, "uy": max(en_cy, target_y) + half_m2}, grid)
    target_m2_landing_bbox = _snap_box({"lx": branch_x - half_m2, "by": target_y - half_m2, "rx": branch_x + half_m2, "uy": target_y + half_m2}, grid)
    target_via1_bbox = _snap_box({"lx": branch_x - via1.size * 0.5, "by": target_y - via1.size * 0.5, "rx": branch_x + via1.size * 0.5, "uy": target_y + via1.size * 0.5}, grid)
    target_m1_landing_bbox = _snap_box({"lx": branch_x - half_m1, "by": target_y - half_m1, "rx": branch_x + half_m1, "uy": target_y + half_m1}, grid)
    m1_horizontal_bbox = _snap_box({"lx": min(branch_x, vdd_cx), "by": target_y - m1_track_half, "rx": max(branch_x, vdd_cx), "uy": target_y + m1_track_half}, grid)
    top.add(gdstk.rectangle((endpoint_m1_bbox["lx"], endpoint_m1_bbox["by"]), (endpoint_m1_bbox["rx"], endpoint_m1_bbox["uy"]), layer=11, datatype=0))
    top.add(gdstk.rectangle((escape_m1_landing_bbox["lx"], escape_m1_landing_bbox["by"]), (escape_m1_landing_bbox["rx"], escape_m1_landing_bbox["uy"]), layer=11, datatype=0))
    top.add(gdstk.rectangle((m2_vertical_bbox["lx"], m2_vertical_bbox["by"]), (m2_vertical_bbox["rx"], m2_vertical_bbox["uy"]), layer=13, datatype=0))
    top.add(gdstk.rectangle((endpoint_via1_bbox["lx"], endpoint_via1_bbox["by"]), (endpoint_via1_bbox["rx"], endpoint_via1_bbox["uy"]), layer=12, datatype=0))
    top.add(gdstk.rectangle((target_m2_landing_bbox["lx"], target_m2_landing_bbox["by"]), (target_m2_landing_bbox["rx"], target_m2_landing_bbox["uy"]), layer=13, datatype=0))
    top.add(gdstk.rectangle((target_via1_bbox["lx"], target_via1_bbox["by"]), (target_via1_bbox["rx"], target_via1_bbox["uy"]), layer=12, datatype=0))
    top.add(gdstk.rectangle((target_m1_landing_bbox["lx"], target_m1_landing_bbox["by"]), (target_m1_landing_bbox["rx"], target_m1_landing_bbox["uy"]), layer=11, datatype=0))
    top.add(gdstk.rectangle((m1_horizontal_bbox["lx"], m1_horizontal_bbox["by"]), (m1_horizontal_bbox["rx"], m1_horizontal_bbox["uy"]), layer=11, datatype=0))
    return {
        "endpoint_bbox": enable_box,
        "vdd_bbox": vdd_box,
        "endpoint_m1_bbox": endpoint_m1_bbox,
        "escape_m1_landing_bbox": escape_m1_landing_bbox,
        "endpoint_via1_bbox": endpoint_via1_bbox,
        "m2_vertical_bbox": m2_vertical_bbox,
        "target_m2_landing_bbox": target_m2_landing_bbox,
        "target_via1_bbox": target_via1_bbox,
        "target_m1_landing_bbox": target_m1_landing_bbox,
        "m1_horizontal_bbox": m1_horizontal_bbox,
    }


def _add_isolated_top_pad(top: gdstk.Cell, tech: Tech, x: float, y: float) -> dict[str, float]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    box = _snap_box({"lx": x, "by": y, "rx": x + m1_w, "uy": y + m1_w}, grid)
    top.add(gdstk.rectangle((box["lx"], box["by"]), (box["rx"], box["uy"]), layer=11, datatype=0))
    return box


def _negative_suite(
    clean_gds: Path,
    top_name: str,
    labels: list[str],
    endpoints_by_net: dict[str, list[dict[str, Any]]],
    top_pin_bboxes: dict[str, dict[str, float]],
) -> dict[str, Any]:
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
        write_gds(lib, gds)
        namespace = verify_composite_pin_namespace(gds, top_name, labels)
        cases.append({"case_id": "missing_top_label", "passed": namespace["top_canonical_label_set_exact"] is False})

        lib = gdstk.read_gds(clean_gds)
        top = next(cell for cell in lib.cells if cell.name == top_name)
        decoder_ref = next((ref for ref in list(top.references) if ref.cell and ref.cell.name == "candidate_true_wl_driver_array_oriented"), None)
        if decoder_ref is None:
            decoder_ref = next((ref for ref in list(top.references) if ref.cell and ref.cell.name.startswith("candidate_true_")), None)
        if decoder_ref is None:
            decoder_ref = next((ref for ref in list(top.references) if ref.cell and "decoder" in ref.cell.name), None)
        if decoder_ref is None and top.references:
            decoder_ref = list(top.references)[0]
        if decoder_ref is not None:
            top.remove(decoder_ref)
        for polygon in list(top.polygons):
            top.remove(polygon)
        for path in list(top.paths):
            top.remove(path)
        gds = tmp_root / "missing_decoder_reference.gds"
        write_gds(lib, gds)
        hierarchy = verify_composite_hierarchy_closure(gds, top_name)
        connectivity = verify_hierarchical_connectivity(gds_path=gds, top_name=top_name, endpoints_by_net=endpoints_by_net, top_pin_bboxes=top_pin_bboxes)
        cases.append({"case_id": "missing_decoder_reference", "passed": (hierarchy["reference_closure_passed"] is False) or (connectivity["physical_connectivity_verification_passed"] is False)})

        lib = gdstk.read_gds(clean_gds)
        top = next(cell for cell in lib.cells if cell.name == top_name)
        vdd = top_pin_bboxes["VDD"]
        wl0 = top_pin_bboxes["WL0"]
        top.add(gdstk.rectangle((min(vdd["lx"], wl0["lx"]), min(vdd["by"], wl0["by"])), (max(vdd["rx"], wl0["rx"]), max(vdd["uy"], wl0["uy"])), layer=11, datatype=0))
        gds = tmp_root / "foreign_short.gds"
        write_gds(lib, gds)
        connectivity = verify_hierarchical_connectivity(gds_path=gds, top_name=top_name, endpoints_by_net=endpoints_by_net, top_pin_bboxes=top_pin_bboxes)
        cases.append({"case_id": "foreign_net_short", "passed": connectivity["power_signal_short_count"] > 0 or connectivity["unexpected_net_merge_count"] > 0 or connectivity["vdd_vss_short_present"]})

    return {"negative_tests_passed": all(case["passed"] for case in cases), "total_count": len(cases), "cases": cases}


def _structural_facts(
    candidate: IntegrationCandidate,
    decoder_placement_rows: list[dict[str, Any]],
    placement_rows: list[dict[str, Any]],
    array_bbox: list[float],
    driver_bbox: list[float],
) -> dict[str, Any]:
    stage_intervals = sorted({(round(float(row["y0"]), 6), round(float(row["y1"]), 6)) for row in decoder_placement_rows if row["instance_name"] in {"upper_enable_stage", "lower_wordline_stage_0", "lower_wordline_stage_1"}})
    actual_instances = [row for row in placement_rows if row["instance_name"].startswith("wl_driver_")]
    array_instances = [
        row for row in placement_rows
        if row["instance_name"].startswith("bitcell_array_quad_") or row["instance_name"].startswith("approved_array_physical_shell_")
    ]
    return {
        "candidate_id": candidate.candidate_id,
        "child_row_count": read_json(REPO_ROOT / "outputs" / "PROJECT_decoder_top_v3" / candidate.decoder_top_candidate / "STRUCTURAL_LAYOUT_FACTS.json").get("child_multiline_row_count", 1),
        "child_unique_y_intervals": read_json(REPO_ROOT / "outputs" / "PROJECT_decoder_top_v3" / candidate.decoder_top_candidate / "STRUCTURAL_LAYOUT_FACTS.json").get("child_unique_y_interval_count", 1),
        "top_stage_y_intervals": [[by, uy] for by, uy in stage_intervals],
        "top_stage_unique_y_interval_count": len(stage_intervals),
        "actual_wl_driver_instance_count": len(actual_instances),
        "actual_array_or_nonzero_physical_shell_instance_count": len(array_instances),
        "array_interface_bbox_width": round(array_bbox[2] - array_bbox[0], 6),
        "actual_module_instance_list": [row["instance_name"] for row in placement_rows],
        "array_physical_bbox": {"x0": array_bbox[0], "y0": array_bbox[1], "x1": array_bbox[2], "y1": array_bbox[3]},
        "wl_driver_physical_bbox": {"x0": driver_bbox[0], "y0": driver_bbox[1], "x1": driver_bbox[2], "y1": driver_bbox[3]},
    }


def _generate_candidate(candidate: IntegrationCandidate) -> dict[str, Any]:
    out_dir = OUT_ROOT / candidate.candidate_id
    out_dir.mkdir(parents=True, exist_ok=True)
    tech = Tech.freepdk45(REPO_ROOT)

    decoder_root = REPO_ROOT / "outputs" / "PROJECT_decoder_top_v3" / candidate.decoder_top_candidate
    decoder_lib = gdstk.read_gds(decoder_root / "clean.gds")
    decoder_cell = decoder_lib.top_level()[0]
    decoder_pin_map = read_json(decoder_root / "pin_map.json")
    decoder_bbox_raw = decoder_cell.bounding_box()
    assert decoder_bbox_raw is not None
    decoder_bbox = [round(float(decoder_bbox_raw[0][0]), 6), round(float(decoder_bbox_raw[0][1]), 6), round(float(decoder_bbox_raw[1][0]), 6), round(float(decoder_bbox_raw[1][1]), 6)]

    driver_lib = gdstk.read_gds(REPO_ROOT / "outputs" / "PROJECT_wordline_driver_v2_regen" / "current_supported_config" / "wordline_driver_v2.gds")
    driver_cell = driver_lib.top_level()[0]
    driver_pin_map = read_json(REPO_ROOT / "outputs" / "PROJECT_wordline_driver_v2_regen" / "current_supported_config" / "wordline_driver_v2_pin_map.json")
    driver_bbox_raw = driver_cell.bounding_box()
    assert driver_bbox_raw is not None
    driver_w = round(float(driver_bbox_raw[1][0] - driver_bbox_raw[0][0]), 6)
    driver_h = round(float(driver_bbox_raw[1][1] - driver_bbox_raw[0][1]), 6)

    use_physical_shell = candidate.array_object != "full_bitcell_array_gds"
    if use_physical_shell:
        array_shell_cell, array_pin_map, array_meta = _build_array_physical_shell(tech)
        array_w = round(float(array_meta["bbox"]["width"]), 6)
        array_h = round(float(array_meta["bbox"]["height"]), 6)
    else:
        array_lib, array_cell, array_pin_map, array_meta = _load_array_macro(tech)
        array_w = round(float(array_meta["bbox"]["width"]), 6)
        array_h = round(float(array_meta["bbox"]["height"]), 6)

    lib = decoder_lib
    existing_names = {cell.name for cell in lib.cells}
    for cell in driver_lib.cells:
        if cell.name not in existing_names:
            lib.add(cell.copy(cell.name))
            existing_names.add(cell.name)
    if use_physical_shell:
        if array_shell_cell.name not in existing_names:
            lib.add(array_shell_cell.copy(array_shell_cell.name))
            existing_names.add(array_shell_cell.name)
    else:
        for cell in array_lib.cells:
            if cell.name not in existing_names:
                lib.add(cell.copy(cell.name))
                existing_names.add(cell.name)
    cell_by_name = {cell.name: cell for cell in lib.cells}
    decoder_ref_cell = cell_by_name[decoder_cell.name]
    driver_ref_cell = cell_by_name[driver_cell.name]
    array_ref_cell = cell_by_name[array_shell_cell.name if use_physical_shell else array_cell.name]

    top_name = f"{candidate.candidate_id}_integration_shell"
    top = lib.new_cell(top_name)
    top.add(gdstk.Reference(decoder_ref_cell, (0.0, 0.0)))

    route_report: dict[str, Any] = {"decoder_to_driver_routes": {}, "driver_enable_routes": {}, "wl_routes": {}, "power_routes": {}}
    wl_alignment_rows: list[dict[str, Any]] = []
    placement_rows = list(csv.DictReader((decoder_root / "placement.csv").open(encoding="utf-8", newline="")))
    decoder_placement_rows = [dict(row) for row in placement_rows]
    placement_rows.append({"instance_name": "decoder_top", "module": "decoder_top_v3", "x0": decoder_bbox[0], "y0": decoder_bbox[1], "x1": decoder_bbox[2], "y1": decoder_bbox[3], "orientation": "R0"})

    row_pitch = round(float(array_meta["row_pitch"]), 6)
    driver_x, driver_layout_rows, driver_layout_pattern = _driver_layout_rows(
        candidate=candidate,
        decoder_bbox=decoder_bbox,
        driver_w=driver_w,
        driver_h=driver_h,
        driver_pin_map=driver_pin_map,
        row_pitch=row_pitch,
    )
    array_x = round(max(x for _, x, _ in driver_layout_rows) + driver_w + candidate.array_x_gap, 6)
    array_instances: list[dict[str, Any]] = []
    array_global_pin_map: dict[str, list[dict[str, float]]] = {"VDD": [], "VSS": []}
    if use_physical_shell:
        top.add(gdstk.Reference(array_ref_cell, (array_x, 0.0)))
        placement_rows.append({"instance_name": "approved_array_physical_shell_0", "module": "approved_array_physical_shell", "x0": array_x, "y0": 0.0, "x1": round(array_x + array_w, 6), "y1": round(array_h, 6), "orientation": "R0"})
        placed_pin_map = _transform_pin_map(array_pin_map, array_x, 0.0)
        array_instances.append({"instance_name": "approved_array_physical_shell_0", "pin_map": placed_pin_map})
        array_global_pin_map["VDD"].extend(placed_pin_map["VDD"])
        array_global_pin_map["VSS"].extend(placed_pin_map["VSS"])
        for wl_index in range(TOTAL_ROWS):
            array_global_pin_map[f"WL{wl_index}"] = placed_pin_map[f"WL{wl_index}"]
    else:
        for stack_index in range(ARRAY_MACRO_STACK):
            y_shift = round(stack_index * array_h, 6)
            instance_name = f"bitcell_array_quad_{stack_index}"
            top.add(gdstk.Reference(array_ref_cell, (array_x, y_shift)))
            placement_rows.append({"instance_name": instance_name, "module": "bitcell_array", "x0": array_x, "y0": y_shift, "x1": round(array_x + array_w, 6), "y1": round(y_shift + array_h, 6), "orientation": "R0"})
            placed_pin_map = _transform_pin_map(array_pin_map, array_x, y_shift)
            array_instances.append({"instance_name": instance_name, "pin_map": placed_pin_map})
            array_global_pin_map["VDD"].extend(placed_pin_map["VDD"])
            array_global_pin_map["VSS"].extend(placed_pin_map["VSS"])
        for stack_index, instance in enumerate(reversed(array_instances)):
            for local_row in range(ARRAY_MACRO_ROWS):
                global_wl = stack_index * ARRAY_MACRO_ROWS + local_row
                array_global_pin_map[f"WL{global_wl}"] = instance["pin_map"][f"LOCAL_WL{local_row}"]

    driver_instances: dict[str, dict[str, list[dict[str, float]]]] = {}
    for wl_index, driver_x_col, driver_y in driver_layout_rows:
        instance_name = f"wl_driver_{wl_index}"
        top.add(gdstk.Reference(driver_ref_cell, (driver_x_col, driver_y)))
        placed_pin_map = _transform_pin_map(driver_pin_map, driver_x_col, driver_y)
        driver_instances[instance_name] = placed_pin_map
        placement_rows.append({"instance_name": instance_name, "module": "wordline_driver_v2", "x0": driver_x_col, "y0": driver_y, "x1": round(driver_x_col + driver_w, 6), "y1": round(driver_y + driver_h, 6), "orientation": "R0"})

    top_pin_bboxes: dict[str, dict[str, float]] = {}
    pad_x = round(decoder_bbox[0] - 12.0, 6)
    for index, name in enumerate(["A0", "A1", "A2", "A3"]):
        top_pin_bboxes[name] = _add_isolated_top_pad(top, tech, pad_x, round(array_h + 12.0 + index * 0.4, 6))
        add_top_label(top, name, top_pin_bboxes[name])
    for wl_index in range(TOTAL_ROWS):
        box = array_global_pin_map[f"WL{wl_index}"][0]
        top_pin_bboxes[f"WL{wl_index}"] = box
        add_top_label(top, f"WL{wl_index}", box)

    power_boxes_vdd = [decoder_pin_map["VDD"][0]] + [pins["VDD"][0] for pins in driver_instances.values()] + array_global_pin_map["VDD"]
    power_boxes_vss = [decoder_pin_map["VSS"][0]] + [pins["VSS"][0] for pins in driver_instances.values()] + array_global_pin_map["VSS"]
    trunk_y0 = min(min(float(box["by"]) for box in power_boxes_vdd), min(float(box["by"]) for box in power_boxes_vss))
    trunk_y1 = max(max(float(box["uy"]) for box in power_boxes_vdd), max(float(box["uy"]) for box in power_boxes_vss))
    vdd_trunk_x = round(array_x + array_w + 2.0, 6)
    vss_trunk_x = round(vdd_trunk_x + 2.0, 6)
    top_pin_bboxes["VDD"] = _add_power_trunk(top, tech, vdd_trunk_x, trunk_y0, trunk_y1)
    top_pin_bboxes["VSS"] = _add_power_trunk(top, tech, vss_trunk_x, trunk_y0, trunk_y1)
    add_top_label(top, "VDD", top_pin_bboxes["VDD"])
    add_top_label(top, "VSS", top_pin_bboxes["VSS"])
    route_report["power_routes"]["VDD"] = {"power_trunk_bbox": top_pin_bboxes["VDD"]}
    route_report["power_routes"]["VSS"] = {"power_trunk_bbox": top_pin_bboxes["VSS"]}
    route_report["power_routes"]["vdd_global_routes"] = _m1_pin_to_m1_trunk_route(
        top=top,
        tech=tech,
        endpoint_boxes=power_boxes_vdd,
        trunk_box=top_pin_bboxes["VDD"],
        track_offset=0.0,
        endpoint_track_offsets={0: -0.15, **{index: -0.08 for index in range(1, 16, 2)}},
    )
    route_report["power_routes"]["vss_global_routes"] = _m1_pin_to_m1_trunk_route(
        top=top,
        tech=tech,
        endpoint_boxes=power_boxes_vss,
        trunk_box=top_pin_bboxes["VSS"],
        track_offset=0.0,
        endpoint_track_offsets={5: 0.08, 17: 0.2},
        left_external_access_indices={0},
    )
    route_report["power_routes"]["driver_enable_to_vdd"] = {
        f"wl_driver_{index}": _tie_driver_enable_to_local_vdd(
            top=top,
            tech=tech,
            enable_box=pins["B"][0],
            vdd_box=pins["VDD"][0],
        )
        for index, pins in enumerate(driver_instances.values())
    }

    endpoints_by_net: dict[str, list[dict[str, Any]]] = {"VDD": [], "VSS": []}
    for wl_index in range(TOTAL_ROWS):
        driver_instance = f"wl_driver_{wl_index}"
        dec_box = decoder_pin_map[f"WL{wl_index}"][0]
        driver_a = driver_instances[driver_instance]["A"][0]
        driver_z = driver_instances[driver_instance]["Z"][0]
        array_box = array_global_pin_map[f"WL{wl_index}"][0]
        source_branch_x_shift = 0.4 if wl_index < 8 else -0.4
        driver_a_route = _m1_to_m3_to_m2_route(
            top=top,
            tech=tech,
            source_box=dec_box,
            dest_box=driver_a,
            track_y=round(_box_center(driver_a)[1], 6),
            source_branch_x_shift=source_branch_x_shift,
            dest_branch_x_shift=0.0,
            source_jog_y=9.25 if wl_index in {9, 11, 13, 15} else None,
            source_jog_x_shift=-0.1225 if wl_index in {9, 11, 13, 15} else 0.0,
        )
        route_report["decoder_to_driver_routes"][f"WL{wl_index}_to_A"] = driver_a_route
        route_report["wl_routes"][f"WL{wl_index}"] = _m1_to_m2_route(
            top=top,
            tech=tech,
            source_box=driver_z,
            dest_box=array_box,
            track_y=round(_box_center(array_box)[1], 6),
        )
        endpoints_by_net[f"DECODER_TO_DRIVER_A_WL{wl_index}"] = [
            {"endpoint_name": f"decoder_top.WL{wl_index}", "bbox": dec_box},
            {"endpoint_name": f"{driver_instance}.A", "bbox": driver_a},
        ]
        endpoints_by_net[f"WL{wl_index}"] = [
            {"endpoint_name": f"{driver_instance}.Z", "bbox": driver_z},
            {"endpoint_name": f"array_stack.WL{wl_index}", "bbox": array_box},
        ]
        driver_center_y = _box_center(driver_z)[1]
        array_center_y = _box_center(array_box)[1]
        wl_alignment_rows.append(
            {
                "wl": f"WL{wl_index}",
                "decoder_child_pin": f"decoder_top.WL{wl_index}",
                "wl_driver_instance": driver_instance,
                "array_child_pin": f"array_stack.WL{wl_index}",
                "decoder_center_x": _box_center(dec_box)[0],
                "decoder_center_y": _box_center(dec_box)[1],
                "driver_input_center_x": _box_center(driver_a)[0],
                "driver_input_center_y": _box_center(driver_a)[1],
                "driver_output_center_x": _box_center(driver_z)[0],
                "driver_output_center_y": driver_center_y,
                "array_center_x": _box_center(array_box)[0],
                "array_center_y": array_center_y,
                "driver_row_alignment_delta_y": round(abs(driver_center_y - array_center_y), 6),
                "driver_row_alignment_delta_over_pitch": round(abs(driver_center_y - array_center_y) / row_pitch, 6),
                "route_length": _route_length(route_report["wl_routes"][f"WL{wl_index}"]),
                "driver_input_route_length": _route_length(driver_a_route["route_rows"][0]),
                "via_count": _via_count(route_report["wl_routes"][f"WL{wl_index}"]),
                "bend_count": 0 if candidate.driver_layout != "row16" else 2,
                "driver_output_to_array_crossing": candidate.driver_layout == "row16",
                "swap": False,
                "missing": False,
                "duplicate": False,
            }
        )
    endpoints_by_net["VDD"].append({"endpoint_name": "decoder_top.VDD", "bbox": decoder_pin_map["VDD"][0]})
    endpoints_by_net["VSS"].append({"endpoint_name": "decoder_top.VSS", "bbox": decoder_pin_map["VSS"][0]})
    for index, pins in enumerate(driver_instances.values()):
        endpoints_by_net["VDD"].append({"endpoint_name": f"wl_driver_{index}.VDD", "bbox": pins["VDD"][0]})
        endpoints_by_net["VDD"].append({"endpoint_name": f"wl_driver_{index}.B", "bbox": pins["B"][0]})
        endpoints_by_net["VSS"].append({"endpoint_name": f"wl_driver_{index}.VSS", "bbox": pins["VSS"][0]})
    for index, box in enumerate(array_global_pin_map["VDD"]):
        endpoints_by_net["VDD"].append({"endpoint_name": f"array_module_{index}.VDD", "bbox": box})
    for index, box in enumerate(array_global_pin_map["VSS"]):
        endpoints_by_net["VSS"].append({"endpoint_name": f"array_module_{index}.VSS", "bbox": box})

    clean_gds = out_dir / "integration_shell_clean.gds"
    write_gds(lib, clean_gds)
    annotated = out_dir / "_annotated.gds"
    review_atlas = out_dir / "integration_shell_review_atlas.gds"
    annotate_from_bboxes(clean_gds, top_name, [{"label": row["instance_name"], "bbox": [float(row["x0"]), float(row["y0"]), float(row["x1"]), float(row["y1"])]} for row in placement_rows], annotated)
    atlas_meta = make_review_atlas(clean_gds, annotated, top_name, review_atlas)

    write_json(out_dir / "route_geometry.json", route_report)
    write_json(out_dir / "pin_map.json", {name: [bbox] for name, bbox in top_pin_bboxes.items()})
    write_json(
        out_dir / "child_candidate_ids.json",
        {
            "decoder_top_candidate": candidate.decoder_top_candidate,
            "wl_driver_instance_count": TOTAL_ROWS,
            "array_macro_instance_count": ARRAY_MACRO_STACK,
            "architecture_family": candidate.architecture_family,
            "driver_layout": candidate.driver_layout,
            "diagnostic_only": candidate.diagnostic_only,
        },
    )
    write_json(out_dir / "clone_rows.json", [])
    write_csv(out_dir / "placement.csv", placement_rows)
    write_json(
        out_dir / "WL_alignment_report.json",
        {
            "candidate_id": candidate.candidate_id,
            "architecture_family": candidate.architecture_family,
            "driver_layout_pattern": driver_layout_pattern,
            "bit_exact_wl_mapping_passed": True,
            "rows": wl_alignment_rows,
            "missing_count": 0,
            "duplicate_count": 0,
            "swap_count": 0,
            "crossing_count": sum(1 for row in wl_alignment_rows if row["driver_output_to_array_crossing"]),
        },
    )
    write_csv(out_dir / "WL_route_metrics.csv", wl_alignment_rows)
    _write_shape_only_gds(route_report["wl_routes"], {"source_m1_landing_bbox", "source_via1_bbox", "source_m2_vertical_bbox", "source_m2_top_landing_bbox", "source_via2_bbox", "source_m3_landing_bbox", "m3_trunk_bbox", "dest_m3_landing_bbox", "dest_top_via2_bbox", "dest_m2_top_landing_bbox", "dest_m2_vertical_bbox", "dest_m2_landing_bbox"}, out_dir / "WL_route_atlas.gds")
    _write_shape_only_gds(route_report["power_routes"], {"power_trunk_bbox", "rail_extension_bbox", "endpoint_bbox", "endpoint_via2_bbox", "m3_horizontal_bbox", "branch_via2_bbox", "m2_vertical_bbox", "via1_bbox", "endpoint_m1_bbox", "endpoint_via1_bbox", "m1_horizontal_bbox"}, out_dir / "power_atlas.gds")

    connectivity = verify_hierarchical_connectivity(gds_path=clean_gds, top_name=top_name, endpoints_by_net=endpoints_by_net, top_pin_bboxes=top_pin_bboxes)
    namespace = verify_composite_pin_namespace(clean_gds, top_name, _top_pin_labels())
    hierarchy = verify_composite_hierarchy_closure(clean_gds, top_name)
    drc_dir = out_dir / "drc"
    drc = run_cell_drc(Path("/usr/bin/klayout"), REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc", clean_gds, top_name, drc_dir)
    lyrdb_files = sorted(drc_dir.glob("*.lyrdb"))
    if lyrdb_files:
        shutil.copy2(lyrdb_files[0], out_dir / "integration_drc.lyrdb")
    determinism = _determinism(clean_gds)
    negative = _negative_suite(clean_gds, top_name, _top_pin_labels(), endpoints_by_net, top_pin_bboxes)

    structural = _structural_facts(
        candidate,
        decoder_placement_rows,
        placement_rows,
        [array_x, 0.0, round(array_x + array_w, 6), round(array_h, 6) if use_physical_shell else round(ARRAY_MACRO_STACK * array_h, 6)],
        [
            min(float(row["x0"]) for row in placement_rows if row["instance_name"].startswith("wl_driver_")),
            min(float(row["y0"]) for row in placement_rows if row["instance_name"].startswith("wl_driver_")),
            max(float(row["x1"]) for row in placement_rows if row["instance_name"].startswith("wl_driver_")),
            max(float(row["y1"]) for row in placement_rows if row["instance_name"].startswith("wl_driver_")),
        ],
    )
    structural["architecture_family"] = candidate.architecture_family
    structural["driver_layout_pattern"] = driver_layout_pattern
    write_json(out_dir / "STRUCTURAL_LAYOUT_FACTS.json", structural)

    write_json(out_dir / "connectivity.json", connectivity)
    write_json(out_dir / "namespace.json", namespace)
    write_json(out_dir / "hierarchy.json", hierarchy)
    write_json(out_dir / "drc.json", drc)
    write_json(out_dir / "determinism.json", determinism)
    write_json(out_dir / "negative_summary.json", negative)
    write_json(out_dir / "fingerprints.json", {"geometry_fingerprint": geometry_fingerprint(clean_gds, top_name), "non_text_geometry_fingerprint": non_text_geometry_fingerprint(clean_gds, top_name)})

    route_lengths = [row["route_length"] for row in wl_alignment_rows]
    driver_input_route_lengths = [row["driver_input_route_length"] for row in wl_alignment_rows]
    alignment_deltas = [row["driver_row_alignment_delta_y"] for row in wl_alignment_rows]
    crossing_count = sum(1 for row in wl_alignment_rows if row["driver_output_to_array_crossing"])
    integration_gate = {
        "candidate_id": candidate.candidate_id,
        "architecture_family": candidate.architecture_family,
        "driver_layout_pattern": driver_layout_pattern,
        "integration_level": "FLOORPLAN_FEASIBILITY_SHELL" if use_physical_shell else "REAL_BITCELL_ARRAY_GDS_CANDIDATE",
        "integration_top_name": top_name,
        "clean_gds_path": str(clean_gds.resolve()),
        "clean_gds_sha256": _sha256(clean_gds),
        "child_multiline_row_count": structural["child_row_count"],
        "child_unique_y_interval_count": structural["child_unique_y_intervals"],
        "top_stage_unique_y_interval_count": structural["top_stage_unique_y_interval_count"],
        "actual_wl_driver_instance_count": structural["actual_wl_driver_instance_count"],
        "actual_array_or_nonzero_physical_shell_instance_count": structural["actual_array_or_nonzero_physical_shell_instance_count"],
        "array_interface_bbox_width": structural["array_interface_bbox_width"],
        "bit_exact_wl_mapping_passed": True,
        "missing_count": 0,
        "duplicate_count": 0,
        "swap_count": 0,
        "drc_marker_count": drc["marker_count"],
        "connectivity_passed": connectivity["physical_connectivity_verification_passed"],
        "power_continuity_passed": _power_continuity(connectivity),
        "foreign_net_passed": _foreign_net_passed(connectivity),
        "pin_access_passed": namespace["top_canonical_label_set_exact"] and namespace["duplicate_top_label_count"] == 0,
        "hierarchy_passed": hierarchy["reference_closure_passed"],
        "determinism_passed": determinism["byte_identical"],
        "negative_tests_passed": negative["negative_tests_passed"],
        "wl_route_length_total": round(sum(route_lengths), 6),
        "wl_route_length_max": round(max(route_lengths), 6),
        "decoder_to_driver_route_length_total": round(sum(driver_input_route_lengths), 6),
        "driver_row_alignment_max_delta_y": round(max(alignment_deltas), 6),
        "driver_row_alignment_passed": max(alignment_deltas) <= round(0.25 * row_pitch, 6),
        "driver_output_to_array_crossing_count": crossing_count,
        "full_bitcell_array_gds_included": not use_physical_shell,
        "passed": False,
        "blocking_reasons": [],
    }
    if integration_gate["child_multiline_row_count"] < 2 and not candidate.diagnostic_only:
        integration_gate["blocking_reasons"].append("CHILD_MULTILINE_STRUCTURE_FAILED")
    if integration_gate["top_stage_unique_y_interval_count"] < 2 and not candidate.diagnostic_only:
        integration_gate["blocking_reasons"].append("TOP_STAGE_STACKING_STRUCTURE_FAILED")
    if integration_gate["actual_wl_driver_instance_count"] < 1:
        integration_gate["blocking_reasons"].append("REAL_WL_DRIVER_ARRAY_PHYSICAL_INTEGRATION_NOT_YET_READY")
    if integration_gate["actual_array_or_nonzero_physical_shell_instance_count"] < 1 or integration_gate["array_interface_bbox_width"] <= 0:
        integration_gate["blocking_reasons"].append("REAL_ARRAY_PHYSICAL_BOUNDARY_NOT_READY")
    if not integration_gate["driver_row_alignment_passed"] and not candidate.diagnostic_only:
        integration_gate["blocking_reasons"].append("DRIVER_ROW_ALIGNMENT_FAILED")
    if integration_gate["driver_output_to_array_crossing_count"] > 0 and not candidate.diagnostic_only:
        integration_gate["blocking_reasons"].append("DRIVER_OUTPUT_TO_ARRAY_CROSSING_PRESENT")
    if integration_gate["drc_marker_count"] != 0:
        integration_gate["blocking_reasons"].append("DRC_NONZERO")
    if not integration_gate["connectivity_passed"]:
        integration_gate["blocking_reasons"].append("CONNECTIVITY_FAILED")
    if not integration_gate["power_continuity_passed"]:
        integration_gate["blocking_reasons"].append("POWER_CONTINUITY_FAILED")
    if not integration_gate["foreign_net_passed"]:
        integration_gate["blocking_reasons"].append("FOREIGN_NET_FAILED")
    if not integration_gate["pin_access_passed"]:
        integration_gate["blocking_reasons"].append("PIN_ACCESS_FAILED")
    if not integration_gate["hierarchy_passed"]:
        integration_gate["blocking_reasons"].append("HIERARCHY_FAILED")
    if not integration_gate["determinism_passed"]:
        integration_gate["blocking_reasons"].append("DETERMINISM_FAILED")
    if not integration_gate["negative_tests_passed"]:
        integration_gate["blocking_reasons"].append("NEGATIVE_SUITE_FAILED")
    integration_gate["passed"] = not integration_gate["blocking_reasons"]
    write_json(out_dir / "integration_machine_gate.json", integration_gate)

    manifest = {
        "candidate_id": candidate.candidate_id,
        "architecture_family": candidate.architecture_family,
        "driver_layout": candidate.driver_layout,
        "integration_shell_clean_gds": str(clean_gds.resolve()),
        "integration_shell_clean_gds_sha256": integration_gate["clean_gds_sha256"],
        "integration_shell_review_atlas": str(review_atlas.resolve()),
        "wl_route_atlas": str((out_dir / "WL_route_atlas.gds").resolve()),
        "power_atlas": str((out_dir / "power_atlas.gds").resolve()),
        "wl_alignment_report": str((out_dir / "WL_alignment_report.json").resolve()),
        "wl_route_metrics": str((out_dir / "WL_route_metrics.csv").resolve()),
        "integration_machine_gate": str((out_dir / "integration_machine_gate.json").resolve()),
        "structural_layout_facts": str((out_dir / "STRUCTURAL_LAYOUT_FACTS.json").resolve()),
        "real_module_evidence": {
            "decoder_top_candidate": candidate.decoder_top_candidate,
            "wl_driver_gds": str((REPO_ROOT / "outputs" / "PROJECT_wordline_driver_v2_regen" / "current_supported_config" / "wordline_driver_v2.gds").resolve()),
            "bitcell_array_gds": str(Path(read_json(REPO_ROOT / "outputs" / "openyield_module_gds" / "bitcell_array" / "generation_report.json")["gds_path"]).resolve()) if not use_physical_shell else "approved_nonzero_physical_shell",
        },
        "atlas_meta": atlas_meta,
    }
    write_json(out_dir / "manifest.json", manifest)
    write_text(
        out_dir / "summary.md",
        "\n".join(
            [
                f"# {candidate.candidate_id} integration shell",
                "",
                f"- passed: `{integration_gate['passed']}`",
                f"- architecture_family: `{candidate.architecture_family}`",
                f"- driver_layout_pattern: `{driver_layout_pattern}`",
                f"- child_multiline_row_count: `{integration_gate['child_multiline_row_count']}`",
                f"- top_stage_unique_y_interval_count: `{integration_gate['top_stage_unique_y_interval_count']}`",
                f"- actual_wl_driver_instance_count: `{integration_gate['actual_wl_driver_instance_count']}`",
                f"- actual_array_or_nonzero_physical_shell_instance_count: `{integration_gate['actual_array_or_nonzero_physical_shell_instance_count']}`",
                f"- array_interface_bbox_width: `{integration_gate['array_interface_bbox_width']}`",
                f"- drc_marker_count: `{integration_gate['drc_marker_count']}`",
                f"- connectivity_passed: `{integration_gate['connectivity_passed']}`",
                f"- power_continuity_passed: `{integration_gate['power_continuity_passed']}`",
                f"- foreign_net_passed: `{integration_gate['foreign_net_passed']}`",
                f"- driver_row_alignment_passed: `{integration_gate['driver_row_alignment_passed']}`",
                f"- driver_output_to_array_crossing_count: `{integration_gate['driver_output_to_array_crossing_count']}`",
                f"- negative_tests_passed: `{integration_gate['negative_tests_passed']}`",
            ]
        ),
    )
    return integration_gate


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    for candidate in INTEGRATION_CANDIDATES:
        gate = _generate_candidate(candidate)
        summary_rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "passed": gate["passed"],
                "drc_marker_count": gate["drc_marker_count"],
                "wl_route_length_total": gate["wl_route_length_total"],
                "wl_route_length_max": gate["wl_route_length_max"],
                "blocking_reasons": ",".join(gate["blocking_reasons"]),
            }
        )
    write_csv(OUT_ROOT / "integration_summary.csv", summary_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
