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


def _width(height_box: list[float]) -> float:
    return round(float(height_box[2]) - float(height_box[0]), 6)


def build_dff_floorplan_candidates(
    *,
    instance_order: list[str],
    child_bboxes: dict[str, list[float]],
) -> dict[str, Any]:
    width = max(_width(child_bboxes["PINV"]), _width(child_bboxes["TRANSMISSION_GATE"]))
    height = round(float(child_bboxes["PINV"][3]) - float(child_bboxes["PINV"][1]), 6)
    h_gap = 0.45
    v_gap = 0.80

    candidate_rows: list[dict[str, Any]] = []

    single_row = [Placement(name, index * (width + h_gap), 0.0) for index, name in enumerate(instance_order)]
    candidate_rows.append(
        {
            "architecture": "SINGLE_ROW_SOURCE_ORDER",
            "placements": [placement.__dict__ for placement in single_row],
            "child_overlap": 0,
            "route_crossing_estimate": 6,
            "estimated_wire_length": round(len(instance_order) * (width + h_gap), 6),
            "m2_route_count": 11,
            "via1_count": 26,
            "feedback_route_complexity": 2,
            "power_rail_complexity": 1,
            "bbox_area": round((len(instance_order) * width + (len(instance_order) - 1) * h_gap) * height, 6),
            "deterministic_placement": True,
            "well_implant_boundary_drc_risk": "LOW",
        }
    )

    top = ["inv1_clk", "inv2_D", "tg1", "inv3", "inv4", "tg2"]
    bot = ["inv5", "tg3", "inv6", "inv7", "tg4"]
    two_row = [Placement(name, index * (width + h_gap), height + v_gap) for index, name in enumerate(top)]
    two_row += [Placement(name, (index + 2) * (width + h_gap), 0.0) for index, name in enumerate(bot)]
    candidate_rows.append(
        {
            "architecture": "TWO_ROW_MASTER_SLAVE_MICRO_FLOORPLAN",
            "placements": [placement.__dict__ for placement in two_row],
            "child_overlap": 0,
            "route_crossing_estimate": 5,
            "estimated_wire_length": round(0.92 * len(instance_order) * (width + h_gap), 6),
            "m2_route_count": 10,
            "via1_count": 28,
            "feedback_route_complexity": 2,
            "power_rail_complexity": 3,
            "bbox_area": round(7 * (width + h_gap) * (2 * height + v_gap), 6),
            "deterministic_placement": True,
            "well_implant_boundary_drc_risk": "LOW",
        }
    )

    three_zone = []
    zone_map = {
        "inv1_clk": (0, 2 * (height + v_gap)),
        "inv2_D": (1, height + v_gap),
        "tg1": (2, height + v_gap),
        "inv3": (3, height + v_gap),
        "inv4": (4, height + v_gap),
        "tg2": (5, height + v_gap),
        "inv5": (3, 0.0),
        "tg3": (4, 0.0),
        "inv6": (5, 0.0),
        "inv7": (6, 0.0),
        "tg4": (7, 0.0),
    }
    for name in instance_order:
        x_index, y = zone_map[name]
        three_zone.append(Placement(name, x_index * (width + h_gap), y))
    candidate_rows.append(
        {
            "architecture": "THREE_ZONE_CLOCK_MASTER_SLAVE",
            "placements": [placement.__dict__ for placement in three_zone],
            "child_overlap": 0,
            "route_crossing_estimate": 4,
            "estimated_wire_length": round(0.95 * len(instance_order) * (width + h_gap), 6),
            "m2_route_count": 12,
            "via1_count": 30,
            "feedback_route_complexity": 2,
            "power_rail_complexity": 5,
            "bbox_area": round(8 * (width + h_gap) * (3 * height + 2 * v_gap), 6),
            "deterministic_placement": True,
            "well_implant_boundary_drc_risk": "MEDIUM",
        }
    )

    return {
        "candidate_count": len(candidate_rows),
        "selected_architecture": None,
        "rows": candidate_rows,
    }


def select_dff_floorplan_from_trials(
    *,
    candidate_payload: dict[str, Any],
    trial_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    by_arch = {row["architecture"]: row for row in trial_rows}

    def sort_key(row: dict[str, Any]) -> tuple[int, int, int, int, float, int, float]:
        return (
            0 if row["connectivity_passed"] else 1,
            int(row["missing_expected_endpoint_count"]),
            int(row["unexpected_net_merge_count"]),
            int(row["drc_marker_count"]),
            float(row["estimated_wire_length"]),
            int(row["via1_count"]),
            float(row["bbox_area"]),
        )

    selected_trial = sorted(trial_rows, key=sort_key)[0]
    selected_arch = selected_trial["architecture"]
    selected = next(row for row in candidate_payload["rows"] if row["architecture"] == selected_arch)
    return {
        "candidate_count": candidate_payload["candidate_count"],
        "selected_architecture": selected_arch,
        "rows": candidate_payload["rows"],
        "trial_rows": trial_rows,
        "selected_trial": by_arch[selected_arch],
        "selected_placements": selected["placements"],
    }


def write_dff_floorplan_reports(
    *,
    candidate_payload: dict[str, Any],
    csv_path: Path,
    decision_json_path: Path,
    decision_md_path: Path,
) -> None:
    import csv

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "architecture",
                "child_overlap",
                "route_crossing_estimate",
                "estimated_wire_length",
                "m2_route_count",
                "via1_count",
                "feedback_route_complexity",
                "power_rail_complexity",
                "bbox_area",
                "deterministic_placement",
                "well_implant_boundary_drc_risk",
            ],
        )
        writer.writeheader()
        for row in candidate_payload["rows"]:
            writer.writerow({key: row[key] for key in writer.fieldnames})
    decision = {
        "floorplan_candidate_count": candidate_payload["candidate_count"],
        "selected_dff_floorplan_architecture": candidate_payload["selected_architecture"],
        "candidates": candidate_payload["rows"],
        "trial_rows": candidate_payload.get("trial_rows", []),
    }
    decision_json_path.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    decision_md_path.write_text(
        "\n".join(
            [
                "# M12C4A DFF Floorplan Decision",
                "",
                f"- floorplan_candidate_count: `{decision['floorplan_candidate_count']}`",
                f"- selected_dff_floorplan_architecture: `{decision['selected_dff_floorplan_architecture']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
