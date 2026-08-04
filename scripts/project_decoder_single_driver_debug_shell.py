#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.composite_pin_namespace_verifier import verify_composite_pin_namespace
from sram_layoutgen.openyield_adapter.decoder_generator import _m1_to_m3_to_m2_route, _m2m3_pin_to_m1_rail_route
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import run_cell_drc
from sram_layoutgen.openyield_adapter.teamb_composite_helper import add_top_label, read_json, write_csv, write_gds, write_json
from sram_layoutgen.tech import Tech


OUT_ROOT = REPO_ROOT / "outputs" / "PROJECT_decoder_wl_array_integration_shell" / "single_driver_debug"


def _box_center(box: dict[str, float]) -> tuple[float, float]:
    return (round((float(box["lx"]) + float(box["rx"])) * 0.5, 6), round((float(box["by"]) + float(box["uy"])) * 0.5, 6))


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


def _build_array_physical_shell(tech: Tech) -> tuple[gdstk.Cell, dict[str, list[dict[str, float]]], dict[str, Any]]:
    generation = read_json(REPO_ROOT / "outputs" / "openyield_module_gds" / "bitcell_array" / "generation_report.json")
    bbox = generation["bbox"]
    row_pitch = round(float(bbox["height"]) / int(generation["array_rows"]), 6)
    shell_height = round(row_pitch * 16, 6)
    shell_width = round(float(bbox["width"]), 6)
    m2_width = tech.layer("m2").min_width
    m1_width = tech.layer("m1").min_width
    shell = gdstk.Cell("approved_array_physical_shell_debug")
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
    for wl_index in range(16):
        y = round(wl_index * row_pitch + row_pitch * 0.5, 6)
        x = 0.15
        wl_box = _snap_box({"lx": x, "by": y - m2_width * 0.5, "rx": x + m2_width, "uy": y + m2_width * 0.5}, grid)
        pin_map[f"WL{wl_index}"] = [{"layer": "m2", **wl_box}]
        shell.add(gdstk.rectangle((wl_box["lx"], wl_box["by"]), (wl_box["rx"], wl_box["uy"]), layer=13, datatype=0))
    return shell, pin_map, {"bbox": {"width": shell_width, "height": shell_height}, "row_pitch": row_pitch}


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
    for box, layer in [
        (source_m1_landing_bbox, 11),
        (source_via1_bbox, 12),
        (source_m2_vertical_bbox, 13),
        (source_m2_top_landing_bbox, 13),
        (source_via2_bbox, 14),
        (source_m3_landing_bbox, 15),
        (m3_trunk_bbox, 15),
        (dest_m3_landing_bbox, 15),
        (dest_top_via2_bbox, 14),
        (dest_m2_top_landing_bbox, 13),
        (dest_m2_vertical_bbox, 13),
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
    en_cx, en_cy = _box_center(enable_box)
    vdd_cx, vdd_cy = _box_center(vdd_box)
    target_y = round(min(vdd_cy, float(vdd_box["by"]) - half_m1), 6)
    endpoint_m1_bbox = _snap_box({"lx": en_cx - half_m1, "by": en_cy - half_m1, "rx": en_cx + half_m1, "uy": en_cy + half_m1}, grid)
    endpoint_via1_bbox = _snap_box({"lx": en_cx - via1.size * 0.5, "by": en_cy - via1.size * 0.5, "rx": en_cx + via1.size * 0.5, "uy": en_cy + via1.size * 0.5}, grid)
    m2_vertical_bbox = _snap_box({"lx": en_cx - half_m2, "by": min(en_cy, target_y) - half_m2, "rx": en_cx + half_m2, "uy": max(en_cy, target_y) + half_m2}, grid)
    m1_horizontal_bbox = _snap_box({"lx": min(en_cx, vdd_cx) - half_m1, "by": target_y - half_m1, "rx": max(en_cx, vdd_cx) + half_m1, "uy": target_y + half_m1}, grid)
    for box, layer in [(endpoint_m1_bbox, 11), (endpoint_via1_bbox, 12), (m2_vertical_bbox, 13), (m1_horizontal_bbox, 11)]:
        top.add(gdstk.rectangle((box["lx"], box["by"]), (box["rx"], box["uy"]), layer=layer, datatype=0))
    return {
        "endpoint_bbox": enable_box,
        "vdd_bbox": vdd_box,
        "endpoint_m1_bbox": endpoint_m1_bbox,
        "endpoint_via1_bbox": endpoint_via1_bbox,
        "m2_vertical_bbox": m2_vertical_bbox,
        "m1_horizontal_bbox": m1_horizontal_bbox,
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wl-index", type=int, default=15)
    parser.add_argument("--wl-index-2", type=int, default=None)
    parser.add_argument("--wl-list", type=str, default=None)
    parser.add_argument("--include-a-route", action="store_true")
    parser.add_argument("--include-b-tie", action="store_true")
    parser.add_argument("--include-z-route", action="store_true")
    parser.add_argument("--global-power", action="store_true")
    args = parser.parse_args()

    tech = Tech.freepdk45(REPO_ROOT)
    out_dir = OUT_ROOT / f"wl{args.wl_index:02d}_a{int(args.include_a_route)}_b{int(args.include_b_tie)}_z{int(args.include_z_route)}"
    out_dir.mkdir(parents=True, exist_ok=True)

    decoder_root = REPO_ROOT / "outputs" / "PROJECT_decoder_top_v3" / "candidate_true_wl_driver_array_oriented"
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

    shell_cell, shell_pin_map, shell_meta = _build_array_physical_shell(tech)
    row_pitch = round(float(shell_meta["row_pitch"]), 6)
    z_center_y = _box_center(driver_pin_map["Z"][0])[1]

    lib = decoder_lib
    existing_names = {cell.name for cell in lib.cells}
    for cell in driver_lib.cells:
        if cell.name not in existing_names:
            lib.add(cell.copy(cell.name))
            existing_names.add(cell.name)
    if shell_cell.name not in existing_names:
        lib.add(shell_cell.copy(shell_cell.name))
        existing_names.add(shell_cell.name)
    cell_by_name = {cell.name: cell for cell in lib.cells}
    top = lib.new_cell(f"single_driver_debug_wl{args.wl_index}")
    top.add(gdstk.Reference(cell_by_name[decoder_cell.name], (0.0, 0.0)))

    driver_x = round(decoder_bbox[2] + 5.0, 6)
    alt_x = round(driver_x + driver_w + 2.0, 6)
    if args.wl_list:
        wl_indices = sorted({int(token.strip()) for token in args.wl_list.split(",") if token.strip()})
    else:
        wl_indices = [args.wl_index] if args.wl_index_2 is None else sorted({args.wl_index, args.wl_index_2})
    driver_instances: dict[int, dict[str, list[dict[str, float]]]] = {}
    placements: list[dict[str, Any]] = [{"instance_name": "decoder_top", "module": "decoder_top_v3", "x0": decoder_bbox[0], "y0": decoder_bbox[1], "x1": decoder_bbox[2], "y1": decoder_bbox[3], "orientation": "R0"}]
    for wl_index in wl_indices:
        driver_y = round(wl_index * row_pitch + row_pitch * 0.5 - z_center_y, 6)
        driver_place_x = driver_x if wl_index % 2 == 0 else alt_x
        top.add(gdstk.Reference(cell_by_name[driver_cell.name], (driver_place_x, driver_y)))
        driver_instances[wl_index] = _transform_pin_map(driver_pin_map, driver_place_x, driver_y)
        placements.append({"instance_name": f"wl_driver_{wl_index}", "module": "wordline_driver_v2", "x0": driver_place_x, "y0": driver_y, "x1": round(driver_place_x + driver_w, 6), "y1": round(driver_y + driver_h, 6), "orientation": "R0"})

    array_x = round(max(driver_x, alt_x) + driver_w + 4.0, 6)
    top.add(gdstk.Reference(cell_by_name[shell_cell.name], (array_x, 0.0)))
    array_pins = _transform_pin_map(shell_pin_map, array_x, 0.0)
    placements.append({"instance_name": "approved_array_physical_shell_0", "module": "approved_array_physical_shell", "x0": array_x, "y0": 0.0, "x1": round(array_x + shell_meta['bbox']['width'], 6), "y1": round(shell_meta['bbox']['height'], 6), "orientation": "R0"})

    top_pin_bboxes: dict[str, dict[str, float]] = {}
    for label in ["A0", "A1", "A2", "A3", "VDD", "VSS"] + [f"WL{i}" for i in range(16)]:
        if label.startswith("WL") and label in array_pins:
            top_pin_bboxes[label] = array_pins[label][0]
        elif label in decoder_pin_map:
            top_pin_bboxes[label] = decoder_pin_map[label][0]
        elif label in array_pins:
            top_pin_bboxes[label] = array_pins[label][0]
        add_top_label(top, label, top_pin_bboxes[label])

    route_geometry: dict[str, Any] = {}
    for wl_index, driver_pins in driver_instances.items():
        if args.include_a_route:
            source_branch_x_shift = 0.4 if wl_index < 8 else -0.4
            route_geometry[f"a_route_wl{wl_index}"] = _m1_to_m3_to_m2_route(
                top=top,
                tech=tech,
                source_box=decoder_pin_map[f"WL{wl_index}"][0],
                dest_box=driver_pins["A"][0],
                track_y=round(_box_center(driver_pins["A"][0])[1], 6),
                source_branch_x_shift=source_branch_x_shift,
                dest_branch_x_shift=0.0,
            )
        if args.include_b_tie:
            route_geometry[f"b_tie_wl{wl_index}"] = _tie_driver_enable_to_local_vdd(top=top, tech=tech, enable_box=driver_pins["B"][0], vdd_box=driver_pins["VDD"][0])
        if args.include_z_route:
            route_geometry[f"z_route_wl{wl_index}"] = _m1_to_m2_route(
                top=top,
                tech=tech,
                source_box=driver_pins["Z"][0],
                dest_box=array_pins[f"WL{wl_index}"][0],
                track_y=round(_box_center(array_pins[f"WL{wl_index}"][0])[1], 6),
            )

    if args.global_power:
        vdd_boxes = [decoder_pin_map["VDD"][0], array_pins["VDD"][0]] + [driver_pins["VDD"][0] for driver_pins in driver_instances.values()]
        vss_boxes = [decoder_pin_map["VSS"][0], array_pins["VSS"][0]] + [driver_pins["VSS"][0] for driver_pins in driver_instances.values()]
        trunk_y0 = min(min(float(box["by"]) for box in vdd_boxes), min(float(box["by"]) for box in vss_boxes))
        trunk_y1 = max(max(float(box["uy"]) for box in vdd_boxes), max(float(box["uy"]) for box in vss_boxes))
        vdd_trunk_x = round(array_x + shell_meta["bbox"]["width"] + 2.0, 6)
        vss_trunk_x = round(vdd_trunk_x + 2.0, 6)
        top_pin_bboxes["VDD"] = _add_power_trunk(top, tech, vdd_trunk_x, trunk_y0, trunk_y1)
        top_pin_bboxes["VSS"] = _add_power_trunk(top, tech, vss_trunk_x, trunk_y0, trunk_y1)
        route_geometry["global_power_vdd"] = _m2m3_pin_to_m1_rail_route(top=top, tech=tech, endpoint_boxes=vdd_boxes, rail_box=top_pin_bboxes["VDD"], branch_x=round((top_pin_bboxes["VDD"]["lx"] + top_pin_bboxes["VDD"]["rx"]) * 0.5, 6))
        route_geometry["global_power_vss"] = _m2m3_pin_to_m1_rail_route(top=top, tech=tech, endpoint_boxes=vss_boxes, rail_box=top_pin_bboxes["VSS"], branch_x=round((top_pin_bboxes["VSS"]["lx"] + top_pin_bboxes["VSS"]["rx"]) * 0.5, 6))
        add_top_label(top, "VDD", top_pin_bboxes["VDD"])
        add_top_label(top, "VSS", top_pin_bboxes["VSS"])

    clean_gds = out_dir / "clean.gds"
    write_gds(lib, clean_gds)
    write_json(out_dir / "route_geometry.json", route_geometry)
    write_csv(out_dir / "placement.csv", placements)

    endpoints_by_net = {
        "VDD": [{"endpoint_name": "decoder_top.VDD", "bbox": decoder_pin_map["VDD"][0]}, {"endpoint_name": "array.VDD", "bbox": array_pins["VDD"][0]}],
        "VSS": [{"endpoint_name": "decoder_top.VSS", "bbox": decoder_pin_map["VSS"][0]}, {"endpoint_name": "array.VSS", "bbox": array_pins["VSS"][0]}],
    }
    for wl_index, driver_pins in driver_instances.items():
        endpoints_by_net["VDD"].extend(
            [
                {"endpoint_name": f"driver{wl_index}.VDD", "bbox": driver_pins["VDD"][0]},
                {"endpoint_name": f"driver{wl_index}.B", "bbox": driver_pins["B"][0]},
            ]
        )
        endpoints_by_net["VSS"].append({"endpoint_name": f"driver{wl_index}.VSS", "bbox": driver_pins["VSS"][0]})
        endpoints_by_net[f"WL{wl_index}"] = [{"endpoint_name": f"driver{wl_index}.Z", "bbox": driver_pins["Z"][0]}, {"endpoint_name": f"array{wl_index}.WL", "bbox": array_pins[f"WL{wl_index}"][0]}]
        endpoints_by_net[f"DRIVER_A_WL{wl_index}"] = [{"endpoint_name": f"decoder_top.WL{wl_index}", "bbox": decoder_pin_map[f"WL{wl_index}"][0]}, {"endpoint_name": f"driver{wl_index}.A", "bbox": driver_pins["A"][0]}]
    connectivity = verify_hierarchical_connectivity(
        gds_path=clean_gds,
        top_name=top.name,
        endpoints_by_net=endpoints_by_net,
        top_pin_bboxes=top_pin_bboxes,
        metal_only=True,
    )
    namespace = verify_composite_pin_namespace(clean_gds, top.name, ["A0", "A1", "A2", "A3"] + [f"WL{i}" for i in range(16)] + ["VDD", "VSS"])
    drc_dir = out_dir / "drc"
    drc = run_cell_drc(Path("/usr/bin/klayout"), REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc", clean_gds, top.name, drc_dir)
    lyrdb_files = sorted(drc_dir.glob("*.lyrdb"))
    if lyrdb_files:
        shutil.copy2(lyrdb_files[0], out_dir / "drc.lyrdb")
    write_json(out_dir / "connectivity.json", connectivity)
    write_json(out_dir / "namespace.json", namespace)
    write_json(out_dir / "drc.json", drc)
    print(json.dumps({"out_dir": str(out_dir), "unexpected_net_merges": connectivity["unexpected_net_merges"], "drc_marker_count": drc["marker_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
