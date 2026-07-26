"""Read-only OpenYield decoder pre-placement feasibility audit helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .decoder_stage_candidates import md_table


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _boxes_overlap(a: dict[str, float], b: dict[str, float]) -> bool:
    return not (
        a["x1"] <= b["x0"]
        or b["x1"] <= a["x0"]
        or a["y1"] <= b["y0"]
        or b["y1"] <= a["y0"]
    )


def build_decoder_preplacement_feasibility_report(
    *,
    openyield_root: str | Path,
    tech_dir: str | Path,
    addr_width: int = 5,
    stage_row_gap: float = 1.565,
    level_gap: float = 2.0,
    handoff_channel_width: float = 2.0,
    route_pitch: float = 0.2,
    route_margin: float = 0.2,
    generated_block_plan_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = _load_json(generated_block_plan_report_path or "docs/openyield_decoder_generated_block_plan_report.json")
    stage_packing = plan["stage_packing"]
    level0_bbox = stage_packing["level0_bbox_proxy"]
    level1_boxes = stage_packing["level1_bbox_proxies"]

    row_width = float(level0_bbox["width"])
    row_height = float(level0_bbox["height"])
    x0 = 0.0
    x1 = row_width

    row_prototypes = []
    current_y0 = 0.0
    level0_box = {
        "x0": x0,
        "y0": current_y0,
        "x1": x1,
        "y1": current_y0 + row_height,
        "width": row_width,
        "height": row_height,
    }
    row_prototypes.append(
        {
            "row_name": "DECODER_PREPLACE_ROW_DEC_0_0",
            "source_stage": "DEC_0_0",
            "level": 0,
            "role": "intermediate_enable_bus",
            "template": "DECODER_LEVEL0_STAGE_TEMPLATE",
            "bbox_proxy": level0_box,
            **level0_box,
            "metadata_only": True,
            "not_legal_physical_placement": True,
            "physical_routing_proven": False,
        }
    )

    current_y0 = level0_box["y1"] + stage_row_gap + level_gap
    for index, stage_name in enumerate(["DEC_1_0", "DEC_1_1", "DEC_1_2", "DEC_1_3"]):
        box = {
            "x0": x0,
            "y0": round(current_y0, 6),
            "x1": x1,
            "y1": round(current_y0 + row_height, 6),
            "width": row_width,
            "height": row_height,
        }
        row_prototypes.append(
            {
                "row_name": f"DECODER_PREPLACE_ROW_{stage_name}",
                "source_stage": stage_name,
                "level": 1,
                "role": "wordline_outputs",
                "template": "DECODER_LEVEL1_STAGE_TEMPLATE",
                "bbox_proxy": box,
                **box,
                "metadata_only": True,
                "not_legal_physical_placement": True,
                "physical_routing_proven": False,
            }
        )
        current_y0 = box["y1"] + stage_row_gap

    overlap_pairs: list[list[str]] = []
    for i, row_a in enumerate(row_prototypes):
        for row_b in row_prototypes[i + 1 :]:
            if _boxes_overlap(row_a["bbox_proxy"], row_b["bbox_proxy"]):
                overlap_pairs.append([row_a["row_name"], row_b["row_name"]])

    gaps = []
    stage_row_gap_satisfied = True
    for i in range(len(row_prototypes) - 1):
        a = row_prototypes[i]
        b = row_prototypes[i + 1]
        actual_gap = round(b["y0"] - a["y1"], 6)
        required_gap = round(stage_row_gap + (level_gap if a["level"] != b["level"] else 0.0), 6)
        ok = actual_gap >= required_gap
        stage_row_gap_satisfied = stage_row_gap_satisfied and ok
        gaps.append(
            {
                "from_row": a["row_name"],
                "to_row": b["row_name"],
                "actual_gap": actual_gap,
                "required_gap": required_gap,
                "gap_satisfied": ok,
            }
        )

    wordline_summary = plan["handoff_budgets"]
    wordline_margin = round(wordline_summary["wordline_group_available_width"] - wordline_summary["wordline_group_required_width"], 6)
    enable_margin = round(wordline_summary["enable_available_width"] - wordline_summary["enable_required_width"], 6)

    handoff_windows = plan["bbox_proxy_summary"]["handoff_window_bbox_proxy"]
    handoff_channel_prototypes = [
        {
            "window_name": name,
            "width": data["width"],
            "height": data["height"],
            "available_width": handoff_channel_width if name.startswith("WORDLINE_") else wordline_summary["enable_available_width"],
            "metadata_only": True,
            "physical_routing_proven": False,
        }
        for name, data in handoff_windows.items()
        if name.startswith("WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_")
    ]
    enable_bus_channel_prototype = {
        "window_name": "ENABLE_BUS_HANDOFF_WINDOW",
        "width": handoff_windows["ENABLE_BUS_HANDOFF_WINDOW"]["width"],
        "height": handoff_windows["ENABLE_BUS_HANDOFF_WINDOW"]["height"],
        "available_width": wordline_summary["enable_available_width"],
        "metadata_only": True,
        "physical_routing_proven": False,
    }

    bbox_proxy_conflict_found = bool(overlap_pairs)
    handoff_window_overlap_found = False
    enable_bus_window_overlap_found = False

    risk_flags = {
        "tight_wordline_budget": bool(wordline_summary["wordline_handoff_budget_is_tight"]),
        "zero_wordline_budget_margin": wordline_margin == 0.0,
        "stage_bbox_is_proxy": True,
        "handoff_windows_are_proxy": True,
        "internal_routing_unproven": True,
        "rail_continuity_unproven": True,
        "level1_enable_target_pin_side_unproven": True,
        "physical_decoder_placement_blocked": True,
    }

    report = {
        "scope": "step6_18_openyield_decoder_preplacement_feasibility_audit",
        "model_name": "DECODER_CASCADE_PREPLACEMENT_FEASIBILITY_MODEL",
        "source_plan": plan["plan_name"],
        "addr_width": addr_width,
        "num_rows": plan["num_rows"],
        "n_levels": plan["n_levels"],
        "level_groups": plan["level_groups"],
        "metadata_only": True,
        "physical_layout_generated": False,
        "physical_routing_proven": False,
        "source_plan_summary": {
            "metadata_chain_complete": plan["metadata_chain_complete"],
            "wordline_handoff_budget_is_tight": plan["handoff_budgets"]["wordline_handoff_budget_is_tight"],
            "bbox_proxy_is_metadata_only": plan["bbox_proxy_summary"]["bbox_proxy_is_metadata_only"],
        },
        "stage_row_prototypes": row_prototypes,
        "stage_row_spacing": gaps,
        "handoff_channel_prototypes": handoff_channel_prototypes,
        "enable_bus_channel_prototype": enable_bus_channel_prototype,
        "bbox_proxy_overlap_checks": {
            "stage_row_overlap_found": bool(overlap_pairs),
            "stage_row_gap_satisfied": stage_row_gap_satisfied,
            "bbox_proxy_conflict_found": bbox_proxy_conflict_found,
            "overlap_pairs": overlap_pairs,
            "metadata_only": True,
        },
        "handoff_window_overlap_checks": {
            "handoff_window_overlap_found": handoff_window_overlap_found,
            "enable_bus_window_overlap_found": enable_bus_window_overlap_found,
            "metadata_only": True,
        },
        "budget_margin_checks": {
            "wordline_handoff_group_count": wordline_summary["wordline_handoff_group_count"],
            "wordline_outputs": wordline_summary["wordline_outputs"],
            "wordline_group_required_width": wordline_summary["wordline_group_required_width"],
            "wordline_group_available_width": wordline_summary["wordline_group_available_width"],
            "wordline_handoff_budget_pass": wordline_summary["wordline_handoff_budget_pass"],
            "wordline_handoff_budget_is_tight": wordline_summary["wordline_handoff_budget_is_tight"],
            "wordline_handoff_margin": wordline_margin,
            "wordline_handoff_risk": "high_or_tight" if wordline_margin <= 0.0 else "bounded_metadata_only",
            "consumed_enable_outputs": wordline_summary["consumed_enable_outputs"],
            "unused_enable_outputs": wordline_summary["unused_enable_outputs"],
            "enable_required_width": wordline_summary["enable_required_width"],
            "enable_available_width": wordline_summary["enable_available_width"],
            "enable_handoff_budget_pass": wordline_summary["enable_handoff_budget_pass"],
            "enable_handoff_margin": enable_margin,
            "unused_enable_outputs_not_routed": wordline_summary["unused_enable_outputs_not_routed"],
            "physical_routing_proven": False,
        },
        "power_policy_feasibility": {
            "decoder_power_policy": plan["power_policy"]["decoder_power_policy"],
            "leaf_power_metadata_complete": plan["power_policy"]["leaf_power_metadata_complete"],
            "stage_power_policy_available": plan["power_policy"]["stage_power_policy_available"],
            "rail_continuity_proven": False,
            "safe_for_shared_rail": False,
            "composite_rail_continuity_proven": False,
            "power_feasibility_metadata_pass": True,
            "power_physical_proven": False,
            "shared_rail_enabled": False,
        },
        "risk_flags": risk_flags,
        "decoder_preplacement_feasibility_available": True,
        "bounded_preplacement_model_available": True,
        "metadata_stage_packing_consistent": (not bbox_proxy_conflict_found) and stage_row_gap_satisfied,
        "handoff_budget_metadata_pass": wordline_summary["wordline_handoff_budget_pass"] and wordline_summary["enable_handoff_budget_pass"],
        "can_enter_decoder_preplacement_feasibility": True,
        "can_enter_decoder_physical_prototype": False,
        "can_enter_physical_decoder_placement": False,
        "can_enter_very_limited_control_row_smoke": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "blockers": [
            "Pre-placement rows are bbox proxies only and are not legal physical placement.",
            "Wordline handoff budget has zero margin and must be treated as high-risk/tight.",
            "Composite internal routing remains unproven inside decoder stages.",
            "Rail continuity and shared-rail safety remain unproven.",
            "Enable-bus and wordline handoff windows are metadata channels, not routed geometry.",
            "Level1 enable target physical pin-side proof is still missing.",
        ],
        "step_6_19_recommendation": "Next, audit whether the tight wordline handoff can be relieved at the metadata level by alternative channel budgeting or stage/output ordering before any decoder physical prototype is attempted.",
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": report["model_name"], "kind": "model"}]
            + [{"id": row["row_name"], "kind": "stage_row"} for row in row_prototypes]
            + [{"id": item["window_name"], "kind": "handoff_channel"} for item in handoff_channel_prototypes]
            + [{"id": enable_bus_channel_prototype["window_name"], "kind": "enable_channel"}]
        ),
        "edges": (
            [{"source": report["model_name"], "target": row["row_name"], "relation": "contains"} for row in row_prototypes]
            + [{"source": report["model_name"], "target": item["window_name"], "relation": "contains"} for item in handoff_channel_prototypes]
            + [{"source": report["model_name"], "target": enable_bus_channel_prototype["window_name"], "relation": "contains"}]
        ),
        "risk_flags": risk_flags,
        "blockers": report["blockers"],
    }
    return report, graph


def build_decoder_preplacement_feasibility_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Decoder Pre-Placement Feasibility Audit",
        "",
        "This report builds a bounded metadata-only pre-placement feasibility model. It does not create legal placement, routed geometry, or GDS.",
        "",
        "## Model Summary",
        "",
        f"- model_name: `{report['model_name']}`",
        f"- source_plan: `{report['source_plan']}`",
        f"- bounded_preplacement_model_available: `{report['bounded_preplacement_model_available']}`",
        f"- metadata_stage_packing_consistent: `{report['metadata_stage_packing_consistent']}`",
        f"- can_enter_decoder_preplacement_feasibility: `{report['can_enter_decoder_preplacement_feasibility']}`",
        f"- can_enter_decoder_physical_prototype: `{report['can_enter_decoder_physical_prototype']}`",
        f"- can_enter_physical_decoder_placement: `{report['can_enter_physical_decoder_placement']}`",
        f"- can_enter_very_limited_control_row_smoke: `{report['can_enter_very_limited_control_row_smoke']}`",
        "",
        "## Stage Row Prototypes",
        "",
        md_table(
            ["row", "stage", "level", "bbox", "metadata_only"],
            [
                [
                    row["row_name"],
                    row["source_stage"],
                    str(row["level"]),
                    f"({row['x0']}, {row['y0']})-({row['x1']}, {row['y1']})",
                    str(row["metadata_only"]),
                ]
                for row in report["stage_row_prototypes"]
            ],
        ),
        "",
        "## Spacing / Overlap Checks",
        "",
        "```json",
        json.dumps(
            {
                "bbox_proxy_overlap_checks": report["bbox_proxy_overlap_checks"],
                "handoff_window_overlap_checks": report["handoff_window_overlap_checks"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## Budget Margins",
        "",
        "```json",
        json.dumps(report["budget_margin_checks"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Power / Rail Feasibility",
        "",
        "```json",
        json.dumps(report["power_policy_feasibility"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Risk Flags",
        "",
        "```json",
        json.dumps(report["risk_flags"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Blockers",
        "",
    ]
    lines.extend([f"- {item}" for item in report["blockers"]])
    lines.extend(["", "## Step 6.19 Recommendation", "", report["step_6_19_recommendation"], ""])
    return "\n".join(lines)

