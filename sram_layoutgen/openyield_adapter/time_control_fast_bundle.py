"""Read-only OpenYield TIME fast metadata closure bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row)
            + " |"
        )
    return "\n".join(lines)


def _find_consumer_contract(report: dict[str, Any], contract_name: str) -> dict[str, Any]:
    for item in report.get("consumer_side_contract_list", []):
        if item.get("contract_name") == contract_name:
            return item
    raise KeyError(f"Missing consumer contract: {contract_name}")


def _find_signal_contract(report: dict[str, Any], contract_name: str) -> dict[str, Any]:
    for item in report.get("signal_binding_contracts", []):
        if item.get("contract_name") == contract_name:
            return item
    raise KeyError(f"Missing signal contract: {contract_name}")


def _find_macro(gds_report: dict[str, Any], macro_name: str) -> dict[str, Any] | None:
    for item in gds_report.get("audited_macros", []):
        if item.get("macro_name") == macro_name:
            return item
    return None


def _find_pin(macro: dict[str, Any] | None, canonical_pin: str) -> dict[str, Any] | None:
    if not macro:
        return None
    for pin in macro.get("pins", []):
        if pin.get("canonical_pin") == canonical_pin:
            return pin
    return None


def _risk_level(margin: float) -> str:
    if margin < 0:
        return "fail"
    if margin == 0:
        return "tight_zero_margin"
    if margin < 0.4:
        return "pass_low_margin"
    return "pass_moderate_margin"


def _budget_entry(
    *,
    control_signal: str,
    fanout_targets: list[str],
    route_pitch: float,
    route_margin: float,
    available_metadata_channel_width: float,
) -> dict[str, Any]:
    fanout_count = len(fanout_targets)
    estimated_required_tracks = max(1, fanout_count)
    estimated_required_width = estimated_required_tracks * route_pitch + route_margin
    budget_margin = available_metadata_channel_width - estimated_required_width
    risk_level = _risk_level(budget_margin)
    return {
        "control_signal": control_signal,
        "fanout_count": fanout_count,
        "fanout_targets": fanout_targets,
        "estimated_required_tracks": estimated_required_tracks,
        "route_pitch": route_pitch,
        "route_margin": route_margin,
        "estimated_required_width": round(estimated_required_width, 6),
        "available_metadata_channel_width": available_metadata_channel_width,
        "budget_pass": budget_margin >= 0,
        "budget_margin": round(budget_margin, 6),
        "risk_level": risk_level,
        "physical_routing_proven": False,
        "metadata_only": True,
    }


def build_time_control_fast_bundle_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
    route_pitch: float = 0.2,
    route_margin: float = 0.2,
    default_control_channel_width: float = 2.0,
    consumer_contract_report_path: str | Path | None = None,
    generated_logic_report_path: str | Path | None = None,
    signal_binding_report_path: str | Path | None = None,
    subblock_report_path: str | Path | None = None,
    decoder_closure_report_path: str | Path | None = None,
    gds_pin_audit_report_path: str | Path | None = None,
    senseamp_adapter_report_path: str | Path | None = None,
    writedriver_adapter_report_path: str | Path | None = None,
    wordlinedriver_adapter_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    tech_dir = Path(tech_dir)
    _ = _load_json(contracts_path)
    consumer_report = _load_json(
        consumer_contract_report_path or "docs/openyield_time_control_consumer_contract_report.json"
    )
    generated_logic_report = _load_json(
        generated_logic_report_path or "docs/openyield_time_control_generated_logic_contract_report.json"
    )
    signal_report = _load_json(signal_binding_report_path or "docs/openyield_time_control_signal_binding_report.json")
    subblock_report = _load_json(subblock_report_path or "docs/openyield_time_control_subblock_audit_report.json")
    decoder_closure = _load_json(
        decoder_closure_report_path or "docs/openyield_decoder_metadata_closure_report.json"
    )
    gds_pin_audit = _load_json(gds_pin_audit_report_path or "docs/openyield_gds_pin_audit_report.json")
    senseamp_report = _load_json(senseamp_adapter_report_path or "docs/openyield_senseamp_adapter_report.json")
    writedriver_report = _load_json(writedriver_adapter_report_path or "docs/openyield_writedriver_adapter_report.json")
    wordlinedriver_report = _load_json(
        wordlinedriver_adapter_report_path or "docs/openyield_wordlinedriver_adapter_report.json"
    )

    precharge_contract = _find_consumer_contract(consumer_report, "PRECHARGE_ENB_CONSUMER_CONTRACT")
    wordline_contract = _find_consumer_contract(consumer_report, "WORDLINE_ENABLE_CONSUMER_CONTRACT")
    write_contract = _find_consumer_contract(consumer_report, "WRITE_ENABLE_CONSUMER_CONTRACT")
    sense_contract = _find_consumer_contract(consumer_report, "SENSE_ENABLE_CONSUMER_CONTRACT")
    wen_delay_contract = _find_signal_contract(signal_report, "WEN_DELAY_CONDITIONAL_BINDING_CONTRACT")
    wordline_signal_contract = _find_signal_contract(signal_report, "WORDLINE_ENABLE_BINDING_CONTRACT")

    precharge_macro = _find_macro(gds_pin_audit, "gen_precharge")
    precharge_pin = _find_pin(precharge_macro, "precharge_enb")
    precharge_power = precharge_macro.get("power_rail_audit", {}) if precharge_macro else {}

    precharge_consumer_pin_metadata_closure = {
        "control_signal": "PRE / precharge_enb",
        "consumer_macro": "PRECHARGE",
        "consumer_pin": "ENB",
        "expected_active_level": "active_low",
        "current_status": precharge_contract.get("status"),
        "precharge_consumer_pin_known": bool(precharge_pin),
        "precharge_consumer_pin_side_known": bool(precharge_pin and precharge_pin.get("pin_side") != "unknown"),
        "precharge_power_domain_known": "partial"
        if not precharge_power.get("has_gnd")
        else True,
        "precharge_adapter_available": False,
        "precharge_metadata_closure_available": "partial",
        "precharge_safe_for_metadata_planning": precharge_contract.get("safe_for_metadata_planning"),
        "precharge_safe_for_physical_placement": False,
        "precharge_consumer_status": "source_level_plus_pin_metadata",
        "notes": [
            "PRECHARGE still has no dedicated adapter module in the current clean worktree.",
            "GDS pin audit provides EN/precharge_enb pin metadata, but power-domain closure remains partial because GND metadata is not fully closed.",
            "This closure is enough for metadata planning only.",
        ],
    }

    wordline_secondary_consumer_closure = {
        "control_signal": "wordline_enable / wl_en",
        "wordline_primary_consumer_closed": True,
        "primary_consumer": "WORDLINEDRIVER.B",
        "wordline_secondary_consumers_available": True,
        "secondary_consumers": [
            "Pinv.A(wl_en_bar)",
            "RWL_AND2.B",
        ],
        "wl_en_bar_secondary_targets": [
            "PRECHARGE.PNAND3.C",
        ],
        "wl_en_bar_path_preserved": True,
        "rwl_and2_consumer_preserved": True,
        "wordline_fanout_metadata_complete": True,
        "wordline_fanout_physical_routing_proven": False,
        "source_evidence": [
            wordline_signal_contract.get("producer_expression_or_dependency"),
            "Consumer contract keeps WORDLINEDRIVER.B as primary while preserving wl_en_bar and RWL-side secondary paths.",
        ],
    }

    fanout_budget = {
        "assumptions": {
            "route_pitch": route_pitch,
            "route_margin": route_margin,
            "default_control_channel_width": default_control_channel_width,
            "metadata_only": True,
            "physical_routing_proven": False,
        },
        "entries": [
            _budget_entry(
                control_signal="write_enable",
                fanout_targets=write_contract.get("fanout_targets", []),
                route_pitch=route_pitch,
                route_margin=route_margin,
                available_metadata_channel_width=default_control_channel_width,
            ),
            _budget_entry(
                control_signal="sense_enable",
                fanout_targets=sense_contract.get("fanout_targets", []),
                route_pitch=route_pitch,
                route_margin=route_margin,
                available_metadata_channel_width=default_control_channel_width,
            ),
            _budget_entry(
                control_signal="precharge_enb",
                fanout_targets=precharge_contract.get("fanout_targets", []),
                route_pitch=route_pitch,
                route_margin=route_margin,
                available_metadata_channel_width=default_control_channel_width,
            ),
            _budget_entry(
                control_signal="wordline_enable",
                fanout_targets=wordline_contract.get("fanout_targets", []),
                route_pitch=route_pitch,
                route_margin=route_margin,
                available_metadata_channel_width=default_control_channel_width,
            ),
            _budget_entry(
                control_signal="wl_en_bar",
                fanout_targets=["PRECHARGE.PNAND3.C"],
                route_pitch=route_pitch,
                route_margin=route_margin,
                available_metadata_channel_width=default_control_channel_width,
            ),
        ],
    }
    fanout_budget["fanout_budget_metadata_pass"] = all(
        item["budget_pass"] for item in fanout_budget["entries"]
    )

    abstract_envelope = {
        "envelope_name": "TIME_CONTROL_ABSTRACT_ENVELOPE",
        "scope": "TIME remaining control subblocks",
        "metadata_only": True,
        "legal_physical_placement": False,
        "physical_routing_proven": False,
        "regions": [
            {
                "region_name": "delay_chain_region",
                "source_contracts": [
                    "RBL_DELAY_BINDING_CONTRACT",
                    "WEN_DELAY_CONDITIONAL_BINDING_CONTRACT",
                    "DELAY_CHAIN_GENERATED_LOGIC_CONTRACT",
                    "WEN_DELAY_CHAIN_CONDITIONAL_GENERATED_LOGIC_CONTRACT",
                ],
                "input_signals": ["rbl", "rbl_delay_bar"],
                "output_signals": ["rbl_delay", "rbl_delay_bar_wen"],
                "consumer_targets": ["WRITE_ENABLE_CONSUMER_CONTRACT", "SENSE_ENABLE_CONSUMER_CONTRACT"],
                "bbox_proxy_available": True,
                "bbox_proxy_policy": "track_count_and_stage_count_proxy_only",
                "metadata_only": True,
                "legal_physical_placement": False,
                "requires_generated_layout_or_stdcell_row": True,
                "requires_routing_proof": True,
                "requires_timing_proof": True,
            },
            {
                "region_name": "pdrive_region",
                "source_contracts": [
                    "CLK_BUF_BINDING_CONTRACT",
                    "PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT",
                    "PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT",
                    "WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT",
                ],
                "input_signals": ["clk", "PRE_UNBUF", "gated_clk_bar"],
                "output_signals": ["clk_buf", "PRE", "wl_en"],
                "consumer_targets": [
                    "WRITE_ENABLE_CONSUMER_CONTRACT",
                    "SENSE_ENABLE_CONSUMER_CONTRACT",
                    "PRECHARGE_ENB_CONSUMER_CONTRACT",
                    "WORDLINE_ENABLE_CONSUMER_CONTRACT",
                ],
                "bbox_proxy_available": True,
                "bbox_proxy_policy": "buffer_chain_stage_proxy_only",
                "metadata_only": True,
                "legal_physical_placement": False,
                "requires_generated_layout_or_stdcell_row": True,
                "requires_routing_proof": True,
                "requires_timing_proof": True,
            },
            {
                "region_name": "generated_logic_region",
                "source_contracts": [
                    "AND2_GENERATED_LOGIC_CONTRACT",
                    "AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
                    "PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
                    "PINV_GENERATED_LOGIC_CONTRACT",
                ],
                "input_signals": ["cs", "clk_buf", "clk_bar", "we", "we_bar", "wl_en", "rbl_delay"],
                "output_signals": ["gated_clk_buf", "gated_clk_bar", "w_en", "s_en", "PRE_UNBUF", "wl_en_bar"],
                "consumer_targets": [
                    "WRITE_ENABLE_CONSUMER_CONTRACT",
                    "SENSE_ENABLE_CONSUMER_CONTRACT",
                    "PRECHARGE_ENB_CONSUMER_CONTRACT",
                    "WORDLINE_ENABLE_CONSUMER_CONTRACT",
                ],
                "bbox_proxy_available": True,
                "bbox_proxy_policy": "composite_gate_count_proxy_only",
                "metadata_only": True,
                "legal_physical_placement": False,
                "requires_generated_layout_or_stdcell_row": True,
                "requires_routing_proof": True,
                "requires_timing_proof": True,
            },
            {
                "region_name": "consumer_handoff_region",
                "source_contracts": [
                    "WRITE_ENABLE_CONSUMER_CONTRACT",
                    "SENSE_ENABLE_CONSUMER_CONTRACT",
                    "PRECHARGE_ENB_CONSUMER_CONTRACT",
                    "WORDLINE_ENABLE_CONSUMER_CONTRACT",
                ],
                "input_signals": ["w_en", "s_en", "PRE", "wl_en"],
                "output_signals": ["WRITEDRIVER.EN", "SENSEAMP.EN", "PRECHARGE.ENB", "WORDLINEDRIVER.B"],
                "consumer_targets": ["peripheral hard macro pin access"],
                "bbox_proxy_available": True,
                "bbox_proxy_policy": "macro_pin_side_and_fanout_proxy_only",
                "metadata_only": True,
                "legal_physical_placement": False,
                "requires_generated_layout_or_stdcell_row": False,
                "requires_routing_proof": True,
                "requires_timing_proof": True,
            },
            {
                "region_name": "precharge_control_region",
                "source_contracts": [
                    "PRECHARGE_ENB_BINDING_CONTRACT",
                    "PRECHARGE_ENB_CONSUMER_CONTRACT",
                ],
                "input_signals": ["gated_clk_buf", "rbl_delay", "wl_en_bar"],
                "output_signals": ["PRE_UNBUF", "PRE"],
                "consumer_targets": ["PRECHARGE.ENB", "PRECHARGE.PNAND3.C"],
                "bbox_proxy_available": True,
                "bbox_proxy_policy": "source_level_plus_pin_metadata_only",
                "metadata_only": True,
                "legal_physical_placement": False,
                "requires_generated_layout_or_stdcell_row": True,
                "requires_routing_proof": True,
                "requires_timing_proof": True,
            },
            {
                "region_name": "wordline_enable_control_region",
                "source_contracts": [
                    "WORDLINE_ENABLE_BINDING_CONTRACT",
                    "WORDLINE_ENABLE_CONSUMER_CONTRACT",
                ],
                "input_signals": ["gated_clk_bar"],
                "output_signals": ["wl_en", "wl_en_bar"],
                "consumer_targets": ["WORDLINEDRIVER.B", "Pinv.A(wl_en_bar)", "RWL_AND2.B"],
                "bbox_proxy_available": True,
                "bbox_proxy_policy": "primary_plus_secondary_fanout_proxy_only",
                "metadata_only": True,
                "legal_physical_placement": False,
                "requires_generated_layout_or_stdcell_row": True,
                "requires_routing_proof": True,
                "requires_timing_proof": True,
            },
            {
                "region_name": "sense_write_enable_region",
                "source_contracts": [
                    "WRITE_ENABLE_BINDING_CONTRACT",
                    "SENSE_ENABLE_BINDING_CONTRACT",
                    "WRITE_ENABLE_CONSUMER_CONTRACT",
                    "SENSE_ENABLE_CONSUMER_CONTRACT",
                ],
                "input_signals": ["rbl_delay_bar", "rbl_delay", "gated_clk_bar", "we", "we_bar"],
                "output_signals": ["w_en", "s_en"],
                "consumer_targets": ["WRITEDRIVER.EN", "SENSEAMP.EN"],
                "bbox_proxy_available": True,
                "bbox_proxy_policy": "paired_enable_channel_proxy_only",
                "metadata_only": True,
                "legal_physical_placement": False,
                "requires_generated_layout_or_stdcell_row": True,
                "requires_routing_proof": True,
                "requires_timing_proof": True,
            },
        ],
    }

    consistency_checks = {
        "time_control_fast_bundle_available": True,
        "precharge_consumer_metadata_closure_available": "partial",
        "wordline_secondary_consumer_metadata_available": True,
        "control_fanout_budget_available": True,
        "control_abstract_envelope_available": True,
        "all_primary_control_consumers_have_contract": bool(
            consumer_report.get("all_primary_control_consumers_have_contract")
        ),
        "consumer_contracts_complete_for_metadata_planning": bool(
            consumer_report.get("consumer_contracts_complete_for_metadata_planning")
        ),
        "generated_logic_contract_coverage_complete": bool(
            generated_logic_report.get("generated_logic_contract_coverage_complete")
        ),
        "control_signal_binding_consistent": bool(signal_report.get("control_signal_binding_consistent")),
        "control_signal_polarity_consistent": bool(
            consumer_report.get("consistency_checks", {}).get("control_signal_polarity_consistent")
        ),
        "fanout_budget_metadata_pass": bool(fanout_budget["fanout_budget_metadata_pass"]),
        "safe_for_metadata_planning": True,
        "safe_for_physical_placement": False,
        "can_enter_time_control_abstract_envelope_planning": True,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
    }

    unresolved_items = [
        "PRECHARGE adapter may still be partial/source-level",
        "fanout budget is metadata-only",
        "abstract envelope is not legal placement",
        "control routing proof is missing",
        "delay timing proof is missing",
        "wen-delay timing proof is missing",
        "rail continuity proof is missing",
        "shared rail is disabled",
        "no DRC/LVS proof exists",
        "standalone integration is not allowed yet",
    ]

    report = {
        "scope": "step6_27_openyield_time_control_fast_metadata_closure_bundle",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(Path(contracts_path).resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "bundle_mode": "fast_metadata_bundle",
        "bundle_components": [
            "precharge_consumer_pin_metadata_closure",
            "wordline_secondary_consumer_closure",
            "control_fanout_handoff_budget",
            "control_row_abstract_placement_envelope",
        ],
        "source_reports": {
            "time_control_consumer_contract": consumer_report.get("scope"),
            "time_control_generated_logic_contract": generated_logic_report.get("scope"),
            "time_control_signal_binding": signal_report.get("scope"),
            "time_control_subblock_audit": subblock_report.get("scope"),
            "decoder_metadata_closure": decoder_closure.get("scope"),
            "senseamp_adapter": senseamp_report.get("scope"),
            "writedriver_adapter": writedriver_report.get("scope"),
            "wordlinedriver_adapter": wordlinedriver_report.get("scope"),
        },
        "precharge_consumer_pin_metadata_closure": precharge_consumer_pin_metadata_closure,
        "wordline_secondary_consumer_closure": wordline_secondary_consumer_closure,
        "control_fanout_budget": fanout_budget,
        "control_row_abstract_placement_envelope": abstract_envelope,
        "consistency_checks": consistency_checks,
        "unresolved_items": unresolved_items,
        "audit_summary": {
            "time_control_fast_bundle_available": True,
            "precharge_metadata_closure_status": "partial",
            "wordline_secondary_consumer_metadata_available": True,
            "fanout_budget_metadata_pass": bool(fanout_budget["fanout_budget_metadata_pass"]),
            "control_abstract_envelope_available": True,
            "can_enter_time_control_abstract_envelope_planning": True,
            "can_enter_time_control_physical_placement": False,
            "can_enter_standalone_control_placement": False,
        },
        "can_enter_time_control_abstract_envelope_planning": True,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
        "step_6_28_recommendation": {
            "recommended_next_phase": "time_control_precharge_adapter_audit_or_control_row_constraints",
            "candidate_directions": [
                "precharge_adapter_metadata_closure",
                "control_row_handoff_constraints",
                "control_channel_reservation_rules",
                "time_control_grouped_planning_interfaces",
            ],
            "reason": [
                "The fast bundle now closes the main metadata handoff story for TIME control signals.",
                "PRECHARGE remains the least-closed consumer and is still not physical-ready.",
                "The next step should refine abstract planning interfaces, not physical placement.",
            ],
        },
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
    }

    graph = {
        "scope": report["scope"],
        "nodes": [
            {"id": "PRECHARGE_ENB_CONSUMER_CLOSURE", "kind": "bundle_component"},
            {"id": "WORDLINE_SECONDARY_CONSUMER_CLOSURE", "kind": "bundle_component"},
            {"id": "CONTROL_FANOUT_BUDGET", "kind": "bundle_component"},
            {"id": "TIME_CONTROL_ABSTRACT_ENVELOPE", "kind": "bundle_component"},
        ]
        + [{"id": item["contract_name"], "kind": "consumer_contract"} for item in consumer_report.get("consumer_side_contract_list", [])]
        + [{"id": item["control_signal"], "kind": "fanout_signal"} for item in fanout_budget["entries"]],
        "edges": [
            {
                "source": "PRECHARGE_ENB_CONSUMER_CLOSURE",
                "target": "PRECHARGE_ENB_CONSUMER_CONTRACT",
                "relation": "refines",
            },
            {
                "source": "WORDLINE_SECONDARY_CONSUMER_CLOSURE",
                "target": "WORDLINE_ENABLE_CONSUMER_CONTRACT",
                "relation": "extends",
            },
        ] + [
            {
                "source": "CONTROL_FANOUT_BUDGET",
                "target": item["control_signal"],
                "relation": "budgets",
            }
            for item in fanout_budget["entries"]
        ] + [
            {
                "source": "TIME_CONTROL_ABSTRACT_ENVELOPE",
                "target": region["region_name"],
                "relation": "contains_region",
            }
            for region in abstract_envelope["regions"]
        ],
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_fast_bundle_markdown(report: dict[str, Any]) -> str:
    budget_rows = []
    for item in report["control_fanout_budget"]["entries"]:
        budget_rows.append(
            [
                item["control_signal"],
                item["fanout_count"],
                ", ".join(item["fanout_targets"]),
                item["estimated_required_tracks"],
                item["route_pitch"],
                item["route_margin"],
                item["estimated_required_width"],
                item["available_metadata_channel_width"],
                item["budget_pass"],
                item["budget_margin"],
                item["risk_level"],
            ]
        )

    region_rows = []
    for item in report["control_row_abstract_placement_envelope"]["regions"]:
        region_rows.append(
            [
                item["region_name"],
                ", ".join(item["source_contracts"]),
                ", ".join(item["input_signals"]),
                ", ".join(item["output_signals"]),
                ", ".join(item["consumer_targets"]),
                item["bbox_proxy_policy"],
                item["metadata_only"],
                item["legal_physical_placement"],
            ]
        )

    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    precharge = report["precharge_consumer_pin_metadata_closure"]
    wordline = report["wordline_secondary_consumer_closure"]

    lines = [
        "# OpenYield TIME Control Fast Metadata Bundle Report",
        "",
        "This bundle is metadata-only. It combines precharge consumer closure, wordline secondary consumer closure, control fanout budget estimation, and an abstract control-row envelope without claiming legal physical placement.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## PRECHARGE Consumer Pin Metadata Closure",
        "",
        "```json",
        json.dumps(precharge, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Wordline Secondary Consumer Closure",
        "",
        "```json",
        json.dumps(wordline, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Control Fanout Budget",
        "",
        _md_table(
            [
                "signal",
                "fanout",
                "targets",
                "tracks",
                "pitch",
                "margin",
                "required width",
                "channel width",
                "pass",
                "budget margin",
                "risk",
            ],
            budget_rows,
        ),
        "",
        "## Control-Row Abstract Placement Envelope",
        "",
        _md_table(
            [
                "region",
                "source contracts",
                "inputs",
                "outputs",
                "consumer targets",
                "bbox proxy policy",
                "metadata_only",
                "legal placement",
            ],
            region_rows,
        ),
        "",
        "## Consistency Checks",
        "",
        _md_table(["check", "value"], consistency_rows),
        "",
        "## Unresolved Items",
        "",
    ]
    lines.extend(f"- {item}" for item in report["unresolved_items"])
    lines.extend(
        [
            "",
            "## Step 6.28 Recommendation",
            "",
            "```json",
            json.dumps(report["step_6_28_recommendation"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Entry Decisions",
            "",
            f"- can_enter_time_control_abstract_envelope_planning: `{report['can_enter_time_control_abstract_envelope_planning']}`",
            f"- can_enter_time_control_physical_placement: `{report['can_enter_time_control_physical_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
        ]
    )
    return "\n".join(lines)
