"""Read-only OpenYield decoder handoff relief audit helpers."""

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


def build_decoder_handoff_relief_report(
    *,
    addr_width: int = 5,
    route_pitch: float = 0.2,
    route_margin: float = 0.2,
    base_wordline_channel_width: float = 2.0,
    candidate_wordline_channel_widths: list[float] | None = None,
    enable_channel_width: float = 2.0,
    grouping_policy: str = "current_8_outputs_per_stage",
    stage_order_policy: str = "current_level1_order",
    preplacement_report_path: str | Path | None = None,
    handoff_budget_report_path: str | Path | None = None,
    generated_block_plan_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if candidate_wordline_channel_widths is None:
        candidate_wordline_channel_widths = [2.0, 2.2, 2.4, 2.6, 3.0]

    preplacement = json.loads(Path(preplacement_report_path or "docs/openyield_decoder_preplacement_feasibility_report.json").read_text(encoding="utf-8"))
    handoff = json.loads(Path(handoff_budget_report_path or "docs/openyield_decoder_output_handoff_budget_report.json").read_text(encoding="utf-8"))
    generated = json.loads(Path(generated_block_plan_report_path or "docs/openyield_decoder_generated_block_plan_report.json").read_text(encoding="utf-8"))

    baseline_required = round(8 * route_pitch + 2 * route_margin, 6)
    baseline_margin = round(base_wordline_channel_width - baseline_required, 6)
    baseline = {
        "option_name": "baseline_current_wordline_budget",
        "grouping_policy": grouping_policy,
        "stage_order_policy": stage_order_policy,
        "tracks_per_group": 8,
        "route_pitch": route_pitch,
        "route_margin": route_margin,
        "required_width": baseline_required,
        "available_width": base_wordline_channel_width,
        "margin": baseline_margin,
        "budget_pass": baseline_margin >= 0,
        "risk": "high_or_tight" if baseline_margin <= 0 else "bounded_metadata_only",
        "safe_for_metadata_planning": True,
        "safe_for_physical_routing": False,
    }

    sweep = []
    first_positive = None
    for width in candidate_wordline_channel_widths:
        margin = round(width - baseline_required, 6)
        row = {
            "candidate_width": width,
            "required_width": baseline_required,
            "margin": margin,
            "budget_pass": margin >= 0,
            "risk_level": _risk_level(margin),
        }
        sweep.append(row)
        if first_positive is None and margin > 0:
            first_positive = row

    split_options = []
    for subgroups, tracks in [("split_8_into_2x4", 4), ("split_8_into_4x2", 2)]:
        required = round(tracks * route_pitch + 2 * route_margin, 6)
        margin = round(base_wordline_channel_width - required, 6)
        split_options.append(
            {
                "option_name": subgroups,
                "grouping_policy": subgroups,
                "tracks_per_subgroup": tracks,
                "required_width": required,
                "available_width": base_wordline_channel_width,
                "margin": margin,
                "budget_pass": margin >= 0,
                "risk_level": _risk_level(margin),
                "additional_windows_required": True,
                "stage_output_contract_consistency": True,
                "wordline_output_handoff_consistency": True,
                "split_grouping_metadata_possible": True,
                "split_grouping_requires_extra_window_count": True,
                "physical_routing_proven": False,
            }
        )

    staggered_options = []
    for tracks in [4, 2]:
        required = round(tracks * route_pitch + 2 * route_margin, 6)
        margin = round(base_wordline_channel_width - required, 6)
        staggered_options.append(
            {
                "option_name": "staggered_output_handoff",
                "tracks_per_window": tracks,
                "window_count_increase": 8 // tracks,
                "required_width": required,
                "available_width": base_wordline_channel_width,
                "margin": margin,
                "metadata_budget_pass": margin >= 0,
                "risk_level": _risk_level(margin),
                "requires_output_order_change": False,
                "requires_stage_window_relayout": True,
                "physical_routing_proven": False,
            }
        )

    keep_with_extra_margin = {
        "option_name": "keep_current_grouping_with_extra_margin_requirement",
        "recommended_policy": "require_wordline_channel_width_gt_required_width",
        "minimum_positive_margin": 0.2,
        "recommended_wordline_channel_width": 2.2,
        "metadata_only": True,
        "physical_routing_proven": False,
    }

    recommended_strategy = "keep_baseline_and_mark_high_risk"
    recommended_width = None
    recommended_margin = None
    if first_positive and round(first_positive["candidate_width"], 6) == 2.2:
        recommended_strategy = "metadata_channel_widening_to_2p2"
        recommended_width = first_positive["candidate_width"]
        recommended_margin = first_positive["margin"]
    elif first_positive:
        recommended_strategy = "metadata_channel_widening_to_positive_margin"
        recommended_width = first_positive["candidate_width"]
        recommended_margin = first_positive["margin"]
    elif split_options:
        recommended_strategy = "split_wordline_windows_metadata_only"

    preservation = {
        "truth_table_binding_preserved": generated["truth_table_binding"]["truth_table_binding_complete"],
        "output_contracts_preserved": generated["output_contracts"]["all_local_outputs_have_contract"],
        "wordline_global_mapping_preserved": generated["output_contracts"]["all_level1_outputs_have_expansion"],
        "wordline_driver_handoff_preserved": generated["truth_table_binding"]["wordline_output_handoff_consistent"],
        "unused_enable_outputs_not_routed": handoff["consistency_checks"]["unused_enable_outputs_not_routed"],
        "output_mapping_preserved": True,
        "physical_routing_proven": False,
    }

    report = {
        "scope": "step6_19_openyield_decoder_handoff_relief_audit",
        "decoder_handoff_relief_available": True,
        "baseline_wordline_budget": baseline,
        "baseline_wordline_margin": baseline_margin,
        "zero_margin_risk_identified": baseline_margin == 0.0,
        "candidate_width_sweep": sweep,
        "positive_margin_candidate_available": first_positive is not None,
        "first_positive_margin_width": first_positive["candidate_width"] if first_positive else None,
        "split_grouping_analysis": split_options,
        "staggered_output_analysis": staggered_options,
        "keep_current_with_extra_margin_option": keep_with_extra_margin,
        "output_mapping_preservation_checks": preservation,
        "recommended_handoff_relief_strategy": recommended_strategy,
        "recommended_min_wordline_channel_width": recommended_width,
        "recommended_margin": recommended_margin,
        "physical_routing_proven": False,
        "can_enter_decoder_preplacement_feasibility": True,
        "can_enter_decoder_physical_prototype": False,
        "can_enter_physical_decoder_placement": False,
        "can_enter_very_limited_control_row_smoke": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "blocker_list": [
            "All relief options remain metadata-only and do not prove routing legality.",
            "Widened metadata channel width does not create a legal routed channel by itself.",
            "Split or staggered windows would require extra planning windows and stage/window relayout metadata.",
            "Physical decoder prototype remains blocked even when positive metadata margin exists.",
        ],
        "step_6_20_recommendation": "Next, if the team wants to keep the current semantic grouping, promote the 2.2um metadata channel width requirement into the next decoder planning step and audit whether the broader control-row floorplan can reserve that space.",
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": baseline["option_name"], "kind": "option"}]
            + [{"id": f"width_{item['candidate_width']}", "kind": "width_candidate"} for item in sweep]
            + [{"id": item["option_name"], "kind": "split_option"} for item in split_options]
            + [{"id": f"staggered_{item['tracks_per_window']}", "kind": "stagger_option"} for item in staggered_options]
        ),
        "edges": (
            [{"source": baseline["option_name"], "target": f"width_{item['candidate_width']}", "relation": "sweep"} for item in sweep]
            + [{"source": baseline["option_name"], "target": item["option_name"], "relation": "alternative_grouping"} for item in split_options]
            + [{"source": baseline["option_name"], "target": f"staggered_{item['tracks_per_window']}", "relation": "alternative_windowing"} for item in staggered_options]
        ),
        "recommended_handoff_relief_strategy": recommended_strategy,
        "blockers": report["blocker_list"],
    }
    return report, graph


def build_decoder_handoff_relief_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Decoder Handoff Relief Audit",
        "",
        "This is a metadata-only relief audit for the tight decoder wordline handoff budget. It does not modify placement, routing, standalone.py, or the GDS writer.",
        "",
        "## Baseline Wordline Budget",
        "",
        "```json",
        json.dumps(report["baseline_wordline_budget"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Candidate Width Sweep",
        "",
        md_table(
            ["candidate_width", "required_width", "margin", "budget_pass", "risk_level"],
            [
                [
                    str(item["candidate_width"]),
                    str(item["required_width"]),
                    str(item["margin"]),
                    str(item["budget_pass"]),
                    item["risk_level"],
                ]
                for item in report["candidate_width_sweep"]
            ],
        ),
        "",
        "## Split Grouping Analysis",
        "",
        "```json",
        json.dumps(report["split_grouping_analysis"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Staggered Output Analysis",
        "",
        "```json",
        json.dumps(report["staggered_output_analysis"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Recommended Strategy",
        "",
        f"- recommended_handoff_relief_strategy: `{report['recommended_handoff_relief_strategy']}`",
        f"- recommended_min_wordline_channel_width: `{report['recommended_min_wordline_channel_width']}`",
        f"- recommended_margin: `{report['recommended_margin']}`",
        "",
        "## Mapping Preservation Checks",
        "",
        "```json",
        json.dumps(report["output_mapping_preservation_checks"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Blockers",
        "",
    ]
    lines.extend([f"- {item}" for item in report["blocker_list"]])
    lines.extend(["", "## Step 6.20 Recommendation", "", report["step_6_20_recommendation"], ""])
    return "\n".join(lines)

