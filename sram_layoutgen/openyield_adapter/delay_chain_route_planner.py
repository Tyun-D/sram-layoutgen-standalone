from __future__ import annotations

import math
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.delay_chain_contract import stage_driver_role, stage_load_role
from sram_layoutgen.openyield_adapter.grid_legal_geometry import snap_bbox, snap_coordinate
from sram_layoutgen.tech import Tech


def _center(bbox: dict[str, float]) -> tuple[float, float]:
    return (round((bbox["lx"] + bbox["rx"]) * 0.5, 6), round((bbox["by"] + bbox["uy"]) * 0.5, 6))


def _m1(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=11, datatype=0))


def _m2(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=13, datatype=0))


def _via1(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=12, datatype=0))


def build_delay_chain_power_rails(top: gdstk.Cell, placed_children: list[Any], tech: Tech) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    via = tech.via_between("m1", "m2")
    if via is None:
        raise RuntimeError("missing via1 definition")
    via_enc = 0.035
    m2_half = max(tech.layer("m2").min_width * 0.5, via.size * 0.5 + via_enc)
    grouped: dict[str, list[dict[str, float]]] = {"VDD": [], "VSS": []}
    for item in placed_children:
        grouped["VDD"].extend(item.placed_pin_map["VDD"])
        grouped["VSS"].extend(item.placed_pin_map["VSS"])

    def _bands(rows: list[dict[str, float]]) -> list[dict[str, float]]:
        bands: dict[tuple[float, float], list[dict[str, float]]] = {}
        for row in rows:
            key = (round(float(row["by"]), 6), round(float(row["uy"]), 6))
            bands.setdefault(key, []).append(row)
        out = []
        for (by, uy), items in sorted(bands.items()):
            out.append(
                snap_bbox(
                    {
                        "lx": min(item["lx"] for item in items),
                        "by": by,
                        "rx": max(item["rx"] for item in items),
                        "uy": uy,
                    },
                    grid,
                )
            )
        return out

    rails_vdd = _bands(grouped["VDD"])
    rails_vss = _bands(grouped["VSS"])
    max_rx = max(max(rail["rx"] for rail in rails_vdd), max(rail["rx"] for rail in rails_vss))
    spine_vdd_x = snap_coordinate(max_rx + 0.80, grid)
    spine_vss_x = snap_coordinate(max_rx + 1.10, grid)
    min_by = min(min(rail["by"] for rail in rails_vss), min(rail["by"] for rail in rails_vdd))
    max_uy = max(max(rail["uy"] for rail in rails_vss), max(rail["uy"] for rail in rails_vdd))

    def _extend_and_stitch(net: str, rails: list[dict[str, float]], spine_x: float) -> dict[str, Any]:
        rows = []
        vertical = snap_bbox({"lx": spine_x - m2_half, "by": min_by, "rx": spine_x + m2_half, "uy": max_uy}, grid)
        _m2(top, vertical)
        for rail in rails:
            extended = snap_bbox({"lx": rail["lx"], "by": rail["by"], "rx": spine_x + m2_half, "uy": rail["uy"]}, grid)
            _m1(top, extended)
            m2_landing = snap_bbox({"lx": spine_x - m2_half, "by": rail["by"], "rx": spine_x + m2_half, "uy": rail["uy"]}, grid)
            via_bbox = snap_bbox(
                {
                    "lx": spine_x - via.size * 0.5,
                    "by": ((rail["by"] + rail["uy"]) * 0.5) - via.size * 0.5,
                    "rx": spine_x + via.size * 0.5,
                    "uy": ((rail["by"] + rail["uy"]) * 0.5) + via.size * 0.5,
                },
                grid,
            )
            _m2(top, m2_landing)
            _via1(top, via_bbox)
            rows.append({"extended_rail_bbox": extended, "m2_landing_bbox": m2_landing, "via_bbox": via_bbox})
        return {"rails": rails, "spine_bbox": vertical, "stitching": rows}

    return {
        "VDD": _extend_and_stitch("VDD", rails_vdd, spine_vdd_x),
        "VSS": _extend_and_stitch("VSS", rails_vss, spine_vss_x),
    }


def build_delay_chain_routes(
    *,
    top: gdstk.Cell,
    placed_children: list[Any],
    stage_count: int,
    loads_per_stage: int,
    tech: Tech,
) -> dict[str, Any]:
    by_name = {child.spec.instance_name: child for child in placed_children}
    grid = tech.manufacturing_grid
    via = tech.via_between("m1", "m2")
    if via is None:
        raise RuntimeError("missing via1 definition")
    via_enc = 0.035
    m2_half = max(tech.layer("m2").min_width * 0.5, via.size * 0.5 + via_enc)
    route_rows: list[dict[str, Any]] = []
    cross_row_route_count = 0
    total_signal_wire_length = 0.0
    maximum_route_length = 0.0
    via1_count = 0
    route_bboxes: list[dict[str, float]] = []
    for stage_index in range(stage_count):
        driver = by_name[stage_driver_role(stage_index)]
        driver_z = driver.placed_pin_map["Z"][0]
        driver_row_top = max(float(driver.bbox[3]), max(float(by_name[stage_load_role(stage_index, load_index)].bbox[3]) for load_index in range(loads_per_stage)))
        track_y = snap_coordinate(driver_row_top + 0.14 + (stage_index % 2) * 0.02, grid)
        branch_bboxes = [driver_z]
        for load_index in range(loads_per_stage):
            branch_bboxes.append(by_name[stage_load_role(stage_index, load_index)].placed_pin_map["A"][0])
        if stage_index < stage_count - 1:
            branch_bboxes.append(by_name[stage_driver_role(stage_index + 1)].placed_pin_map["A"][0])
        else:
            branch_bboxes.append(driver.placed_pin_map["Z"][0])
        centers = [_center(bbox) for bbox in branch_bboxes]
        same_row_centers = centers[: 1 + loads_per_stage]
        trunk_lx = min(cx for cx, _ in same_row_centers)
        trunk_rx = max(cx for cx, _ in same_row_centers)
        if stage_index < stage_count - 1:
            next_cx, next_cy = centers[-1]
            trunk_rx = max(trunk_rx, next_cx)
        trunk = snap_bbox({"lx": trunk_lx, "by": track_y - m2_half, "rx": trunk_rx, "uy": track_y + m2_half}, grid)
        _m2(top, trunk)
        route_rows.append({"net_name": f"stage_{stage_index:02d}_net", "endpoint": "trunk", "m2_trunk_bbox": trunk})
        route_bboxes.append(trunk)
        total_signal_wire_length += float(trunk["rx"]) - float(trunk["lx"])
        maximum_route_length = max(maximum_route_length, float(trunk["rx"]) - float(trunk["lx"]))
        for endpoint_index, bbox in enumerate(branch_bboxes):
            cx, cy = centers[endpoint_index]
            m1_half = max(tech.layer("m1").min_width * 0.5, via.size * 0.5 + via_enc)
            m1_landing = snap_bbox(
                {
                    "lx": cx - m1_half,
                    "by": cy - m1_half,
                    "rx": cx + m1_half,
                    "uy": cy + m1_half,
                },
                grid,
            )
            m2_landing = snap_bbox(
                {
                    "lx": cx - m2_half,
                    "by": min(cy - m2_half, track_y - m2_half),
                    "rx": cx + m2_half,
                    "uy": max(cy + m2_half, track_y + m2_half),
                },
                grid,
            )
            via_bbox = snap_bbox({"lx": cx - via.size * 0.5, "by": cy - via.size * 0.5, "rx": cx + via.size * 0.5, "uy": cy + via.size * 0.5}, grid)
            _m1(top, m1_landing)
            _m2(top, m2_landing)
            _via1(top, via_bbox)
            endpoint_name = (
                f"stage_{stage_index:02d}_driver.Z"
                if endpoint_index == 0
                else (
                    f"stage_{stage_index:02d}_load_{endpoint_index - 1:02d}.A"
                    if endpoint_index <= loads_per_stage
                    else ("TOP.out" if stage_index == stage_count - 1 else f"stage_{stage_index + 1:02d}_driver.A")
                )
            )
            route_rows.append(
                {
                    "net_name": f"stage_{stage_index:02d}_net",
                    "endpoint": endpoint_name,
                    "m1_landing_bbox": m1_landing,
                    "m2_landing_bbox": m2_landing,
                    "via_bbox": via_bbox,
                }
            )
            route_bboxes.extend([m1_landing, m2_landing, via_bbox])
            total_signal_wire_length += max(float(m1_landing["uy"]) - float(m1_landing["by"]), float(m2_landing["uy"]) - float(m2_landing["by"]))
            maximum_route_length = max(
                maximum_route_length,
                max(float(m1_landing["uy"]) - float(m1_landing["by"]), float(m2_landing["uy"]) - float(m2_landing["by"])),
            )
            via1_count += 1
        if stage_index < stage_count - 1 and abs(centers[-1][1] - centers[0][1]) > 0.2:
            cross_row_route_count += 1
    off_grid_count = 0
    for bbox in route_bboxes:
        for value in bbox.values():
            if not math.isclose(float(value), snap_coordinate(float(value), grid), rel_tol=0.0, abs_tol=1e-9):
                off_grid_count += 1
    return {
        "routing_architecture": "stage_trunk_m2_with_endpoint_landings",
        "route_rows": route_rows,
        "route_segment_count": len(route_rows),
        "via1_count": via1_count,
        "total_signal_wire_length": round(total_signal_wire_length, 6),
        "maximum_route_length": round(maximum_route_length, 6),
        "cross_row_route_count": cross_row_route_count,
        "off_grid_count": off_grid_count,
        "route_bboxes": route_bboxes,
    }
