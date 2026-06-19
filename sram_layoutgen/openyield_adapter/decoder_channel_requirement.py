"""Read-only OpenYield decoder channel requirement propagation audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .decoder_stage_candidates import md_table


def _risk_level(margin: float) -> str:
    if margin < 0:
        return "fail"
    if margin == 0:
        return "tight_zero_margin"
    if margin < 0.4:
        return "pass_low_margin"
    return "pass_moderate_margin"


def build_decoder_channel_requirement_report(
    *,
    addr_width: int = 5,
    base_wordline_channel_width: float = 2.0,
    recommended_wordline_channel_width: float = 2.2,
    route_pitch: float = 0.2,
    route_margin: float = 0.2,
    enable_channel_width: float = 2.0,
    stage_row_gap: float = 1.565,
    level_gap: float = 2.0,
    control_window_policy: str = "metadata_expand_wordline_windows",
    handoff_relief_report_path: str | Path | None = None,
    preplacement_report_path: str | Path | None = None,
    generated_block_plan_report_path: str | Path | None = None,
    control_geometry_report_path: str | Path | None = None,
    control_channel_budget_report_path: str | Path | None = None,
    control_row_feasibility_report_path: str | Path | None = None,
    control_row_floorplan_report_path: str | Path | None = None,
    control_target_envelope_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    handoff_relief = json.loads(Path(handoff_relief_report_path or "docs/openyield_decoder_handoff_relief_report.json").read_text(encoding="utf-8"))
    preplacement = json.loads(Path(preplacement_report_path or "docs/openyield_decoder_preplacement_feasibility_report.json").read_text(encoding="utf-8"))
    generated = json.loads(Path(generated_block_plan_report_path or "docs/openyield_decoder_generated_block_plan_report.json").read_text(encoding="utf-8"))
    control_geometry = json.loads(Path(control_geometry_report_path or "docs/openyield_control_geometry_window_report.json").read_text(encoding="utf-8"))
    control_budget = json.loads(Path(control_channel_budget_report_path or "docs/openyield_control_channel_budget_report.json").read_text(encoding="utf-8"))
    control_feasibility = json.loads(Path(control_row_feasibility_report_path or "docs/openyield_control_row_feasibility_report.json").read_text(encoding="utf-8"))
    control_floorplan = json.loads(Path(control_row_floorplan_report_path or "docs/openyield_control_row_floorplan_report.json").read_text(encoding="utf-8"))
    control_target = json.loads(Path(control_target_envelope_report_path or "docs/openyield_control_target_envelope_report.json").read_text(encoding="utf-8"))

    decoder_channel_entry = next(
        item for item in control_budget["channels"] if item["channel_name"] == "ADDR_TO_DECODER_CHANNEL"
    )

    required_width = round(8 * route_pitch + 2 * route_margin, 6)
    old_margin = round(base_wordline_channel_width - required_width, 6)
    new_margin = round(recommended_wordline_channel_width - required_width, 6)

    affected_windows = []
    for index in range(4):
        affected_windows.append(
            {
                "window_name": f"WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_{index}",
                "source_stage": f"DEC_1_{index}",
                "old_width": base_wordline_channel_width,
                "new_width": recommended_wordline_channel_width,
                "delta_width": round(recommended_wordline_channel_width - base_wordline_channel_width, 6),
                "old_margin": old_margin,
                "new_margin": new_margin,
                "budget_risk_before": _risk_level(old_margin),
                "budget_risk_after": _risk_level(new_margin),
                "metadata_only": True,
                "physical_routing_proven": False,
            }
        )

    extra_width = round(recommended_wordline_channel_width - base_wordline_channel_width, 6)
    decoder_input_window = control_geometry["decoder_input_window"]
    decoder_input_budget_old = round(float(decoder_input_window["width"]) - float(decoder_input_window["budget_required_width"]), 6)
    control_geometry_window_compatibility_checked = True

    floorplan_checks = {
        "stage_row_overlap_found": preplacement["bbox_proxy_overlap_checks"]["stage_row_overlap_found"],
        "handoff_window_overlap_found": preplacement["handoff_window_overlap_checks"]["handoff_window_overlap_found"],
        "enable_bus_window_overlap_found": preplacement["handoff_window_overlap_checks"]["enable_bus_window_overlap_found"],
        "control_keepout_conflict_found": control_geometry["keepout_conflict_found"],
        "bbox_proxy_conflict_found": preplacement["bbox_proxy_overlap_checks"]["bbox_proxy_conflict_found"],
        "metadata_only": True,
    }

    control_geometry_compatibility = {
        "control_geometry_window_compatibility_checked": control_geometry_window_compatibility_checked,
        "decoder_wordline_channel_requires_floorplan_update": True,
        "control_window_metadata_update_required": True,
        "extra_width_required": extra_width,
        "extra_width_available_or_assumed": "unknown",
        "compatibility_status": "requires_parent_floorplan_reservation",
        "safe_for_metadata_requirement_propagation": True,
        "safe_for_physical_floorplan_claim": False,
        "control_window_policy": control_window_policy,
        "referenced_windows": [
            "CLOCK_ENTRY_WINDOW",
            "ADDR_TO_DECODER_WINDOW",
            "DATA_TO_WRITEDRIVER_WINDOW",
            "DECODER_INPUT_ANCHOR",
            "WRITEDRIVER_INPUT_ANCHOR",
            "DECODER_CASCADE_ENVELOPE",
        ],
    }

    enable_channel_impact = {
        "enable_channel_width": enable_channel_width,
        "enable_required_width": generated["handoff_budgets"]["enable_required_width"],
        "enable_margin": round(enable_channel_width - generated["handoff_budgets"]["enable_required_width"], 6),
        "enable_handoff_budget_pass": generated["handoff_budgets"]["enable_handoff_budget_pass"],
        "enable_channel_unchanged": True,
        "unused_enable_outputs_not_routed": generated["handoff_budgets"]["unused_enable_outputs_not_routed"],
        "enable_channel_impact": "none_in_metadata_model",
    }

    updated_budget_summary = {
        "base_wordline_channel_width": base_wordline_channel_width,
        "recommended_wordline_channel_width": recommended_wordline_channel_width,
        "wordline_required_width": required_width,
        "old_wordline_margin": old_margin,
        "new_wordline_margin": new_margin,
        "old_risk_level": _risk_level(old_margin),
        "new_risk_level": _risk_level(new_margin),
        "recommended_wordline_channel_width_recorded": True,
    }

    risk_flags = {
        "metadata_requirement_propagated": True,
        "positive_wordline_margin_available": new_margin > 0,
        "wordline_margin_still_low": 0 < new_margin < 0.4,
        "physical_routing_proven": False,
        "parent_floorplan_reservation_required": True,
        "floorplan_space_proven": False,
        "handoff_windows_are_proxy": True,
        "stage_bbox_is_proxy": True,
        "rail_continuity_unproven": True,
        "physical_decoder_placement_blocked": True,
    }

    report = {
        "scope": "step6_20_openyield_decoder_channel_requirement_audit",
        "requirement_name": "DECODER_WORDLINE_CHANNEL_2P2_REQUIREMENT",
        "source_step": "Step 6.19 decoder handoff relief",
        "source_strategy": handoff_relief["recommended_handoff_relief_strategy"],
        "base_width": base_wordline_channel_width,
        "recommended_width": recommended_wordline_channel_width,
        "required_width": required_width,
        "recommended_margin": new_margin,
        "metadata_only": True,
        "physical_routing_proven": False,
        "decoder_channel_requirement_available": True,
        "affected_windows": affected_windows,
        "affected_handoff_groups": [item["source_stage"] for item in affected_windows],
        "floorplan_compatibility": floorplan_checks,
        "control_window_compatibility": control_geometry_compatibility,
        "enable_window_impact": enable_channel_impact,
        "bbox_proxy_overlap_checks": floorplan_checks,
        "updated_budget_summary": updated_budget_summary,
        "risk_flags": risk_flags,
        "recommended_next_decoder_policy": "record_2p2_wordline_channel_requirement_and_stop_decoder_physical_push",
        "recommended_wordline_channel_width_recorded": True,
        "metadata_requirement_propagated": True,
        "positive_wordline_margin_available": new_margin > 0,
        "safe_for_metadata_requirement_propagation": True,
        "safe_for_physical_floorplan_claim": False,
        "compatibility_status": "requires_parent_floorplan_reservation",
        "parent_floorplan_reservation_required": True,
        "can_enter_decoder_preplacement_feasibility": True,
        "can_enter_decoder_physical_prototype": False,
        "can_enter_physical_decoder_placement": False,
        "can_enter_very_limited_control_row_smoke": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "blocker_list": [
            "The 2.2um channel is only a propagated metadata reservation, not a legal routed channel.",
            "Broader parent floorplan space for the extra 0.2um is not physically proven.",
            "Control geometry windows and decoder envelope would need synchronized metadata updates.",
            "Physical decoder prototype and placement remain blocked even after positive metadata margin is recorded.",
        ],
        "step_6_21_recommendation": "Next, audit the parent control-row reservation model: determine where the extra 0.2um can be carved out in the broader control/decoder side plan without changing physical placement yet.",
        "source_context": {
            "control_geometry_decoder_window_width": decoder_input_window["width"],
            "control_geometry_decoder_window_budget_required": decoder_input_window["budget_required_width"],
            "control_geometry_decoder_window_old_margin": decoder_input_budget_old,
            "control_budget_decoder_channel_width": decoder_channel_entry["channel_width_um"],
            "control_row_decoder_channel_width": control_feasibility["row_to_decoder_channel"]["channel_width_um"],
            "decoder_target_envelope_metadata_only": control_target["decoder_envelope_is_metadata_only"],
            "control_floorplan_row_to_decoder_consumer": control_floorplan["addr_dff_row_summary"]["downstream_consumer"],
        },
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": report["requirement_name"], "kind": "requirement"}]
            + [{"id": item["window_name"], "kind": "affected_window"} for item in affected_windows]
            + [
                {"id": "ADDR_TO_DECODER_WINDOW", "kind": "control_window"},
                {"id": "DECODER_CASCADE_ENVELOPE", "kind": "decoder_envelope"},
            ]
        ),
        "edges": (
            [{"source": report["requirement_name"], "target": item["window_name"], "relation": "widens"} for item in affected_windows]
            + [{"source": report["requirement_name"], "target": "ADDR_TO_DECODER_WINDOW", "relation": "requires_parent_reservation"}]
            + [{"source": report["requirement_name"], "target": "DECODER_CASCADE_ENVELOPE", "relation": "propagates_to"}]
        ),
        "recommended_next_decoder_policy": report["recommended_next_decoder_policy"],
        "blockers": report["blocker_list"],
    }
    return report, graph


def build_decoder_channel_requirement_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Decoder Channel Requirement Audit",
        "",
        "This report propagates the 2.2um wordline channel recommendation as a metadata-only decoder planning requirement. It does not prove legal routing, placement, or floorplan closure.",
        "",
        "## Requirement Summary",
        "",
        f"- requirement_name: `{report['requirement_name']}`",
        f"- source_strategy: `{report['source_strategy']}`",
        f"- base_width: `{report['base_width']}`",
        f"- recommended_width: `{report['recommended_width']}`",
        f"- required_width: `{report['required_width']}`",
        f"- recommended_margin: `{report['recommended_margin']}`",
        "",
        "## Affected Windows",
        "",
        md_table(
            ["window", "old_width", "new_width", "delta", "old_margin", "new_margin", "risk_before", "risk_after"],
            [
                [
                    item["window_name"],
                    str(item["old_width"]),
                    str(item["new_width"]),
                    str(item["delta_width"]),
                    str(item["old_margin"]),
                    str(item["new_margin"]),
                    item["budget_risk_before"],
                    item["budget_risk_after"],
                ]
                for item in report["affected_windows"]
            ],
        ),
        "",
        "## Updated Budget Summary",
        "",
        "```json",
        json.dumps(report["updated_budget_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Floorplan Compatibility Checks",
        "",
        "```json",
        json.dumps(report["floorplan_compatibility"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Control Geometry Compatibility",
        "",
        "```json",
        json.dumps(report["control_window_compatibility"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Enable Channel Impact",
        "",
        "```json",
        json.dumps(report["enable_window_impact"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Risk Flags",
        "",
        "```json",
        json.dumps(report["risk_flags"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Recommended Next Decoder Policy",
        "",
        f"`{report['recommended_next_decoder_policy']}`",
        "",
        "## Blockers",
        "",
    ]
    lines.extend([f"- {item}" for item in report["blocker_list"]])
    lines.extend(["", "## Step 6.21 Recommendation", "", report["step_6_21_recommendation"], ""])
    return "\n".join(lines)
