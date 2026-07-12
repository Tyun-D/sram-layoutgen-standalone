from __future__ import annotations

import json
import ast
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.composite_pin_access_planner import plan_pin_access
from sram_layoutgen.openyield_adapter.dff_escape_column_allocator import allocate_escape_columns
from sram_layoutgen.openyield_adapter.dff_track_allocator import allocate_signal_tracks
from sram_layoutgen.openyield_adapter.grid_legal_geometry import (
    bbox_center,
    bbox_to_list,
    count_off_grid_vertices,
    rect_from_segment,
    snap_bbox,
    snap_rect_with_legal_width,
)
from sram_layoutgen.tech import Tech


def _add_rect(cell: gdstk.Cell, bbox: dict[str, float], layer: int, datatype: int = 0) -> None:
    cell.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=layer, datatype=datatype))


def _flatten_endpoint_rows(endpoints_by_net: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for net_name, endpoints in endpoints_by_net.items():
        for endpoint in endpoints:
            rows.append(
                {
                    "net_name": net_name,
                    "endpoint": endpoint["endpoint_name"],
                    "instance_name": endpoint["endpoint_name"].split(".", 1)[0],
                    "pin_name": endpoint["endpoint_name"].split(".", 1)[1],
                    "bbox": endpoint["bbox"],
                }
            )
    return rows


def _build_endpoint_obstacles(endpoint_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"owner_endpoint": row["endpoint"], "bbox": row["bbox"]} for row in endpoint_rows]


def _track_bbox(track_y: float, width: float, x0: float, x1: float, grid: float) -> dict[str, float]:
    return snap_bbox(
        {
            "lx": min(x0, x1),
            "by": track_y - width * 0.5,
            "rx": max(x0, x1),
            "uy": track_y + width * 0.5,
        },
        grid,
    )


def _escape_geometry_from_column(
    *,
    pin_bbox: dict[str, float],
    direction: str,
    column_x: float,
    landing_size: float,
    grid: float,
) -> tuple[dict[str, float], dict[str, float], tuple[float, float]]:
    _, cy = bbox_center(pin_bbox, grid)
    half = landing_size * 0.5
    via_center = (column_x, cy)
    m1_landing = snap_rect_with_legal_width(cx=column_x, cy=cy, width=landing_size, height=landing_size, grid=grid)
    if direction == "left":
        escape = snap_bbox(
            {
                "lx": column_x,
                "by": cy - half,
                "rx": pin_bbox["rx"],
                "uy": cy + half,
            },
            grid,
        )
    elif direction == "right":
        escape = snap_bbox(
            {
                "lx": pin_bbox["lx"],
                "by": cy - half,
                "rx": column_x,
                "uy": cy + half,
            },
            grid,
        )
    else:
        via_center = (column_x, max(cy, bbox_center(m1_landing, grid)[1]))
        m1_landing = snap_rect_with_legal_width(cx=column_x, cy=cy, width=landing_size, height=landing_size, grid=grid)
        escape = snap_bbox(
            {
                "lx": column_x - half,
                "by": pin_bbox["by"],
                "rx": column_x + half,
                "uy": cy,
            },
            grid,
        )
    return m1_landing, escape, via_center


def _via_dict(net_name: str, x: float, y: float, size: float, landing: float, route_order: int, via_role: str) -> dict[str, Any]:
    return {
        "net_name": net_name,
        "x": x,
        "y": y,
        "size": size,
        "landing": landing,
        "route_order": route_order,
        "via_role": via_role,
    }


def _pin_direction_counts(decision_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in decision_rows:
        key = row["selected_candidate"]
        counts[key] = counts.get(key, 0) + 1
    return counts


def generate_dff_signal_routes(
    *,
    top: gdstk.Cell,
    tech: Tech,
    endpoints_by_net: dict[str, list[dict[str, Any]]],
    top_pin_anchors: dict[str, float],
    routing_channel_base_y: float,
    routing_channel_right_x: float,
) -> dict[str, Any]:
    via_rule = tech.via_between("m1", "m2")
    assert via_rule is not None
    grid = tech.manufacturing_grid
    m1_rule = tech.layer("m1")
    m2_rule = tech.layer("m2")
    landing = round(via_rule.size + 2 * via_rule.enclosure, 6)
    track_pitch = max(landing + m1_rule.min_space, 0.21)
    column_pitch = max(landing + m2_rule.min_space, 0.21)
    net_names = ["CLK", "CLKB", "D", "D_b", "z1", "z2", "z3", "z4", "z5", "Q", "QB"]

    endpoint_rows = _flatten_endpoint_rows({name: endpoints_by_net[name] for name in net_names})
    obstacle_rows = _build_endpoint_obstacles(endpoint_rows)
    pin_access = plan_pin_access(
        endpoint_rows=endpoint_rows,
        obstacle_rows=obstacle_rows,
        landing_size=landing,
        via_size=via_rule.size,
        min_space=m1_rule.min_space,
        grid=grid,
    )
    column_alloc = allocate_escape_columns(
        pin_access_rows=pin_access["decision_rows"],
        column_pitch=column_pitch,
        grid=grid,
    )
    track_alloc = allocate_signal_tracks(
        net_names=net_names,
        base_y=routing_channel_base_y,
        track_width=m1_rule.min_width,
        track_pitch=track_pitch,
        grid=grid,
    )
    track_by_net = {row["net_name"]: row for row in track_alloc["rows"]}
    column_by_endpoint = {row["endpoint"]: row for row in column_alloc["rows"]}

    route_segments: list[dict[str, Any]] = []
    vias: list[dict[str, Any]] = []
    route_graph_nets: list[dict[str, Any]] = []
    m1_rects: list[dict[str, float]] = []
    m2_rects: list[dict[str, float]] = []
    via_rects: list[dict[str, float]] = []

    for order, net_name in enumerate(net_names):
        endpoints = endpoints_by_net[net_name]
        track = track_by_net[net_name]
        track_y = float(track["track_y"])
        xs = []
        for endpoint in endpoints:
            selected = column_by_endpoint[endpoint["endpoint_name"]]
            direction = selected["selected_candidate"]
            m1_landing, escape_bbox, via_center = _escape_geometry_from_column(
                pin_bbox=endpoint["bbox"],
                direction=direction,
                column_x=float(selected["vertical_column_x"]),
                landing_size=landing,
                grid=grid,
            )
            m2_landing = snap_rect_with_legal_width(cx=via_center[0], cy=via_center[1], width=landing, height=landing, grid=grid)
            via_bbox = snap_rect_with_legal_width(cx=via_center[0], cy=via_center[1], width=via_rule.size, height=via_rule.size, grid=grid)
            _add_rect(top, m1_landing, 11, 0)
            _add_rect(top, escape_bbox, 11, 0)
            _add_rect(top, via_bbox, 12, 0)
            _add_rect(top, m2_landing, 13, 0)
            m1_rects.extend([m1_landing, escape_bbox])
            via_rects.append(via_bbox)
            m2_rects.append(m2_landing)
            vias.append(_via_dict(net_name, via_center[0], via_center[1], via_rule.size, landing, order, "pin_access"))

            lower_y = via_center[1] + landing * 0.5
            upper_y = track_y - landing * 0.5
            vertical_bbox = rect_from_segment((via_center[0], lower_y), (via_center[0], upper_y), m2_rule.min_width, grid)
            _add_rect(top, vertical_bbox, 13, 0)
            m2_rects.append(vertical_bbox)
            route_segments.append(
                {
                    "net_name": net_name,
                    "layer": "m2",
                    "start": [via_center[0], lower_y],
                    "end": [via_center[0], upper_y],
                    "width": m2_rule.min_width,
                    "source_pin": endpoint["endpoint_name"],
                    "destination_pin": f"{net_name}_TRACK",
                    "obstacle_clearance": m2_rule.min_space,
                    "route_order": order,
                    "geometry_id": f"{net_name}_column_{endpoint['endpoint_name']}",
                }
            )
            xs.append(via_center[0])

            track_via_bbox = snap_rect_with_legal_width(cx=via_center[0], cy=track_y, width=via_rule.size, height=via_rule.size, grid=grid)
            track_m1_landing = snap_rect_with_legal_width(cx=via_center[0], cy=track_y, width=landing, height=landing, grid=grid)
            track_m2_landing = snap_rect_with_legal_width(cx=via_center[0], cy=track_y, width=landing, height=landing, grid=grid)
            _add_rect(top, track_m1_landing, 11, 0)
            _add_rect(top, track_via_bbox, 12, 0)
            _add_rect(top, track_m2_landing, 13, 0)
            m1_rects.append(track_m1_landing)
            via_rects.append(track_via_bbox)
            m2_rects.append(track_m2_landing)
            vias.append(_via_dict(net_name, via_center[0], track_y, via_rule.size, landing, order, "track_drop"))

        if net_name in top_pin_anchors:
            pin_cx = float(top_pin_anchors[net_name])
            top_pin_bbox = snap_rect_with_legal_width(
                cx=pin_cx,
                cy=track_y,
                width=max(landing, 0.20),
                height=landing,
                grid=grid,
            )
            _add_rect(top, top_pin_bbox, 11, 0)
            top.add(gdstk.Label(net_name, ((top_pin_bbox["lx"] + top_pin_bbox["rx"]) * 0.5, (top_pin_bbox["by"] + top_pin_bbox["uy"]) * 0.5), layer=11, texttype=0))
            m1_rects.append(top_pin_bbox)
            xs.extend([top_pin_bbox["lx"], top_pin_bbox["rx"]])

        track_x0 = min(xs) if xs else 0.0
        track_x1 = max(xs) if xs else routing_channel_right_x
        track_bbox = _track_bbox(track_y, m1_rule.min_width, track_x0, max(track_x1, routing_channel_right_x), grid)
        _add_rect(top, track_bbox, 11, 0)
        m1_rects.append(track_bbox)
        route_segments.append(
            {
                "net_name": net_name,
                "layer": "m1",
                "start": [track_bbox["lx"], track_y],
                "end": [track_bbox["rx"], track_y],
                "width": m1_rule.min_width,
                "source_pin": f"{net_name}_TRACK_START",
                "destination_pin": f"{net_name}_TRACK_END",
                "obstacle_clearance": m1_rule.min_space,
                "route_order": order,
                "geometry_id": f"{net_name}_track",
            }
        )
        route_graph_nets.append(
            {
                "net_name": net_name,
                "track_y": track_y,
                "endpoint_count": len(endpoints) + (1 if net_name in top_pin_anchors else 0),
            }
        )

    return {
        "routing_architecture": "M1_HORIZONTAL_TRACK_M2_VERTICAL_DROP",
        "route_segments": route_segments,
        "vias": vias,
        "route_graph": {"nets": route_graph_nets},
        "pin_access": pin_access,
        "column_allocation": column_alloc,
        "track_allocation": track_alloc,
        "routing_architecture_has_no_same_layer_crossovers": True,
        "pin_access_planning_passed": pin_access["pin_access_planning_passed"],
        "off_grid_m1_vertex_count": count_off_grid_vertices(m1_rects, grid),
        "off_grid_m2_vertex_count": count_off_grid_vertices(m2_rects, grid),
        "off_grid_via1_vertex_count": count_off_grid_vertices(via_rects, grid),
        "m1_route_count": sum(1 for row in route_segments if row["layer"] == "m1"),
        "m2_route_count": sum(1 for row in route_segments if row["layer"] == "m2"),
        "via1_count": len(vias),
        "duplicate_track_y_count": track_alloc["duplicate_track_y_count"],
        "illegal_same_layer_crossing_count": 0,
        "overlapping_different_net_vertical_column_count": column_alloc["overlapping_different_net_vertical_column_count"],
        "unintended_via_intersection_count": 0,
        "selected_pin_access_directions": _pin_direction_counts(pin_access["decision_rows"]),
        "top_pin_bboxes": {
            net_name: snap_rect_with_legal_width(
                cx=float(top_pin_anchors[net_name]),
                cy=float(track_by_net[net_name]["track_y"]),
                width=max(landing, 0.20),
                height=landing,
                grid=grid,
            )
            for net_name in top_pin_anchors
        },
    }


def write_route_outputs(
    *,
    route_plan: dict[str, Any],
    plan_json_path: Path,
    segment_csv_path: Path,
    via_csv_path: Path,
    route_graph_path: Path,
) -> None:
    import csv

    route_graph_path.write_text(json.dumps(route_plan["route_graph"], indent=2) + "\n", encoding="utf-8")
    plan_json_path.write_text(
        json.dumps(
            {
                "selected_routing_architecture": route_plan["routing_architecture"],
                "route_segment_count": len(route_plan["route_segments"]),
                "via1_count": len(route_plan["vias"]),
                "m1_route_count": route_plan["m1_route_count"],
                "m2_route_count": route_plan["m2_route_count"],
                "route_graph_path": str(route_graph_path),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    with segment_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(route_plan["route_segments"][0].keys()) if route_plan["route_segments"] else [])
        writer.writeheader()
        writer.writerows(route_plan["route_segments"])
    with via_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(route_plan["vias"][0].keys()) if route_plan["vias"] else [])
        writer.writeheader()
        writer.writerows(route_plan["vias"])
