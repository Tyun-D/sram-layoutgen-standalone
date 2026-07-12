from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gdstk
from sram_layoutgen.tech import Tech


def _snap(value: float, grid: float) -> float:
    return round(round(value / grid) * grid, 6)


def _center(pin: dict[str, float]) -> tuple[float, float]:
    return (round((pin["lx"] + pin["rx"]) * 0.5, 6), round((pin["by"] + pin["uy"]) * 0.5, 6))


def _landing_bbox(cx: float, cy: float, size: float) -> dict[str, float]:
    half = size * 0.5
    return {"lx": cx - half, "by": cy - half, "rx": cx + half, "uy": cy + half}


def _add_rect(cell: gdstk.Cell, bbox: dict[str, float], layer: int, datatype: int = 0) -> None:
    cell.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=layer, datatype=datatype))


def _segment_rect(start: tuple[float, float], end: tuple[float, float], width: float) -> dict[str, float]:
    if abs(start[0] - end[0]) <= 1e-6:
        half = width * 0.5
        return {
            "lx": start[0] - half,
            "by": min(start[1], end[1]),
            "rx": start[0] + half,
            "uy": max(start[1], end[1]),
        }
    half = width * 0.5
    return {
        "lx": min(start[0], end[0]),
        "by": start[1] - half,
        "rx": max(start[0], end[0]),
        "uy": start[1] + half,
    }


def generate_dff_signal_routes(
    *,
    top: gdstk.Cell,
    tech: Tech,
    endpoints_by_net: dict[str, list[dict[str, Any]]],
    top_pin_pads: dict[str, dict[str, float]],
    row_top_y: float,
) -> dict[str, Any]:
    via_rule = tech.via_between("m1", "m2")
    assert via_rule is not None
    grid = tech.manufacturing_grid
    m1_width = tech.layer("m1").min_width
    m2_width = tech.layer("m2").min_width
    landing = _snap(via_rule.size + 2 * via_rule.enclosure, grid)
    nets = ["CLK", "CLKB", "D", "D_b", "z1", "z2", "z3", "z4", "z5", "Q", "QB"]
    base_y = _snap(row_top_y + 0.35, grid)
    trunk_pitch = _snap(max(tech.layer("m2").pitch, 0.16), grid)

    route_segments: list[dict[str, Any]] = []
    vias: list[dict[str, Any]] = []
    route_graph: dict[str, list[dict[str, Any]]] = {"nets": []}

    for order, net_name in enumerate(nets):
        endpoints = endpoints_by_net[net_name]
        trunk_y = _snap(base_y + order * trunk_pitch, grid)
        xs: list[float] = []
        for endpoint in endpoints:
            pin = endpoint["bbox"]
            cx, cy = _center(pin)
            escape_center_x = cx
            if endpoint.get("m1_escape") == "left":
                escape_center_x = _snap(pin["lx"] - landing * 0.5, grid)
                _add_rect(
                    top,
                    {
                        "lx": escape_center_x,
                        "by": cy - m1_width * 0.5,
                        "rx": pin["rx"],
                        "uy": cy + m1_width * 0.5,
                    },
                    11,
                    0,
                )
            elif endpoint.get("m1_escape") == "right":
                escape_center_x = _snap(pin["rx"] + landing * 0.5, grid)
                _add_rect(
                    top,
                    {
                        "lx": pin["lx"],
                        "by": cy - m1_width * 0.5,
                        "rx": escape_center_x,
                        "uy": cy + m1_width * 0.5,
                    },
                    11,
                    0,
                )
            cx = escape_center_x
            xs.append(cx)
            landing_box = _landing_bbox(cx, cy, landing)
            _add_rect(top, landing_box, 11, 0)
            via_box = _landing_bbox(cx, cy, via_rule.size)
            _add_rect(top, via_box, 12, 0)
            _add_rect(top, landing_box, 13, 0)
            if abs(trunk_y - cy) > 1e-6:
                vertical_start_y = cy + landing * 0.5 if trunk_y > cy else cy - landing * 0.5
                _add_rect(top, _segment_rect((cx, vertical_start_y), (cx, trunk_y), m2_width), 13, 0)
                route_segments.append(
                    {
                        "net_name": net_name,
                        "layer": "m2",
                        "start": [cx, vertical_start_y],
                        "end": [cx, trunk_y],
                        "width": m2_width,
                        "source_pin": endpoint["endpoint_name"],
                        "destination_pin": f"{net_name}_TRUNK",
                        "obstacle_clearance": tech.layer("m2").min_space,
                        "route_order": order,
                        "geometry_id": f"{net_name}_drop_{endpoint['endpoint_name']}",
                    }
                )
            vias.append({"net_name": net_name, "x": cx, "y": cy, "size": via_rule.size, "landing": landing, "route_order": order})

        if net_name in top_pin_pads:
            pad = top_pin_pads[net_name]
            cx, cy = _center(pad)
            xs.append(cx)
            landing_box = _landing_bbox(cx, cy, landing)
            _add_rect(top, landing_box, 11, 0)
            via_box = _landing_bbox(cx, cy, via_rule.size)
            _add_rect(top, via_box, 12, 0)
            _add_rect(top, landing_box, 13, 0)
            vertical_start_y = cy + landing * 0.5 if trunk_y > cy else cy - landing * 0.5
            _add_rect(top, _segment_rect((cx, vertical_start_y), (cx, trunk_y), m2_width), 13, 0)
            route_segments.append(
                {
                    "net_name": net_name,
                    "layer": "m2",
                    "start": [cx, vertical_start_y],
                    "end": [cx, trunk_y],
                    "width": m2_width,
                    "source_pin": f"TOP.{net_name}",
                    "destination_pin": f"{net_name}_TRUNK",
                    "obstacle_clearance": tech.layer("m2").min_space,
                    "route_order": order,
                    "geometry_id": f"{net_name}_top_drop",
                }
            )
            vias.append({"net_name": net_name, "x": cx, "y": cy, "size": via_rule.size, "landing": landing, "route_order": order})

        trunk_lx = _snap(min(xs), grid)
        trunk_rx = _snap(max(xs), grid)
        _add_rect(top, _segment_rect((trunk_lx, trunk_y), (trunk_rx, trunk_y), m2_width), 13, 0)
        route_segments.append(
            {
                "net_name": net_name,
                "layer": "m2",
                "start": [trunk_lx, trunk_y],
                "end": [trunk_rx, trunk_y],
                "width": m2_width,
                "source_pin": f"{net_name}_TRUNK_START",
                "destination_pin": f"{net_name}_TRUNK_END",
                "obstacle_clearance": tech.layer("m2").min_space,
                "route_order": order,
                "geometry_id": f"{net_name}_trunk",
            }
        )
        route_graph["nets"].append({"net_name": net_name, "trunk_y": trunk_y, "endpoint_count": len(endpoints) + (1 if net_name in top_pin_pads else 0)})

    return {
        "route_segments": route_segments,
        "vias": vias,
        "route_graph": route_graph,
    }


def write_route_outputs(
    *,
    route_plan: dict[str, Any],
    plan_json_path: Path,
    plan_md_path: Path,
    segment_csv_path: Path,
    via_csv_path: Path,
    route_graph_path: Path,
) -> None:
    import csv

    route_graph_path.write_text(json.dumps(route_plan["route_graph"], indent=2) + "\n", encoding="utf-8")
    plan_json_path.write_text(
        json.dumps(
            {
                "route_segment_count": len(route_plan["route_segments"]),
                "via1_count": len(route_plan["vias"]),
                "m1_route_count": 0,
                "m2_route_count": len(route_plan["route_segments"]),
                "route_graph_path": str(route_graph_path),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    plan_md_path.write_text(
        "\n".join(
            [
                "# M12C4A DFF Route Plan",
                "",
                f"- route_segment_count: `{len(route_plan['route_segments'])}`",
                f"- via1_count: `{len(route_plan['vias'])}`",
                "",
            ]
        ),
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
