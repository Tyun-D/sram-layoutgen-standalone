"""Read-only OpenYield decoder generated-block metadata plan summary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .decoder_stage_candidates import md_table


def _load_json(path: str | Path) -> dict[str, Any]:
    data = Path(path)
    return json.loads(data.read_text(encoding="utf-8"))


def build_decoder_generated_block_plan_report(
    *,
    openyield_root: str | Path,
    tech_dir: str | Path,
    addr_width: int = 5,
    candidate_report_path: str | Path | None = None,
    row_rule_report_path: str | Path | None = None,
    logic_repair_report_path: str | Path | None = None,
    composite_leaf_report_path: str | Path | None = None,
    stage_template_report_path: str | Path | None = None,
    truth_table_report_path: str | Path | None = None,
    output_contract_report_path: str | Path | None = None,
    handoff_budget_report_path: str | Path | None = None,
    control_envelope_report_path: str | Path | None = None,
    control_anchor_report_path: str | Path | None = None,
    time_decomposition_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate_report = _load_json(candidate_report_path or "docs/openyield_decoder_stage_candidate_report.json")
    row_rule_report = _load_json(row_rule_report_path or "docs/openyield_decoder_row_rule_report.json")
    logic_repair_report = _load_json(logic_repair_report_path or "docs/openyield_decoder_logic_repair_report.json")
    composite_leaf_report = _load_json(composite_leaf_report_path or "docs/openyield_decoder_composite_leaf_convention_report.json")
    stage_template_report = _load_json(stage_template_report_path or "docs/openyield_decoder_stage_template_report.json")
    truth_table_report = _load_json(truth_table_report_path or "docs/openyield_decoder_truth_table_binding_report.json")
    output_contract_report = _load_json(output_contract_report_path or "docs/openyield_decoder_output_contract_report.json")
    handoff_budget_report = _load_json(handoff_budget_report_path or "docs/openyield_decoder_output_handoff_budget_report.json")
    control_envelope_report = _load_json(control_envelope_report_path or "docs/openyield_control_target_envelope_report.json")
    control_anchor_report = _load_json(control_anchor_report_path or "docs/openyield_control_anchor_binding_report.json")
    time_decomposition_report = _load_json(time_decomposition_report_path or "docs/openyield_time_control_decomposition_report.json")

    hierarchy = candidate_report["decoder_cascade_hierarchy"]
    level0_stage = next(item for item in hierarchy["stage_instances"] if item["level"] == 0)
    level1_stages = [item for item in hierarchy["stage_instances"] if item["level"] == 1]
    stage_packing = row_rule_report["stage_packing_plan"]
    level0_packing = next(item for item in stage_packing if item["stage_name"] == "DEC_0_0")
    level1_packings = [item for item in stage_packing if item["stage_name"].startswith("DEC_1_")]
    handoff_windows = handoff_budget_report["handoff_windows"]
    wordline_windows = [item for item in handoff_windows if item["window_name"].startswith("WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_")]
    enable_window = next(item for item in handoff_windows if item["window_name"] == "ENABLE_BUS_HANDOFF_WINDOW")
    wordline_budget_groups = handoff_budget_report["wordline_handoff_budget_summary"]["groups"]

    required_sections = {
        "stage_hierarchy": bool(hierarchy["stage_instances"]),
        "stage_templates": stage_template_report["decoder_stage_templates_available"],
        "stage_packing": row_rule_report["decoder_stage_packing_available"],
        "row_rules": row_rule_report["decoder_row_rules_available"],
        "logic_repair_strategy": logic_repair_report["decoder_logic_repair_options_available"],
        "composite_leaf_conventions": composite_leaf_report["decoder_composite_leaf_conventions_available"],
        "truth_table_binding": truth_table_report["truth_table_binding_complete"],
        "output_contracts": output_contract_report["decoder_output_contracts_available"],
        "handoff_budgets": handoff_budget_report["decoder_output_handoff_budget_available"],
        "input_handoff": truth_table_report["handoff_consistency"]["input_handoff_consistent"],
        "enable_bus_handoff": truth_table_report["handoff_consistency"]["level_enable_handoff_consistent"],
        "wordline_output_handoff": truth_table_report["handoff_consistency"]["output_handoff_consistent"],
        "power_policy": stage_template_report["stage_power_policy_available"],
        "bbox_proxy_summary": stage_template_report["stage_bbox_proxy_available"],
        "budget_summary": True,
    }

    consistency_checks = {
        "decoder_stage_candidates_available": candidate_report["decoder_generated_block_plan_available"],
        "decoder_row_rules_available": row_rule_report["decoder_row_rules_available"],
        "decoder_logic_repair_strategy_available": logic_repair_report["decoder_logic_repair_options_available"],
        "decoder_composite_leaf_conventions_available": composite_leaf_report["decoder_composite_leaf_conventions_available"],
        "decoder_stage_templates_available": stage_template_report["decoder_stage_templates_available"],
        "decoder_truth_table_binding_complete": truth_table_report["truth_table_binding_complete"],
        "decoder_output_contracts_available": output_contract_report["decoder_output_contracts_available"],
        "decoder_output_handoff_budget_available": handoff_budget_report["decoder_output_handoff_budget_available"],
        "input_handoff_consistent": truth_table_report["handoff_consistency"]["input_handoff_consistent"],
        "level_enable_handoff_consistent": truth_table_report["handoff_consistency"]["level_enable_handoff_consistent"],
        "wordline_output_handoff_consistent": truth_table_report["handoff_consistency"]["output_handoff_consistent"],
        "unused_enable_outputs_not_routed": handoff_budget_report["consistency_checks"]["unused_enable_outputs_not_routed"],
        "all_required_sections_present": all(required_sections.values()),
        "metadata_chain_complete": all(required_sections.values()),
        "physical_routing_proven": False,
    }

    report = {
        "scope": "step6_17_openyield_decoder_generated_block_plan_summary",
        "plan_name": "DECODER_CASCADE_GENERATED_BLOCK_PLAN",
        "target_block": "DECODER_CASCADE",
        "addr_width": addr_width,
        "num_rows": 32,
        "n_levels": hierarchy["n_levels"],
        "level_groups": hierarchy["level_groups"],
        "source_strategy": "OpenYield decoder.py + metadata audits",
        "logic_strategy": "metadata_composite_nand2_inv",
        "metadata_only": True,
        "physical_layout_generated": False,
        "physical_routing_proven": False,
        "stage_hierarchy": {
            "level_0": {
                "stage_count": 1,
                "stage": "DEC_0_0",
                "role": "intermediate_enable_bus",
                "template": "DECODER_LEVEL0_STAGE_TEMPLATE",
                "inputs": ["A3", "A4", "VSS"],
                "enable": "VDD",
                "outputs": level0_stage["output_nets"],
                "consumed_outputs": output_contract_report["level0_output_expansion"]["downstream_consumed_enable_outputs"],
                "unconsumed_outputs": output_contract_report["level0_output_expansion"]["unused_or_unconsumed_enable_outputs"],
            },
            "level_1": {
                "stage_count": 4,
                "stages": [item["stage_name"] for item in level1_stages],
                "role": "wordline_outputs",
                "template": "DECODER_LEVEL1_STAGE_TEMPLATE",
                "inputs": ["A0", "A1", "A2"],
                "enables": [item["enable_net"] for item in level1_stages],
                "outputs": [net for item in level1_stages for net in item["output_nets"]],
            },
        },
        "stage_templates": {
            "DECODER3_8_STAGE_TEMPLATE": True,
            "DECODER_LEVEL0_STAGE_TEMPLATE": True,
            "DECODER_LEVEL1_STAGE_TEMPLATE": True,
            "stage_pin_slots_available": stage_template_report["stage_pin_slots_available"],
            "stage_internal_net_zones_available": stage_template_report["stage_internal_net_zones_available"],
            "stage_bbox_proxy_available": stage_template_report["stage_bbox_proxy_available"],
            "stage_power_policy_available": stage_template_report["stage_power_policy_available"],
        },
        "stage_packing": {
            "stage_count": len(stage_packing),
            "level0_bbox_proxy": level0_packing["candidate_bbox"],
            "level1_bbox_proxies": {item["stage_name"]: item["candidate_bbox"] for item in level1_packings},
            "stage_bbox_proxy_policy": "pessimistic_linear_macro_proxy_from_row_rules",
            "stage_bbox_proxy_is_metadata_only": True,
            "stage_bbox_proxy_not_legal_physical_layout": True,
        },
        "row_rules": {
            "row_rule_names": [item["rule_name"] for item in row_rule_report["decoder_row_rules"]],
            "level0_power_policy": row_rule_report["decoder_row_rules"][0]["power_policy"],
            "level1_power_policy": row_rule_report["decoder_row_rules"][1]["power_policy"],
            "safe_for_shared_rail": False,
        },
        "logic_repair_strategy": {
            "recommended_decoder_logic_strategy": logic_repair_report["recommended_decoder_logic_strategy"],
            "direct_pnand3_exists": logic_repair_report["direct_pnand3_exists"],
            "direct_and3_exists": logic_repair_report["direct_and3_exists"],
            "gen_nand4_proxy_only": logic_repair_report["gen_nand4_proxy_only"],
            "gen_nand4_safe_for_physical_substitution": logic_repair_report["gen_nand4_safe_for_physical_substitution"],
        },
        "composite_leaf_conventions": {
            "pnand3_composite_convention_available": composite_leaf_report["pnand3_composite_convention_available"],
            "and3_composite_convention_available": composite_leaf_report["and3_composite_convention_available"],
            "leaf_pin_metadata_complete": composite_leaf_report["leaf_pin_metadata_complete"],
            "leaf_power_metadata_complete": composite_leaf_report["leaf_power_metadata_complete"],
            "composite_internal_net_routing_proven": composite_leaf_report["composite_internal_net_routing_proven"],
            "composite_rail_continuity_proven": composite_leaf_report["composite_rail_continuity_proven"],
            "convention_names": [item["convention_name"] for item in composite_leaf_report["composite_leaf_conventions"]],
        },
        "truth_table_binding": {
            "truth_table_binding_complete": truth_table_report["truth_table_binding_complete"],
            "requires_decoder_truth_table_binding": truth_table_report["requires_decoder_truth_table_binding"],
            "input_handoff_consistent": truth_table_report["handoff_consistency"]["input_handoff_consistent"],
            "level_enable_handoff_consistent": truth_table_report["handoff_consistency"]["level_enable_handoff_consistent"],
            "wordline_output_handoff_consistent": truth_table_report["handoff_consistency"]["output_handoff_consistent"],
            "wordline_driver_semantics_confirmed": truth_table_report["handoff_consistency"]["wordline_driver_semantics_confirmed"],
        },
        "output_contracts": {
            "local_contract_count": len(output_contract_report["generic_output_contracts"]),
            "contract_names": [item["contract_name"] for item in output_contract_report["generic_output_contracts"]],
            "all_local_outputs_have_contract": output_contract_report["consistency_checks"]["all_local_outputs_have_contract"],
            "all_level0_outputs_have_expansion": output_contract_report["consistency_checks"]["all_level0_outputs_have_expansion"],
            "all_level1_outputs_have_expansion": output_contract_report["consistency_checks"]["all_level1_outputs_have_expansion"],
        },
        "handoff_budgets": {
            "wordline_handoff_group_count": len(wordline_windows),
            "wordline_outputs": handoff_budget_report["level1_wordline_handoff_summary"]["total_wordline_handoffs"],
            "all_wordline_outputs_have_handoff_budget": handoff_budget_report["consistency_checks"]["all_wordline_outputs_have_handoff_budget"],
            "wordline_handoff_budget_pass": handoff_budget_report["consistency_checks"]["wordline_handoff_budget_pass"],
            "wordline_handoff_budget_is_tight": all(
                item["estimated_required_width"] == item["available_width"] for item in wordline_budget_groups
            ),
            "wordline_group_required_width": wordline_budget_groups[0]["estimated_required_width"],
            "wordline_group_available_width": wordline_budget_groups[0]["available_width"],
            "consumed_enable_outputs": handoff_budget_report["consumed_enable_handoff_count"],
            "unused_enable_outputs": handoff_budget_report["unused_enable_output_count"],
            "all_consumed_enable_outputs_have_handoff_budget": handoff_budget_report["consistency_checks"]["all_consumed_enable_outputs_have_handoff_budget"],
            "unused_enable_outputs_not_routed": handoff_budget_report["consistency_checks"]["unused_enable_outputs_not_routed"],
            "enable_handoff_budget_pass": handoff_budget_report["consistency_checks"]["enable_handoff_budget_pass"],
            "enable_required_width": handoff_budget_report["enable_handoff_budget_summary"]["estimated_required_width"],
            "enable_available_width": handoff_budget_report["enable_handoff_budget_summary"]["available_width"],
            "physical_routing_proven": False,
        },
        "input_handoff": {
            "anchor_name": control_envelope_report["decoder_input_anchor_summary"]["anchor_name"],
            "source_window": control_envelope_report["decoder_input_anchor_summary"]["source_window"],
            "side_hint": control_envelope_report["decoder_input_anchor_summary"]["side_hint"],
            "metadata_only": True,
            "physical_access_proven": False,
        },
        "enable_bus_handoff": {
            "consumed_outputs": output_contract_report["level0_output_expansion"]["downstream_consumed_enable_outputs"],
            "unused_outputs": output_contract_report["level0_output_expansion"]["unused_or_unconsumed_enable_outputs"],
            "window_name": enable_window["window_name"],
            "metadata_only": True,
            "physical_routing_proven": False,
        },
        "wordline_output_handoff": {
            "window_names": [item["window_name"] for item in wordline_windows],
            "downstream_consumer": "WORDLINEDRIVER",
            "consumer_pin": "A",
            "wordline_driver_access_targets": len(handoff_budget_report["consumer_access_targets"]["wordline_driver_a_targets"]),
            "metadata_only": True,
            "physical_routing_proven": False,
        },
        "power_policy": {
            "decoder_power_policy": "local_horizontal_vdd_gnd_only_no_shared_rail",
            "safe_for_shared_rail": False,
            "rail_continuity_proven": False,
            "stage_power_policy_available": stage_template_report["stage_power_policy_available"],
            "leaf_power_metadata_complete": composite_leaf_report["leaf_power_metadata_complete"],
            "composite_rail_continuity_proven": composite_leaf_report["composite_rail_continuity_proven"],
        },
        "bbox_proxy_summary": {
            "bbox_proxy_is_metadata_only": True,
            "bbox_proxy_not_legal_physical_layout": True,
            "stage_bbox_proxy_policy": "pessimistic_linear_macro_proxy_from_row_rules",
            "stage_bbox_proxy_width": level0_packing["candidate_bbox"]["width"],
            "stage_bbox_proxy_height": level0_packing["candidate_bbox"]["height"],
            "composite_leaf_bbox_proxy": {
                item["convention_name"]: item["bbox_proxy"] for item in composite_leaf_report["composite_leaf_conventions"]
            },
            "handoff_window_bbox_proxy": {
                item["window_name"]: {"width": item["width"], "height": item["height"]}
                for item in handoff_windows
            },
        },
        "budget_summary": {
            "route_pitch": handoff_budget_report["inputs"]["route_pitch"],
            "route_margin": handoff_budget_report["inputs"]["route_margin"],
            "wordline_channel_width": handoff_budget_report["inputs"]["wordline_channel_width"],
            "enable_channel_width": handoff_budget_report["inputs"]["enable_channel_width"],
            "wordline_handoff_budget_is_tight": all(
                item["estimated_required_width"] == item["available_width"] for item in wordline_budget_groups
            ),
        },
        "consistency_checks": consistency_checks,
        "blockers": [
            "bbox proxies are metadata-only",
            "stage packing is not legalized",
            "composite internal net routing is not proven",
            "rail continuity is not proven",
            "shared rail is disabled",
            "handoff windows are metadata proxies",
            "wordline budget is tight and not a routing proof",
            "decoder level1 enable target physical pin-side proof is missing",
            "full channel legality is not proven",
        ],
        "decoder_generated_block_plan_available": True,
        "metadata_chain_complete": consistency_checks["metadata_chain_complete"],
        "all_required_sections_present": consistency_checks["all_required_sections_present"],
        "can_enter_decoder_generated_block_planning": True,
        "can_enter_decoder_preplacement_feasibility": consistency_checks["metadata_chain_complete"],
        "can_enter_physical_decoder_placement": False,
        "can_enter_very_limited_control_row_smoke": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "next_step_recommendation": "Step 6.18 should perform decoder pre-placement feasibility: validate whether the metadata stage rows, bbox proxies, and tight wordline budget can be turned into a bounded prototype packing study without claiming legal placement.",
        "source_reports": {
            "candidate": candidate_report.get("scope"),
            "row_rules": row_rule_report.get("scope"),
            "logic_repair": logic_repair_report.get("scope"),
            "composite_leaf": composite_leaf_report.get("scope"),
            "stage_templates": stage_template_report.get("scope"),
            "truth_table": truth_table_report.get("scope"),
            "output_contracts": output_contract_report.get("scope"),
            "handoff_budgets": handoff_budget_report.get("scope"),
            "control_envelope": control_envelope_report.get("scope"),
            "control_anchor": control_anchor_report.get("scope"),
            "time_decomposition": time_decomposition_report.get("scope"),
        },
    }

    graph = {
        "scope": report["scope"],
        "nodes": [
            {"id": "DECODER_CASCADE_GENERATED_BLOCK_PLAN", "kind": "plan"},
            {"id": "DEC_0_0", "kind": "stage"},
            {"id": "DEC_1_0", "kind": "stage"},
            {"id": "DEC_1_1", "kind": "stage"},
            {"id": "DEC_1_2", "kind": "stage"},
            {"id": "DEC_1_3", "kind": "stage"},
            {"id": "DECODER_LEVEL0_STAGE_TEMPLATE", "kind": "template"},
            {"id": "DECODER_LEVEL1_STAGE_TEMPLATE", "kind": "template"},
            {"id": "DECODER3_8_OUTPUT_CONTRACT_WL*", "kind": "contract_family"},
            {"id": "WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_*", "kind": "handoff_window_family"},
        ],
        "edges": [
            {"source": "DECODER_CASCADE_GENERATED_BLOCK_PLAN", "target": "DEC_0_0", "relation": "contains"},
            {"source": "DECODER_CASCADE_GENERATED_BLOCK_PLAN", "target": "DEC_1_0", "relation": "contains"},
            {"source": "DECODER_CASCADE_GENERATED_BLOCK_PLAN", "target": "DEC_1_1", "relation": "contains"},
            {"source": "DECODER_CASCADE_GENERATED_BLOCK_PLAN", "target": "DEC_1_2", "relation": "contains"},
            {"source": "DECODER_CASCADE_GENERATED_BLOCK_PLAN", "target": "DEC_1_3", "relation": "contains"},
            {"source": "DEC_0_0", "target": "DECODER_LEVEL0_STAGE_TEMPLATE", "relation": "uses_template"},
            {"source": "DEC_1_0", "target": "DECODER_LEVEL1_STAGE_TEMPLATE", "relation": "uses_template"},
            {"source": "DEC_1_1", "target": "DECODER_LEVEL1_STAGE_TEMPLATE", "relation": "uses_template"},
            {"source": "DEC_1_2", "target": "DECODER_LEVEL1_STAGE_TEMPLATE", "relation": "uses_template"},
            {"source": "DEC_1_3", "target": "DECODER_LEVEL1_STAGE_TEMPLATE", "relation": "uses_template"},
            {"source": "DECODER_LEVEL1_STAGE_TEMPLATE", "target": "DECODER3_8_OUTPUT_CONTRACT_WL*", "relation": "expands_outputs"},
            {"source": "DECODER3_8_OUTPUT_CONTRACT_WL*", "target": "WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_*", "relation": "feeds_handoff"},
        ],
        "consistency_checks": consistency_checks,
        "blockers": report["blockers"],
    }
    return report, graph


def build_decoder_generated_block_plan_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Decoder Generated Block Plan Summary",
        "",
        "This report summarizes the decoder metadata chain as a generated-block pre-placement plan. It remains metadata-only and does not create legal physical placement, routing, or GDS.",
        "",
        "## Plan Summary",
        "",
        f"- plan_name: `{report['plan_name']}`",
        f"- target_block: `{report['target_block']}`",
        f"- addr_width: `{report['addr_width']}`",
        f"- num_rows: `{report['num_rows']}`",
        f"- metadata_chain_complete: `{report['metadata_chain_complete']}`",
        f"- can_enter_decoder_generated_block_planning: `{report['can_enter_decoder_generated_block_planning']}`",
        f"- can_enter_decoder_preplacement_feasibility: `{report['can_enter_decoder_preplacement_feasibility']}`",
        f"- can_enter_physical_decoder_placement: `{report['can_enter_physical_decoder_placement']}`",
        f"- can_enter_very_limited_control_row_smoke: `{report['can_enter_very_limited_control_row_smoke']}`",
        "",
        "## Stage Hierarchy",
        "",
        "```json",
        json.dumps(report["stage_hierarchy"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Logic Strategy",
        "",
        "```json",
        json.dumps(report["logic_repair_strategy"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Composite Leaf Convention Summary",
        "",
        "```json",
        json.dumps(report["composite_leaf_conventions"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Output Contract / Truth Table Summary",
        "",
        "```json",
        json.dumps(
            {
                "truth_table_binding": report["truth_table_binding"],
                "output_contracts": report["output_contracts"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## Handoff Budget Summary",
        "",
        "```json",
        json.dumps(report["handoff_budgets"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## BBox Proxy Summary",
        "",
        "```json",
        json.dumps(report["bbox_proxy_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Power / Rail Policy",
        "",
        "```json",
        json.dumps(report["power_policy"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Consistency Checks",
        "",
        md_table(
            ["check", "value"],
            [[key, str(value)] for key, value in report["consistency_checks"].items()],
        ),
        "",
        "## Blockers",
        "",
    ]
    lines.extend([f"- {item}" for item in report["blockers"]])
    lines.extend(
        [
            "",
            "## Step 6.18 Recommendation",
            "",
            report["next_step_recommendation"],
            "",
        ]
    )
    return "\n".join(lines)

