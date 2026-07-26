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


def build_dff_buf_floorplan_candidates(
    *,
    child_bboxes: dict[str, list[float]],
) -> dict[str, Any]:
    dff_w = _width(child_bboxes["DFF"])
    dff_h = _height(child_bboxes["DFF"])
    inv1_w = _width(child_bboxes["PINV_INV1"])
    inv1_h = _height(child_bboxes["PINV_INV1"])
    inv2_w = _width(child_bboxes["PINV_INV2"])
    inv2_h = _height(child_bboxes["PINV_INV2"])
    row_h = max(dff_h, inv1_h, inv2_h)
    h_gap = 0.35
    v_gap = 0.55
    rows: list[dict[str, Any]] = []

    single_row = [
        Placement("dff", 0.0, 0.0),
        Placement("inv1", dff_w + h_gap, 0.0),
        Placement("inv2", dff_w + h_gap + inv1_w + h_gap, 0.0),
    ]
    rows.append(
        {
            "architecture": "SINGLE_ROW_SOURCE_ORDER",
            "placements": [placement.__dict__ for placement in single_row],
            "estimated_signal_wirelength": round(dff_w + inv1_w + inv2_w + 2 * h_gap, 6),
            "expected_via_count": 10,
            "same_layer_crossover_count": 0,
            "power_alignment_result": "DIRECT_ROW_ALIGNMENT",
            "routing_channel_sufficiency": "HIGH",
            "drc_risk_score": 2,
            "bbox_area": round((dff_w + inv1_w + inv2_w + 2 * h_gap) * row_h, 6),
            "selection_reason_hint": "Keeps source order and straightforward power alignment.",
        }
    )

    buffer_stack = [
        Placement("dff", 0.0, 0.0),
        Placement("inv1", dff_w - inv1_w, dff_h + v_gap),
        Placement("inv2", dff_w - inv2_w, dff_h + v_gap + inv1_h + 0.25),
    ]
    rows.append(
        {
            "architecture": "STACKED_OUTPUT_BUFFER_COLUMN",
            "placements": [placement.__dict__ for placement in buffer_stack],
            "estimated_signal_wirelength": round(dff_h + inv1_h + inv2_h + 2 * v_gap, 6),
            "expected_via_count": 12,
            "same_layer_crossover_count": 0,
            "power_alignment_result": "REQUIRES_VERTICAL_POWER_STITCH",
            "routing_channel_sufficiency": "MEDIUM",
            "drc_risk_score": 4,
            "bbox_area": round(dff_w * (dff_h + inv1_h + inv2_h + 2 * v_gap + 0.25), 6),
            "selection_reason_hint": "Minimizes qint/QB horizontal distance but increases power stitching complexity.",
        }
    )

    staggered = [
        Placement("dff", 0.0, 0.0),
        Placement("inv1", dff_w + h_gap, 0.55),
        Placement("inv2", dff_w + h_gap + inv1_w + h_gap, 0.0),
    ]
    rows.append(
        {
            "architecture": "STAGGERED_OUTPUT_CHAIN",
            "placements": [placement.__dict__ for placement in staggered],
            "estimated_signal_wirelength": round(dff_w + inv1_w + inv2_w + 2 * h_gap + 0.55, 6),
            "expected_via_count": 11,
            "same_layer_crossover_count": 0,
            "power_alignment_result": "DIRECT_ROW_ALIGNMENT_WITH_VERTICAL_TAP",
            "routing_channel_sufficiency": "MEDIUM",
            "drc_risk_score": 3,
            "bbox_area": round((dff_w + inv1_w + inv2_w + 2 * h_gap) * max(dff_h, inv1_h + 0.55, inv2_h), 6),
            "selection_reason_hint": "Creates extra local channel between inv1 and inv2 without changing source order.",
        }
    )

    return {
        "candidate_count": len(rows),
        "rows": rows,
    }


def select_dff_buf_floorplan_from_trials(
    *,
    candidate_payload: dict[str, Any],
    trial_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    def sort_key(row: dict[str, Any]) -> tuple[int, int, int, int, float, int, float]:
        return (
            0 if row["connectivity_passed"] else 1,
            int(row["missing_expected_endpoint_count"]),
            int(row["unexpected_net_merge_count"]),
            int(row["drc_marker_count"]),
            float(row["estimated_signal_wirelength"]),
            int(row["via1_count"]),
            float(row["bbox_area"]),
        )

    selected_trial = sorted(trial_rows, key=sort_key)[0]
    selected_arch = selected_trial["architecture"]
    selected_row = next(row for row in candidate_payload["rows"] if row["architecture"] == selected_arch)
    return {
        "candidate_count": candidate_payload["candidate_count"],
        "selected_architecture": selected_arch,
        "rows": candidate_payload["rows"],
        "trial_rows": trial_rows,
        "selected_trial": selected_trial,
        "selected_placements": selected_row["placements"],
    }


def write_dff_buf_floorplan_outputs(
    *,
    candidate_payload: dict[str, Any],
    json_path: Path,
    md_path: Path,
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(candidate_payload, indent=2) + "\n", encoding="utf-8")
    selected = candidate_payload.get("selected_architecture")
    selected_reason = ""
    if candidate_payload.get("selected_trial"):
        selected_reason = candidate_payload["selected_trial"].get("selection_reason", "")
    md_path.write_text(
        "\n".join(
            [
                "# Wave3 DFF_BUF Floorplan Selection",
                "",
                f"- floorplan_candidate_count: `{candidate_payload['candidate_count']}`",
                f"- selected_floorplan_architecture: `{selected}`",
                f"- selected_floorplan_reason: `{selected_reason}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
