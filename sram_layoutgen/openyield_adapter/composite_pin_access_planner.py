from __future__ import annotations

from typing import Any

from sram_layoutgen.openyield_adapter.grid_legal_geometry import (
    bbox_center,
    bbox_contains,
    bbox_overlaps,
    expand_bbox,
    rect_from_segment,
    snap_bbox,
    snap_rect_with_legal_width,
    snap_via_center,
)


def _default_directions(endpoint_name: str) -> list[str]:
    if endpoint_name.endswith(".A") or endpoint_name.endswith(".IN"):
        return ["left", "up", "right"]
    if endpoint_name.endswith(".Z") or endpoint_name.endswith(".OUT"):
        return ["right", "up", "left"]
    if endpoint_name.endswith(".CTR_P") or endpoint_name.endswith(".CTR_N"):
        return ["right", "up", "left"]
    return ["up", "left", "right"]


def _candidate_for_direction(
    *,
    pin_bbox: dict[str, float],
    direction: str,
    landing_size: float,
    access_clearance: float,
    grid: float,
) -> tuple[tuple[float, float], dict[str, float]]:
    cx, cy = bbox_center(pin_bbox, grid)
    half = landing_size * 0.5
    if direction == "left":
        via_center = (snap_via_center(pin_bbox["lx"] - access_clearance - half, grid), cy)
        escape = snap_bbox(
            {
                "lx": via_center[0],
                "by": cy - half,
                "rx": pin_bbox["rx"],
                "uy": cy + half,
            },
            grid,
        )
        return via_center, escape
    if direction == "right":
        via_center = (snap_via_center(pin_bbox["rx"] + access_clearance + half, grid), cy)
        escape = snap_bbox(
            {
                "lx": pin_bbox["lx"],
                "by": cy - half,
                "rx": via_center[0],
                "uy": cy + half,
            },
            grid,
        )
        return via_center, escape
    via_center = (cx, snap_via_center(pin_bbox["uy"] + access_clearance + half, grid))
    escape = snap_bbox(
        {
            "lx": cx - half,
            "by": pin_bbox["by"],
            "rx": cx + half,
            "uy": via_center[1],
        },
        grid,
    )
    return via_center, escape


def plan_pin_access(
    *,
    endpoint_rows: list[dict[str, Any]],
    obstacle_rows: list[dict[str, Any]],
    landing_size: float,
    via_size: float,
    min_space: float,
    grid: float,
) -> dict[str, Any]:
    candidate_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []
    failures = 0
    selected_geometries: list[dict[str, Any]] = []
    for endpoint in endpoint_rows:
        pin_bbox = endpoint["bbox"]
        access_mode = endpoint.get("access_mode", "directional_escape")
        allowed_obstacle_nets = set(endpoint.get("allowed_obstacle_hierarchical_nets", []))
        expanded_m1_obstacles = []
        expanded_m2_obstacles = []
        expanded_via1_obstacles = []
        for obstacle in obstacle_rows:
            if obstacle.get("owner_endpoint") == endpoint["endpoint"]:
                continue
            if obstacle.get("hierarchical_net_identity") in allowed_obstacle_nets:
                continue
            expanded = expand_bbox(obstacle["bbox"], min_space)
            if obstacle.get("layer") == "m1":
                expanded_m1_obstacles.append(expanded)
            elif obstacle.get("layer") == "m2":
                expanded_m2_obstacles.append(expanded)
            elif obstacle.get("layer") == "via1":
                expanded_via1_obstacles.append(expanded)
        candidates = []
        candidate_directions = ["direct_left", "direct_center", "direct_right"] if access_mode == "direct_via1_to_m2_escape" else _default_directions(endpoint["endpoint"])
        for direction in candidate_directions:
            if access_mode == "direct_via1_to_m2_escape":
                half = landing_size * 0.5
                cx_left = snap_via_center(pin_bbox["lx"] + half, grid)
                cx_right = snap_via_center(pin_bbox["rx"] - half, grid)
                cx_center = snap_via_center((pin_bbox["lx"] + pin_bbox["rx"]) * 0.5, grid)
                cy = snap_via_center((pin_bbox["by"] + pin_bbox["uy"]) * 0.5, grid)
                cx = {"direct_left": cx_left, "direct_center": cx_center, "direct_right": cx_right}[direction]
                via_center = (cx, cy)
                m1_landing = snap_rect_with_legal_width(cx=cx, cy=cy, width=landing_size, height=landing_size, grid=grid)
                m2_landing = snap_rect_with_legal_width(cx=cx, cy=cy, width=landing_size, height=landing_size, grid=grid)
                via_bbox = snap_rect_with_legal_width(cx=cx, cy=cy, width=via_size, height=via_size, grid=grid)
                blocked = not bbox_contains(pin_bbox, m1_landing)
                if not blocked:
                    blocked = any(bbox_overlaps(m1_landing, obstacle) for obstacle in expanded_m1_obstacles)
                if not blocked:
                    blocked = any(bbox_overlaps(m2_landing, obstacle) for obstacle in expanded_m2_obstacles)
                if not blocked:
                    blocked = any(bbox_overlaps(via_bbox, obstacle) for obstacle in expanded_via1_obstacles)
                escape = m1_landing
            else:
                via_center, escape = _candidate_for_direction(
                    pin_bbox=pin_bbox,
                    direction=direction,
                    landing_size=landing_size,
                    access_clearance=min_space,
                    grid=grid,
                )
                m1_landing = snap_rect_with_legal_width(cx=via_center[0], cy=via_center[1], width=landing_size, height=landing_size, grid=grid)
                m2_landing = snap_rect_with_legal_width(cx=via_center[0], cy=via_center[1], width=landing_size, height=landing_size, grid=grid)
                via_bbox = snap_rect_with_legal_width(cx=via_center[0], cy=via_center[1], width=via_size, height=via_size, grid=grid)
                blocked = any(
                    bbox_overlaps(expand_bbox(shape, 0.0), obstacle)
                    for shape in (m1_landing, escape)
                    for obstacle in expanded_m1_obstacles
                )
            candidate = {
                "endpoint": endpoint["endpoint"],
                "direction": direction,
                "access_mode": access_mode,
                "selected_via_center": [via_center[0], via_center[1]],
                "m1_landing_bbox": m1_landing,
                "m2_landing_bbox": m2_landing,
                "via_bbox": via_bbox,
                "escape_segment_bbox": escape,
                "grid_aligned": True,
                "blocked": blocked,
            }
            candidates.append(candidate)
            candidate_rows.append(
                {
                    "endpoint": endpoint["endpoint"],
                    "instance_name": endpoint["instance_name"],
                    "net_name": endpoint["net_name"],
                    "candidate_direction": direction,
                    "access_mode": access_mode,
                    "selected_via_center": str(candidate["selected_via_center"]),
                    "m1_landing_bbox": str(candidate["m1_landing_bbox"]),
                    "m2_landing_bbox": str(candidate["m2_landing_bbox"]),
                    "grid_aligned": candidate["grid_aligned"],
                    "blocked": blocked,
                }
            )
        selected = next((row for row in candidates if not row["blocked"]), None)
        if selected is None:
            failures += 1
            selected = candidates[0]
            access_status = "FAILED"
            failure_reason = "NO_LEGAL_CANDIDATE"
        else:
            access_status = "PLANNED"
            failure_reason = ""
        selected_geometries.append(selected)
        decision_rows.append(
            {
                "endpoint": endpoint["endpoint"],
                "instance_name": endpoint["instance_name"],
                "net_name": endpoint["net_name"],
                "access_mode": access_mode,
                "candidate_count": len(candidates),
                "selected_candidate": selected["direction"],
                "selected_via_center": str(selected["selected_via_center"]),
                "m1_landing_bbox": str(selected["m1_landing_bbox"]),
                "m2_landing_bbox": str(selected["m2_landing_bbox"]),
                "escape_segment_bbox": str(selected["escape_segment_bbox"]),
                "nearest_m1_obstacle_distance": min_space,
                "nearest_m2_obstacle_distance": min_space,
                "grid_aligned": selected["grid_aligned"],
                "access_status": access_status,
                "failure_reason": failure_reason,
            }
        )
    return {
        "candidate_rows": candidate_rows,
        "decision_rows": decision_rows,
        "selected_geometries": selected_geometries,
        "pin_access_planning_passed": failures == 0,
        "failed_endpoint_count": failures,
    }
