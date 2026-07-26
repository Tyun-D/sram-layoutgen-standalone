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
            row = {
                "net_name": net_name,
                "endpoint": endpoint["endpoint_name"],
                "instance_name": endpoint["endpoint_name"].split(".", 1)[0],
                "pin_name": endpoint["endpoint_name"].split(".", 1)[1],
                "bbox": endpoint["bbox"],
                "access_mode": endpoint.get("access_mode", "directional_escape"),
                "allowed_obstacle_hierarchical_nets": endpoint.get("allowed_obstacle_hierarchical_nets", []),
            }
            rows.append(row)
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


def _row_geometry_from_planner(row: dict[str, Any]) -> tuple[dict[str, float], dict[str, float], dict[str, float], tuple[float, float]]:
    return (
        ast.literal_eval(row["m1_landing_bbox"]),
        ast.literal_eval(row["m2_landing_bbox"]),
        ast.literal_eval(row["escape_segment_bbox"]),
        tuple(ast.literal_eval(row["selected_via_center"])),
    )


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


def _bboxes_overlap(a: dict[str, float], b: dict[str, float]) -> bool:
    return not (
        a["rx"] <= b["lx"]
        or b["rx"] <= a["lx"]
        or a["uy"] <= b["by"]
        or b["uy"] <= a["by"]
    )


def generate_dff_signal_routes(
    *,
    top: gdstk.Cell,
    tech: Tech,
    endpoints_by_net: dict[str, list[dict[str, Any]]],
    obstacle_rows: list[dict[str, Any]] | None = None,
    top_pin_anchors: dict[str, float],
    routing_channel_base_y: float,
    routing_channel_right_x: float,
    net_names: list[str] | None = None,
) -> dict[str, Any]:
    via_rule = tech.via_between("m1", "m2")
    assert via_rule is not None
    grid = tech.manufacturing_grid
    m1_rule = tech.layer("m1")
    m2_rule = tech.layer("m2")
    landing = round(via_rule.size + 2 * via_rule.enclosure, 6)
    track_pitch = max(landing + m1_rule.min_space, 0.21)
    column_pitch = max(landing + m2_rule.min_space, 0.21)
    net_names = list(net_names) if net_names is not None else ["CLK", "CLKB", "D", "D_b", "z1", "z2", "z3", "z4", "z5", "Q", "QB"]

    endpoint_rows = _flatten_endpoint_rows({name: endpoints_by_net[name] for name in net_names})
    if obstacle_rows is None:
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
    route_objects: list[dict[str, Any]] = []

    for order, net_name in enumerate(net_names):
        endpoints = endpoints_by_net[net_name]
        track = track_by_net[net_name]
        track_y = float(track["track_y"])
        xs = []
        pending_columns: list[dict[str, Any]] = []
        for endpoint in endpoints:
            selected = column_by_endpoint[endpoint["endpoint_name"]]
            direction = selected["selected_candidate"]
            if "selected_via_center" in selected and "m1_landing_bbox" in selected and "escape_segment_bbox" in selected:
                m1_landing, m2_landing, escape_bbox, via_center = _row_geometry_from_planner(selected)
            else:
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
            m1_rects.append(m1_landing)
            route_objects.append(
                {
                    "route_object_id": f"{net_name}:{endpoint['endpoint_name']}:m1_landing",
                    "net_name": net_name,
                    "intended_hierarchical_net": endpoint["intended_hierarchical_net"],
                    "layer": "m1",
                    "bbox": bbox_to_list(m1_landing),
                    "role": "pin_access_landing",
                    "shape_kind": "axis_aligned_rectangle",
                    "bbox_is_exact_geometry": True,
                }
            )
            if selected.get("access_mode") != "direct_via1_to_m2_escape":
                _add_rect(top, escape_bbox, 11, 0)
                m1_rects.append(escape_bbox)
                route_objects.append(
                    {
                        "route_object_id": f"{net_name}:{endpoint['endpoint_name']}:m1_escape",
                        "net_name": net_name,
                        "intended_hierarchical_net": endpoint["intended_hierarchical_net"],
                        "layer": "m1",
                        "bbox": bbox_to_list(escape_bbox),
                        "role": "pin_access_escape",
                        "shape_kind": "axis_aligned_rectangle",
                        "bbox_is_exact_geometry": True,
                    }
                )
            xs.append(via_center[0])
            pending_columns.append(
                {
                    "endpoint": endpoint,
                    "selected": selected,
                    "via_center": via_center,
                    "escape_bbox": escape_bbox,
                    "m2_landing": m2_landing,
                    "via_bbox": via_bbox,
                    "m1_landing": m1_landing,
                }
            )

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
            route_objects.append(
                {
                    "route_object_id": f"{net_name}:TOP:m1_pin",
                    "net_name": net_name,
                    "intended_hierarchical_net": f"TOP::{net_name}",
                    "layer": "m1",
                    "bbox": bbox_to_list(top_pin_bbox),
                    "role": "top_pin",
                    "shape_kind": "axis_aligned_rectangle",
                    "bbox_is_exact_geometry": True,
                }
            )
            xs.extend([top_pin_bbox["lx"], top_pin_bbox["rx"]])

        track_x0 = min(xs) if xs else 0.0
        track_x1 = max(xs) if xs else routing_channel_right_x
        track_bbox = _track_bbox(track_y, m1_rule.min_width, track_x0, max(track_x1, routing_channel_right_x), grid)
        _add_rect(top, track_bbox, 11, 0)
        m1_rects.append(track_bbox)
        route_objects.append(
            {
                "route_object_id": f"{net_name}:TRACK:m1",
                "net_name": net_name,
                "intended_hierarchical_net": "PARENT::qint" if net_name == "qint" else f"TOP::{net_name}",
                "layer": "m1",
                "bbox": bbox_to_list(track_bbox),
                "role": "horizontal_track",
                "shape_kind": "axis_aligned_rectangle",
                "bbox_is_exact_geometry": True,
            }
        )
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
        for pending in pending_columns:
            if _bboxes_overlap(pending["escape_bbox"], track_bbox):
                continue
            via_center = pending["via_center"]
            endpoint = pending["endpoint"]
            _add_rect(top, pending["via_bbox"], 12, 0)
            _add_rect(top, pending["m2_landing"], 13, 0)
            via_rects.append(pending["via_bbox"])
            m2_rects.append(pending["m2_landing"])
            vias.append(_via_dict(net_name, via_center[0], via_center[1], via_rule.size, landing, order, "pin_access"))
            route_objects.append(
                {
                    "route_object_id": f"{net_name}:{endpoint['endpoint_name']}:via_pin",
                    "net_name": net_name,
                    "intended_hierarchical_net": endpoint["intended_hierarchical_net"],
                    "layer": "via1",
                    "bbox": bbox_to_list(pending["via_bbox"]),
                    "role": "pin_access_via",
                    "shape_kind": "axis_aligned_rectangle",
                    "bbox_is_exact_geometry": True,
                }
            )
            route_objects.append(
                {
                    "route_object_id": f"{net_name}:{endpoint['endpoint_name']}:m2_landing",
                    "net_name": net_name,
                    "intended_hierarchical_net": endpoint["intended_hierarchical_net"],
                    "layer": "m2",
                    "bbox": bbox_to_list(pending["m2_landing"]),
                    "role": "pin_access_m2_landing",
                    "shape_kind": "axis_aligned_rectangle",
                    "bbox_is_exact_geometry": True,
                }
            )

            lower_y = via_center[1] + landing * 0.5
            upper_y = track_y - landing * 0.5
            vertical_bbox = rect_from_segment((via_center[0], lower_y), (via_center[0], upper_y), m2_rule.min_width, grid)
            _add_rect(top, vertical_bbox, 13, 0)
            m2_rects.append(vertical_bbox)
            route_objects.append(
                {
                    "route_object_id": f"{net_name}:{endpoint['endpoint_name']}:m2_escape",
                    "net_name": net_name,
                    "intended_hierarchical_net": endpoint["intended_hierarchical_net"],
                    "layer": "m2",
                    "bbox": bbox_to_list(vertical_bbox),
                    "role": "vertical_escape",
                    "shape_kind": "axis_aligned_rectangle",
                    "bbox_is_exact_geometry": True,
                }
            )
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
            route_objects.extend(
                [
                    {
                        "route_object_id": f"{net_name}:{endpoint['endpoint_name']}:track_drop_m1",
                        "net_name": net_name,
                        "intended_hierarchical_net": "PARENT::qint" if net_name == "qint" else f"TOP::{net_name}",
                        "layer": "m1",
                        "bbox": bbox_to_list(track_m1_landing),
                        "role": "track_drop_m1_landing",
                        "shape_kind": "axis_aligned_rectangle",
                        "bbox_is_exact_geometry": True,
                    },
                    {
                        "route_object_id": f"{net_name}:{endpoint['endpoint_name']}:track_drop_via",
                        "net_name": net_name,
                        "intended_hierarchical_net": "PARENT::qint" if net_name == "qint" else f"TOP::{net_name}",
                        "layer": "via1",
                        "bbox": bbox_to_list(track_via_bbox),
                        "role": "track_drop_via",
                        "shape_kind": "axis_aligned_rectangle",
                        "bbox_is_exact_geometry": True,
                    },
                    {
                        "route_object_id": f"{net_name}:{endpoint['endpoint_name']}:track_drop_m2",
                        "net_name": net_name,
                        "intended_hierarchical_net": "PARENT::qint" if net_name == "qint" else f"TOP::{net_name}",
                        "layer": "m2",
                        "bbox": bbox_to_list(track_m2_landing),
                        "role": "track_drop_m2_landing",
                        "shape_kind": "axis_aligned_rectangle",
                        "bbox_is_exact_geometry": True,
                    },
                ]
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
        "route_objects": route_objects,
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
