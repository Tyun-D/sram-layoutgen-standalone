from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.grid_legal_geometry import snap_bbox, snap_coordinate
from sram_layoutgen.openyield_adapter.inverter_chain_floorplan_planner import Placement
from sram_layoutgen.openyield_adapter.teamb_composite_helper import add_horizontal_pin_route
from sram_layoutgen.tech import Tech


def _bbox_length(bbox: dict[str, float]) -> float:
    return round(max(float(bbox["rx"]) - float(bbox["lx"]), float(bbox["uy"]) - float(bbox["by"])), 6)


def _round6(value: float) -> float:
    return round(float(value), 6)


def build_row_aware_power_rails(top: gdstk.Cell, placed_children: list[Any], tech: Tech) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    via = tech.via_between("m1", "m2")
    if via is None:
        raise RuntimeError("missing via1 definition for m1/m2")
    via_enc = 0.035
    m2_half = max(tech.layer("m2").min_width * 0.5, via.size * 0.5 + via_enc)
    grouped: dict[str, list[dict[str, float]]] = {"VDD": [], "VSS": []}
    for item in placed_children:
        grouped["VDD"].extend(item.placed_pin_map["VDD"])
        grouped["VSS"].extend(item.placed_pin_map["VSS"])

    def _bands(rows: list[dict[str, float]]) -> list[dict[str, float]]:
        bands: dict[tuple[float, float], list[dict[str, float]]] = {}
        for row in rows:
            key = (_round6(row["by"]), _round6(row["uy"]))
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

    result: dict[str, Any] = {}
    for net in ("VDD", "VSS"):
        rails = _bands(grouped[net])
        for rail in rails:
            top.add(gdstk.rectangle((rail["lx"], rail["by"]), (rail["rx"], rail["uy"]), layer=11, datatype=0))
        straps = []
        if len(rails) > 1:
            strap_x = snap_coordinate(min(rail["lx"] for rail in rails) + 0.18, grid)
            min_by = min(rail["by"] for rail in rails)
            max_uy = max(rail["uy"] for rail in rails)
            vertical = snap_bbox({"lx": strap_x - m2_half, "by": min_by, "rx": strap_x + m2_half, "uy": max_uy}, grid)
            top.add(gdstk.rectangle((vertical["lx"], vertical["by"]), (vertical["rx"], vertical["uy"]), layer=13, datatype=0))
            for rail in rails:
                m2_landing = snap_bbox({"lx": strap_x - m2_half, "by": rail["by"], "rx": strap_x + m2_half, "uy": rail["uy"]}, grid)
                via_bbox = snap_bbox({"lx": strap_x - via.size * 0.5, "by": ((rail["by"] + rail["uy"]) * 0.5) - via.size * 0.5, "rx": strap_x + via.size * 0.5, "uy": ((rail["by"] + rail["uy"]) * 0.5) + via.size * 0.5}, grid)
                top.add(gdstk.rectangle((m2_landing["lx"], m2_landing["by"]), (m2_landing["rx"], m2_landing["uy"]), layer=13, datatype=0))
                top.add(gdstk.rectangle((via_bbox["lx"], via_bbox["by"]), (via_bbox["rx"], via_bbox["uy"]), layer=12, datatype=0))
                straps.append({"m2_landing_bbox": m2_landing, "via_bbox": via_bbox})
            straps.append({"m2_vertical_bbox": vertical})
        result[net] = {"rails": rails, "stitching": straps}
    return result


def build_inverter_chain_routes(
    *,
    top: gdstk.Cell,
    placed_children: list[Any],
    internal_net_names: list[str],
    tech: Tech,
) -> dict[str, Any]:
    route_rows = []
    route_bboxes: list[dict[str, float]] = []
    cross_row_route_count = 0
    signal_pin_top = max(
        max(float(item.placed_pin_map["A"][0]["uy"]), float(item.placed_pin_map["Z"][0]["uy"]))
        for item in placed_children
    )
    base_track_y = signal_pin_top + 0.02
    track_pitch = 0.10
    for index, (net_name, left, right) in enumerate(zip(internal_net_names, placed_children[:-1], placed_children[1:])):
        left_bbox = left.placed_pin_map["Z"][0]
        right_bbox = right.placed_pin_map["A"][0]
        if abs(((left_bbox["by"] + left_bbox["uy"]) * 0.5) - ((right_bbox["by"] + right_bbox["uy"]) * 0.5)) > 0.2:
            cross_row_route_count += 1
        track_y = base_track_y + index * track_pitch
        items = add_horizontal_pin_route(top, left_bbox, right_bbox, tech=tech, track_y=track_y)
        for row in items:
            route_rows.append({"net_name": net_name, **row})
            if "m1_landing_bbox" in row:
                route_bboxes.append(row["m1_landing_bbox"])
            if "m2_landing_bbox" in row:
                route_bboxes.append(row["m2_landing_bbox"])
            if "via_bbox" in row:
                route_bboxes.append(row["via_bbox"])
            if "m2_trunk_bbox" in row:
                route_bboxes.append(row["m2_trunk_bbox"])
    maximum_route_length = 0.0
    total_signal_length = 0.0
    via1_count = 0
    for row in route_rows:
        if "via_bbox" in row:
            via1_count += 1
        for key in ("m1_landing_bbox", "m2_landing_bbox", "m2_trunk_bbox"):
            if key in row:
                bbox = row[key]
                length = max(float(bbox["rx"]) - float(bbox["lx"]), float(bbox["uy"]) - float(bbox["by"]))
                total_signal_length += length
                maximum_route_length = max(maximum_route_length, length)
    off_grid_count = 0
    for bbox in route_bboxes:
        for value in bbox.values():
            snapped = snap_coordinate(float(value), tech.manufacturing_grid)
            if not math.isclose(float(value), snapped, rel_tol=0.0, abs_tol=1e-9):
                off_grid_count += 1
    return {
        "routing_architecture": "m1_landing_via1_m2_trunk",
        "route_rows": route_rows,
        "route_segment_count": len([row for row in route_rows if "m2_trunk_bbox" in row or "m1_landing_bbox" in row or "m2_landing_bbox" in row]),
        "via1_count": via1_count,
        "total_signal_wire_length": round(total_signal_length, 6),
        "maximum_route_length": round(maximum_route_length, 6),
        "cross_row_route_count": cross_row_route_count,
        "off_grid_count": off_grid_count,
        "pin_access_clearance": min(float(item.placed_pin_map["A"][0]["lx"]) for item in placed_children[1:]) - max(float(item.placed_pin_map["Z"][0]["rx"]) for item in placed_children[:-1]) if len(placed_children) > 1 else 0.0,
    }
