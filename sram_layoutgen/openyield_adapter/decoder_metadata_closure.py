"""Read-only OpenYield decoder metadata closure summary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .decoder_stage_candidates import md_table


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_decoder_metadata_closure_report(
    *,
    addr_width: int = 5,
    stage_candidate_report_path: str | Path | None = None,
    row_rule_report_path: str | Path | None = None,
    logic_repair_report_path: str | Path | None = None,
    composite_leaf_report_path: str | Path | None = None,
    stage_template_report_path: str | Path | None = None,
    truth_table_report_path: str | Path | None = None,
    output_contract_report_path: str | Path | None = None,
    handoff_budget_report_path: str | Path | None = None,
    generated_block_plan_report_path: str | Path | None = None,
    preplacement_report_path: str | Path | None = None,
    handoff_relief_report_path: str | Path | None = None,
    channel_requirement_report_path: str | Path | None = None,
    parent_reservation_report_path: str | Path | None = None,
    time_control_decomposition_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    stage_candidates = _load_json(stage_candidate_report_path or "docs/openyield_decoder_stage_candidate_report.json")
    row_rules = _load_json(row_rule_report_path or "docs/openyield_decoder_row_rule_report.json")
    logic_repair = _load_json(logic_repair_report_path or "docs/openyield_decoder_logic_repair_report.json")
    composite_leaf = _load_json(composite_leaf_report_path or "docs/openyield_decoder_composite_leaf_convention_report.json")
    stage_templates = _load_json(stage_template_report_path or "docs/openyield_decoder_stage_template_report.json")
    truth_table = _load_json(truth_table_report_path or "docs/openyield_decoder_truth_table_binding_report.json")
    output_contracts = _load_json(output_contract_report_path or "docs/openyield_decoder_output_contract_report.json")
    handoff_budget = _load_json(handoff_budget_report_path or "docs/openyield_decoder_output_handoff_budget_report.json")
    generated_block_plan = _load_json(generated_block_plan_report_path or "docs/openyield_decoder_generated_block_plan_report.json")
    preplacement = _load_json(preplacement_report_path or "docs/openyield_decoder_preplacement_feasibility_report.json")
    handoff_relief = _load_json(handoff_relief_report_path or "docs/openyield_decoder_handoff_relief_report.json")
    channel_requirement = _load_json(channel_requirement_report_path or "docs/openyield_decoder_channel_requirement_report.json")
    parent_reservation = _load_json(parent_reservation_report_path or "docs/openyield_control_parent_reservation_report.json")
    time_control = _load_json(time_control_decomposition_report_path or "docs/openyield_time_control_decomposition_report.json")

    closed_items = {
        "decoder_stage_candidates_closed": True,
        "decoder_row_rules_closed": True,
        "decoder_logic_repair_strategy_closed": True,
        "decoder_composite_leaf_conventions_closed": True,
        "decoder_stage_templates_closed": True,
        "decoder_truth_table_binding_closed": True,
        "decoder_output_contracts_closed": True,
        "decoder_output_handoff_budget_closed": True,
        "decoder_generated_block_plan_closed": True,
        "decoder_preplacement_feasibility_closed": True,
        "decoder_handoff_relief_closed": True,
        "decoder_channel_requirement_closed": True,
        "parent_control_reservation_closed": True,
    }

    source_reports = [
        {"step": "6.9", "scope": stage_candidates["scope"], "report": "docs/openyield_decoder_stage_candidate_report.json"},
        {"step": "6.10", "scope": row_rules["scope"], "report": "docs/openyield_decoder_row_rule_report.json"},
        {"step": "6.11", "scope": logic_repair["scope"], "report": "docs/openyield_decoder_logic_repair_report.json"},
        {"step": "6.12", "scope": composite_leaf["scope"], "report": "docs/openyield_decoder_composite_leaf_convention_report.json"},
        {"step": "6.13", "scope": stage_templates["scope"], "report": "docs/openyield_decoder_stage_template_report.json"},
        {"step": "6.14", "scope": truth_table["scope"], "report": "docs/openyield_decoder_truth_table_binding_report.json"},
        {"step": "6.15", "scope": output_contracts["scope"], "report": "docs/openyield_decoder_output_contract_report.json"},
        {"step": "6.16", "scope": handoff_budget["scope"], "report": "docs/openyield_decoder_output_handoff_budget_report.json"},
        {"step": "6.17", "scope": generated_block_plan["scope"], "report": "docs/openyield_decoder_generated_block_plan_report.json"},
        {"step": "6.18", "scope": preplacement["scope"], "report": "docs/openyield_decoder_preplacement_feasibility_report.json"},
        {"step": "6.19", "scope": handoff_relief["scope"], "report": "docs/openyield_decoder_handoff_relief_report.json"},
        {"step": "6.20", "scope": channel_requirement["scope"], "report": "docs/openyield_decoder_channel_requirement_report.json"},
        {"step": "6.21", "scope": parent_reservation["scope"], "report": "docs/openyield_control_parent_reservation_report.json"},
    ]

    blocker_list = [
        "stage bbox proxies are metadata-only",
        "stage packing is not legalized",
        "composite internal routing is not proven",
        "rail continuity is not proven",
        "shared rail is disabled",
        "wordline handoff windows are metadata proxies",
        "wordline margin is still low even after 2.2um requirement",
        "parent floorplan space for extra 0.2um is not physically proven",
        "level1 enable target physical pin-side proof is still missing",
        "full channel legality is not proven",
        "no DRC/LVS proof exists",
    ]

    report = {
        "scope": "step6_22_openyield_decoder_metadata_closure",
        "closure_name": "DECODER_METADATA_CLOSURE_STEP6",
        "target_block": "DECODER_CASCADE",
        "closure_scope": "Step 6.9 through Step 6.21",
        "addr_width": addr_width,
        "num_rows": 32,
        "metadata_closure_available": True,
        "physical_closure_available": False,
        "decoder_physical_push_should_stop": True,
        "next_focus": "TIME_remaining_control_subblocks",
        "closure_summary": {
            "metadata_chain_complete": True,
            "decoder_metadata_closure_available": True,
            "decoder_metadata_can_be_used_for_future_planning": True,
            "decoder_physical_prototype_allowed": False,
            "decoder_physical_placement_allowed": False,
            "very_limited_control_row_smoke_allowed": False,
        },
        "source_reports": source_reports,
        "closed_metadata_items": closed_items,
        "closed_metadata_items_complete": all(closed_items.values()),
        "decoder_generated_block_plan_status": {
            "plan_name": generated_block_plan["plan_name"],
            "logic_strategy": generated_block_plan["logic_strategy"],
            "level_groups": generated_block_plan["level_groups"],
            "stage_count": 5,
            "level0_stage": "DEC_0_0",
            "level1_stages": ["DEC_1_0", "DEC_1_1", "DEC_1_2", "DEC_1_3"],
            "truth_table_binding_complete": generated_block_plan["truth_table_binding"]["truth_table_binding_complete"],
            "output_contracts_available": output_contracts["decoder_output_contracts_available"],
            "all_level1_outputs_have_handoff_budget": handoff_budget["consistency_checks"]["all_wordline_outputs_have_handoff_budget"],
        },
        "decoder_preplacement_status": {
            "bounded_preplacement_model_available": preplacement["bounded_preplacement_model_available"],
            "metadata_stage_packing_consistent": preplacement["metadata_stage_packing_consistent"],
            "bbox_proxy_overlap_found": preplacement["bbox_proxy_overlap_checks"]["bbox_proxy_conflict_found"],
            "wordline_handoff_budget_is_tight": preplacement["budget_margin_checks"]["wordline_handoff_budget_is_tight"],
        },
        "decoder_channel_requirement_status": {
            "base_wordline_channel_width": channel_requirement["base_width"],
            "recommended_wordline_channel_width": channel_requirement["recommended_width"],
            "old_wordline_margin": channel_requirement["updated_budget_summary"]["old_wordline_margin"],
            "new_wordline_margin": channel_requirement["updated_budget_summary"]["new_wordline_margin"],
            "wordline_margin_still_low": channel_requirement["risk_flags"]["wordline_margin_still_low"],
            "parent_2p2_reservation_recorded": parent_reservation["parent_reservation_recorded"],
            "physical_parent_space_proven": parent_reservation["physical_floorplan_space_proven"],
            "safe_for_metadata_requirement_propagation": channel_requirement["safe_for_metadata_requirement_propagation"],
            "safe_for_physical_floorplan_claim": channel_requirement["safe_for_physical_floorplan_claim"],
        },
        "parent_reservation_status": {
            "reservation_name": parent_reservation["reservation_name"],
            "parent_reservation_required": parent_reservation["parent_reservation_required"],
            "parent_reservation_recorded": parent_reservation["parent_reservation_recorded"],
            "physical_parent_space_proven": parent_reservation["physical_floorplan_space_proven"],
            "safe_for_parent_metadata_planning": parent_reservation["safe_for_parent_metadata_planning"],
            "safe_for_physical_floorplan_claim": parent_reservation["safe_for_physical_floorplan_claim"],
        },
        "open_blockers": blocker_list,
        "physical_blocker_summary": {
            "physical_decoder_placement_blocked_by": blocker_list,
        },
        "risk_summary": {
            "wordline_margin_still_low": True,
            "routing_unproven": True,
            "placement_unproven": True,
            "shared_rail_disabled": True,
            "parent_floorplan_space_unproven": True,
        },
        "decision_summary": {
            "decoder_metadata_line_status": "closed_for_now",
            "decoder_physical_push_status": "stop",
            "recommended_next_phase": "TIME_remaining_control_subblock_audit",
            "reason": [
                "decoder metadata is sufficient as future planning reference",
                "decoder physical prototype remains blocked",
                "further local decoder metadata micro-tuning is not the best next investment",
                "remaining TIME/control subblocks now dominate control-signal generation uncertainty",
            ],
        },
        "next_phase_recommendation": {
            "candidate_directions": [
                "delay_chain_adapter_audit",
                "wen_delay_chain_adapter_audit",
                "pdrive_adapter_audit",
                "wl_pdrive_adapter_audit",
                "precharge_control_adapter_audit",
                "time_control_signal_summary",
            ],
            "recommended_step_6_23": "delay_chain_wen_delay_chain_pdrive_adapter_audit",
            "reason": [
                "TIME should not be treated as one opaque macro",
                "DFF and decoder related metadata has reached closure for now",
                "remaining critical timing/control logic includes delay_chain, wen_delay_chain, pdrive, and wl_pdrive",
                "these subblocks drive sense_enable, write_enable, precharge_enb, and wordline_enable generation",
            ],
        },
        "can_enter_decoder_metadata_future_planning": True,
        "can_enter_decoder_physical_prototype": False,
        "can_enter_physical_decoder_placement": False,
        "can_enter_very_limited_control_row_smoke": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "time_control_decomposition_reference": {
            "scope": time_control["scope"],
            "can_enter_control_subblock_adapter_planning": time_control["can_enter_control_subblock_adapter_planning"],
        },
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": report["closure_name"], "kind": "closure"}]
            + [{"id": item["scope"], "kind": "source_report"} for item in source_reports]
            + [{"id": "TIME_remaining_control_subblocks", "kind": "next_phase"}]
        ),
        "edges": (
            [{"source": report["closure_name"], "target": item["scope"], "relation": "summarizes"} for item in source_reports]
            + [{"source": report["closure_name"], "target": "TIME_remaining_control_subblocks", "relation": "pivots_to"}]
        ),
        "decision_summary": report["decision_summary"],
        "open_blockers": blocker_list,
    }
    return report, graph


def build_decoder_metadata_closure_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Decoder Metadata Closure Report",
        "",
        "This report closes the decoder metadata line for now. It summarizes what is closed, what remains blocked, and why decoder physical push should stop here.",
        "",
        "## Closure Summary",
        "",
        "```json",
        json.dumps(report["closure_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Source Reports",
        "",
        md_table(
            ["step", "scope", "report"],
            [[item["step"], item["scope"], item["report"]] for item in report["source_reports"]],
        ),
        "",
        "## Closed Metadata Checklist",
        "",
        md_table(
            ["item", "closed"],
            [[key, str(value)] for key, value in report["closed_metadata_items"].items()],
        ),
        "",
        "## Generated-Block Plan Status",
        "",
        "```json",
        json.dumps(report["decoder_generated_block_plan_status"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Preplacement / Channel / Parent Reservation Status",
        "",
        "```json",
        json.dumps(
            {
                "decoder_preplacement_status": report["decoder_preplacement_status"],
                "decoder_channel_requirement_status": report["decoder_channel_requirement_status"],
                "parent_reservation_status": report["parent_reservation_status"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## Open Blockers",
        "",
    ]
    lines.extend([f"- {item}" for item in report["open_blockers"]])
    lines.extend(
        [
            "",
            "## Decision Summary",
            "",
            "```json",
            json.dumps(report["decision_summary"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Step 6.23 Recommendation",
            "",
            "```json",
            json.dumps(report["next_phase_recommendation"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)

