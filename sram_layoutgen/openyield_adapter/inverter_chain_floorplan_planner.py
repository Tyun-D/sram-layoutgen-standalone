from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Placement:
    instance_name: str
    x: float
    y: float
    orientation: str = "R0"


def _width(bbox: list[float]) -> float:
    return round(float(bbox[2]) - float(bbox[0]), 6)


def _height(bbox: list[float]) -> float:
    return round(float(bbox[3]) - float(bbox[1]), 6)


def _bbox_area(child_bboxes: dict[str, list[float]], placements: list[Placement]) -> float:
    min_x = min(placement.x for placement in placements)
    min_y = min(placement.y for placement in placements)
    max_x = max(placement.x + _width(child_bboxes[placement.instance_name]) for placement in placements)
    max_y = max(placement.y + _height(child_bboxes[placement.instance_name]) for placement in placements)
    return round((max_x - min_x) * (max_y - min_y), 6)


def build_inverter_chain_floorplan_candidates(*, module_name: str, child_bboxes: dict[str, list[float]]) -> dict[str, Any]:
    instance_order = list(child_bboxes.keys())
    widths = [_width(child_bboxes[name]) for name in instance_order]
    heights = [_height(child_bboxes[name]) for name in instance_order]
    row_h = max(heights)
    h_gap = 0.35
    channel_gap = 0.65
    v_gap = 0.95
    stagger_step = 0.28
    rows: list[dict[str, Any]] = []

    single_row = []
    cursor = 0.0
    for name, width in zip(instance_order, widths):
        single_row.append(Placement(name, cursor, 0.0))
        cursor = round(cursor + width + h_gap, 6)
    rows.append(
        {
            "architecture": "single_row_left_to_right",
            "placements": [item.__dict__ for item in single_row],
            "estimated_signal_wire_length": round(sum(widths) + h_gap * (len(widths) - 1), 6),
            "maximum_route_length_estimate": round(max(widths) + h_gap + 0.65, 6),
            "cross_row_route_count_estimate": 0,
            "bbox_area_estimate": _bbox_area(child_bboxes, single_row),
            "selection_reason_hint": "Small-to-large source order with the shortest direct stage-to-stage travel.",
        }
    )

    routing_channel = []
    cursor = 0.0
    for index, (name, width) in enumerate(zip(instance_order, widths)):
        routing_channel.append(Placement(name, cursor, 0.0 if index % 2 == 0 else 0.10))
        cursor = round(cursor + width + channel_gap, 6)
    rows.append(
        {
            "architecture": "single_row_with_routing_channel",
            "placements": [item.__dict__ for item in routing_channel],
            "estimated_signal_wire_length": round(sum(widths) + channel_gap * (len(widths) - 1), 6),
            "maximum_route_length_estimate": round(max(widths) + channel_gap + 0.95, 6),
            "cross_row_route_count_estimate": 0,
            "bbox_area_estimate": _bbox_area(child_bboxes, routing_channel),
            "selection_reason_hint": "Preserves source order but leaves a larger deterministic inter-stage routing corridor.",
        }
    )

    split = (len(instance_order) + 1) // 2
    top_row = instance_order[:split]
    bot_row = list(reversed(instance_order[split:]))
    two_row: list[Placement] = []
    cursor = 0.0
    for name in top_row:
        two_row.append(Placement(name, cursor, row_h + v_gap))
        cursor = round(cursor + _width(child_bboxes[name]) + h_gap, 6)
    cursor = 0.0
    for name in bot_row:
        two_row.append(Placement(name, cursor, 0.0))
        cursor = round(cursor + _width(child_bboxes[name]) + h_gap, 6)
    rows.append(
        {
            "architecture": "two_row_serpentine",
            "placements": [item.__dict__ for item in two_row],
            "estimated_signal_wire_length": round(sum(widths) + h_gap * (len(widths) - 1) + v_gap, 6),
            "maximum_route_length_estimate": round(max(widths) + h_gap + row_h + v_gap, 6),
            "cross_row_route_count_estimate": max(1, len(bot_row)),
            "bbox_area_estimate": _bbox_area(child_bboxes, two_row),
            "selection_reason_hint": "Reduces total width when the largest stage dominates the row span.",
        }
    )

    size_aware = []
    cursor = 0.0
    for index, (name, width) in enumerate(zip(instance_order, widths)):
        size_aware.append(Placement(name, cursor, 0.0 if index % 2 == 0 else stagger_step))
        cursor = round(cursor + width + h_gap, 6)
    rows.append(
        {
            "architecture": "size_aware_staggered",
            "placements": [item.__dict__ for item in size_aware],
            "estimated_signal_wire_length": round(sum(widths) + h_gap * (len(widths) - 1) + stagger_step * (len(widths) // 2), 6),
            "maximum_route_length_estimate": round(max(widths) + h_gap + stagger_step + 0.85, 6),
            "cross_row_route_count_estimate": 0,
            "bbox_area_estimate": _bbox_area(child_bboxes, size_aware),
            "selection_reason_hint": "Creates local vertical breathing room near the larger downstream stages.",
        }
    )
    return {"module_name": module_name, "candidate_count": len(rows), "rows": rows}


def select_inverter_chain_floorplan(*, candidate_payload: dict[str, Any], trial_rows: list[dict[str, Any]]) -> dict[str, Any]:
    def sort_key(row: dict[str, Any]) -> tuple[int, int, int, int, float, float, int]:
        return (
            0 if row["connectivity_passed"] else 1,
            int(row["drc_marker_count"]),
            0 if row["rail_continuity"] else 1,
            int(row["off_grid_count"]),
            float(row["maximum_route_length"]),
            float(row["area"]),
            int(row["cross_row_route_count"]),
        )

    selected_trial = sorted(trial_rows, key=sort_key)[0]
    selected_arch = selected_trial["architecture"]
    selected_row = next(row for row in candidate_payload["rows"] if row["architecture"] == selected_arch)
    return {
        "module_name": candidate_payload["module_name"],
        "candidate_count": candidate_payload["candidate_count"],
        "rows": candidate_payload["rows"],
        "trial_rows": trial_rows,
        "selected_architecture": selected_arch,
        "selected_trial": selected_trial,
        "selected_placements": selected_row["placements"],
    }


def write_floorplan_outputs(*, payload: dict[str, Any], candidates_path: Path, selected_path: Path) -> None:
    candidates_path.parent.mkdir(parents=True, exist_ok=True)
    candidates_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    selected_path.write_text(
        json.dumps(
            {
                "selected_architecture": payload["selected_architecture"],
                "selected_trial": payload["selected_trial"],
                "selected_placements": payload["selected_placements"],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
