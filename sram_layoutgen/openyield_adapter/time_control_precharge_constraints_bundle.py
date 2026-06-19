"""Read-only OpenYield TIME PRECHARGE and control-row constraints bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.time_control_fast_bundle import (
    build_time_control_fast_bundle_report,
)


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


def _find_generated_logic_contract(report: dict[str, Any], contract_name: str) -> dict[str, Any]:
    for item in report.get("generated_logic_contract_list", []):
        if item.get("contract_name") == contract_name:
            return item
    raise KeyError(f"Missing generated logic contract: {contract_name}")


def _find_macro(report: dict[str, Any], macro_name: str) -> dict[str, Any] | None:
    for item in report.get("audited_macros", []):
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


def _constraint_from_budget(
    *,
    constraint_name: str,
    source_signal: str,
    source_region: str,
    target_macro: str,
    target_pin: str,
    target_pin_side: str,
    target_region: str,
    preferred_handoff_direction: str,
    budget_entry: dict[str, Any],
) -> dict[str, Any]:
    return {
        "constraint_name": constraint_name,
        "source_signal": source_signal,
        "source_region": source_region,
        "target_macro": target_macro,
        "target_pin": target_pin,
        "target_pin_side": target_pin_side,
        "target_region": target_region,
        "fanout_count": budget_entry["fanout_count"],
        "preferred_handoff_direction": preferred_handoff_direction,
        "estimated_tracks": budget_entry["estimated_required_tracks"],
        "route_pitch": budget_entry["route_pitch"],
        "route_margin": budget_entry["route_margin"],
        "required_width": budget_entry["estimated_required_width"],
        "available_metadata_channel_width": budget_entry["available_metadata_channel_width"],
        "budget_pass": budget_entry["budget_pass"],
        "budget_margin": budget_entry["budget_margin"],
        "metadata_only": True,
        "physical_routing_proven": False,
    }


def _reservation_rule(
    *,
    rule_name: str,
    signals: list[str],
    source_region: str,
    target_region: str,
    reserved_width: float,
    required_width: float,
    shares_channel_with: list[str],
    exclusive_or_shared: str,
) -> dict[str, Any]:
    margin = round(reserved_width - required_width, 6)
    return {
        "rule_name": rule_name,
        "signals": signals,
        "source_region": source_region,
        "target_region": target_region,
        "reserved_width": reserved_width,
        "required_width": required_width,
        "margin": margin,
        "risk_level": _risk_level(margin),
        "shares_channel_with": shares_channel_with,
        "exclusive_or_shared": exclusive_or_shared,
        "metadata_only": True,
        "legal_routing_proven": False,
    }


def _grouped_interface(
    *,
    interface_name: str,
    source_signals: list[str],
    target_macro: str,
    target_pins: list[str],
    polarity_expectation: str,
    consumer_contracts: list[str],
    generated_logic_contracts: list[str],
    handoff_constraints: list[str],
    reservation_rules: list[str],
    metadata_ready: bool | str,
    physical_ready: bool,
    blocked_by: list[str],
) -> dict[str, Any]:
    return {
        "interface_name": interface_name,
        "source_signals": source_signals,
        "target_macro": target_macro,
        "target_pins": target_pins,
        "polarity_expectation": polarity_expectation,
        "consumer_contracts": consumer_contracts,
        "generated_logic_contracts": generated_logic_contracts,
        "handoff_constraints": handoff_constraints,
        "reservation_rules": reservation_rules,
        "metadata_ready": metadata_ready,
        "physical_ready": physical_ready,
        "blocked_by": blocked_by,
    }


def build_time_control_precharge_constraints_bundle_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
    route_pitch: float = 0.2,
    route_margin: float = 0.2,
    default_control_channel_width: float = 2.0,
    consumer_contract_report_path: str | Path | None = None,
    generated_logic_report_path: str | Path | None = None,
    gds_pin_audit_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    tech_dir = Path(tech_dir)
    contracts_path = Path(contracts_path)

    fast_report, _ = build_time_control_fast_bundle_report(
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        tech_dir=tech_dir,
        route_pitch=route_pitch,
        route_margin=route_margin,
        default_control_channel_width=default_control_channel_width,
    )
    consumer_report = _load_json(
        consumer_contract_report_path or "docs/openyield_time_control_consumer_contract_report.json"
    )
    generated_logic_report = _load_json(
        generated_logic_report_path or "docs/openyield_time_control_generated_logic_contract_report.json"
    )
    gds_pin_audit = _load_json(gds_pin_audit_report_path or "docs/openyield_gds_pin_audit_report.json")

    write_contract = _find_consumer_contract(consumer_report, "WRITE_ENABLE_CONSUMER_CONTRACT")
    sense_contract = _find_consumer_contract(consumer_report, "SENSE_ENABLE_CONSUMER_CONTRACT")
    precharge_contract = _find_consumer_contract(consumer_report, "PRECHARGE_ENB_CONSUMER_CONTRACT")
    wordline_contract = _find_consumer_contract(consumer_report, "WORDLINE_ENABLE_CONSUMER_CONTRACT")

    _find_generated_logic_contract(generated_logic_report, "AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT")
    _find_generated_logic_contract(generated_logic_report, "PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT")
    _find_generated_logic_contract(generated_logic_report, "PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT")
    _find_generated_logic_contract(generated_logic_report, "WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT")
    _find_generated_logic_contract(generated_logic_report, "PINV_GENERATED_LOGIC_CONTRACT")

    precharge_macro = _find_macro(gds_pin_audit, "gen_precharge")
    precharge_enb_pin = _find_pin(precharge_macro, "precharge_enb")
    precharge_vdd_pin = _find_pin(precharge_macro, "vdd")
    precharge_gnd_pin = _find_pin(precharge_macro, "gnd")
    precharge_power = (precharge_macro or {}).get("power_rail_audit", {})

    precharge_pin_known = bool(precharge_enb_pin)
    precharge_pin_side_known = bool(precharge_enb_pin and precharge_enb_pin.get("pin_side") != "unknown")
    precharge_vdd_pin_known = bool(precharge_vdd_pin)
    precharge_gnd_pin_known = bool(precharge_gnd_pin)
    precharge_power_metadata_complete = precharge_vdd_pin_known and precharge_gnd_pin_known
    precharge_pin_metadata_complete = precharge_pin_known and precharge_pin_side_known
    precharge_closure_status = "complete" if precharge_power_metadata_complete and precharge_pin_metadata_complete else "partial"
    precharge_safe_for_metadata_planning = (
        True if precharge_closure_status == "complete" else "partial"
    )

    precharge_adapter_metadata_closure = {
        "precharge_adapter_metadata_available": True,
        "precharge_adapter_metadata_closure_status": precharge_closure_status,
        "precharge_consumer_signal": "PRE / precharge_enb",
        "precharge_consumer_pin": "ENB",
        "precharge_consumer_pin_aliases": ["EN", "ENB", "precharge_enb", "PRE"],
        "precharge_active_level": "active_low",
        "precharge_pin_known": precharge_pin_known,
        "precharge_pin_side_known": precharge_pin_side_known,
        "precharge_power_domain_known": True if precharge_power_metadata_complete else "partial",
        "precharge_vdd_pin_known": precharge_vdd_pin_known,
        "precharge_gnd_pin_known": precharge_gnd_pin_known,
        "precharge_power_metadata_complete": precharge_power_metadata_complete,
        "precharge_pin_metadata_complete": precharge_pin_metadata_complete,
        "precharge_safe_for_metadata_planning": precharge_safe_for_metadata_planning,
        "precharge_safe_for_physical_placement": False,
        "gds_macro_candidate": "gen_precharge",
        "physical_alias_pin_name": precharge_enb_pin.get("pin_name") if precharge_enb_pin else None,
        "physical_alias_pin_side": precharge_enb_pin.get("pin_side") if precharge_enb_pin else None,
        "power_rail_summary": {
            "has_vdd": precharge_power.get("has_vdd"),
            "has_gnd": precharge_power.get("has_gnd"),
            "vdd_side": precharge_power.get("vdd_side"),
            "gnd_side": precharge_power.get("gnd_side"),
            "rail_continuity_status": precharge_power.get("rail_continuity_status"),
        },
        "notes": [
            "PRECHARGE still has no dedicated adapter module in the current clean worktree.",
            "The active-low consumer contract is normalized to ENB while the current hard-macro GDS exposes the physical alias pin EN.",
            "Power-domain closure remains partial because VDD metadata exists but GND pin metadata is still missing in the current GDS pin audit.",
        ],
    }

    budgets = {entry["control_signal"]: entry for entry in fast_report["control_fanout_budget"]["entries"]}

    handoff_constraints = [
        _constraint_from_budget(
            constraint_name="WRITE_ENABLE_TO_WRITEDRIVER_EN",
            source_signal="write_enable",
            source_region="sense_write_enable_region",
            target_macro="WRITEDRIVER",
            target_pin="EN",
            target_pin_side="bottom",
            target_region="consumer_handoff_region",
            preferred_handoff_direction="horizontal_to_write_periphery",
            budget_entry=budgets["write_enable"],
        ),
        _constraint_from_budget(
            constraint_name="SENSE_ENABLE_TO_SENSEAMP_EN",
            source_signal="sense_enable",
            source_region="sense_write_enable_region",
            target_macro="SENSEAMP",
            target_pin="EN",
            target_pin_side="top",
            target_region="consumer_handoff_region",
            preferred_handoff_direction="horizontal_to_read_periphery",
            budget_entry=budgets["sense_enable"],
        ),
        _constraint_from_budget(
            constraint_name="PRECHARGE_ENB_TO_PRECHARGE_ENB",
            source_signal="precharge_enb",
            source_region="precharge_control_region",
            target_macro="PRECHARGE",
            target_pin="ENB",
            target_pin_side=precharge_enb_pin.get("pin_side", "bottom") if precharge_enb_pin else "unknown",
            target_region="consumer_handoff_region",
            preferred_handoff_direction="horizontal_to_precharge_edge",
            budget_entry=budgets["precharge_enb"],
        ),
        _constraint_from_budget(
            constraint_name="WORDLINE_ENABLE_TO_WORDLINEDRIVER_B",
            source_signal="wordline_enable",
            source_region="wordline_enable_control_region",
            target_macro="WORDLINEDRIVER",
            target_pin="B",
            target_pin_side="left",
            target_region="consumer_handoff_region",
            preferred_handoff_direction="horizontal_to_wordline_driver",
            budget_entry=budgets["wordline_enable"],
        ),
        _constraint_from_budget(
            constraint_name="WL_EN_BAR_TO_PRECHARGE_PNAND3_C",
            source_signal="wl_en_bar",
            source_region="wordline_enable_control_region",
            target_macro="PRECHARGE",
            target_pin="PNAND3.C",
            target_pin_side="internal_metadata_only",
            target_region="precharge_control_region",
            preferred_handoff_direction="local_generated_logic_feedback",
            budget_entry=budgets["wl_en_bar"],
        ),
    ]

    reservation_rules = [
        _reservation_rule(
            rule_name="CONTROL_ROW_WRITE_ENABLE_CHANNEL",
            signals=["write_enable"],
            source_region="sense_write_enable_region",
            target_region="consumer_handoff_region",
            reserved_width=default_control_channel_width,
            required_width=budgets["write_enable"]["estimated_required_width"],
            shares_channel_with=[],
            exclusive_or_shared="exclusive",
        ),
        _reservation_rule(
            rule_name="CONTROL_ROW_SENSE_ENABLE_CHANNEL",
            signals=["sense_enable"],
            source_region="sense_write_enable_region",
            target_region="consumer_handoff_region",
            reserved_width=default_control_channel_width,
            required_width=budgets["sense_enable"]["estimated_required_width"],
            shares_channel_with=[],
            exclusive_or_shared="exclusive",
        ),
        _reservation_rule(
            rule_name="CONTROL_ROW_PRECHARGE_ENB_CHANNEL",
            signals=["precharge_enb"],
            source_region="precharge_control_region",
            target_region="consumer_handoff_region",
            reserved_width=default_control_channel_width,
            required_width=budgets["precharge_enb"]["estimated_required_width"],
            shares_channel_with=[],
            exclusive_or_shared="exclusive",
        ),
        _reservation_rule(
            rule_name="CONTROL_ROW_WORDLINE_ENABLE_CHANNEL",
            signals=["wordline_enable"],
            source_region="wordline_enable_control_region",
            target_region="consumer_handoff_region",
            reserved_width=default_control_channel_width,
            required_width=budgets["wordline_enable"]["estimated_required_width"],
            shares_channel_with=[],
            exclusive_or_shared="exclusive",
        ),
        _reservation_rule(
            rule_name="CONTROL_ROW_WL_EN_BAR_SECONDARY_CHANNEL",
            signals=["wl_en_bar"],
            source_region="wordline_enable_control_region",
            target_region="precharge_control_region",
            reserved_width=default_control_channel_width,
            required_width=budgets["wl_en_bar"]["estimated_required_width"],
            shares_channel_with=[],
            exclusive_or_shared="exclusive",
        ),
    ]

    grouped_planning_interfaces = [
        _grouped_interface(
            interface_name="TIME_CONTROL_TO_WRITEDRIVER_INTERFACE",
            source_signals=["write_enable"],
            target_macro="WRITEDRIVER",
            target_pins=["EN"],
            polarity_expectation="active_high",
            consumer_contracts=[write_contract["contract_name"]],
            generated_logic_contracts=write_contract["generated_logic_contracts"],
            handoff_constraints=["WRITE_ENABLE_TO_WRITEDRIVER_EN"],
            reservation_rules=["CONTROL_ROW_WRITE_ENABLE_CHANNEL"],
            metadata_ready=True,
            physical_ready=False,
            blocked_by=[
                "handoff constraints are metadata-only",
                "channel reservation rules are not legal routing",
                "control routing proof is missing",
                "delay timing proof is missing",
            ],
        ),
        _grouped_interface(
            interface_name="TIME_CONTROL_TO_SENSEAMP_INTERFACE",
            source_signals=["sense_enable"],
            target_macro="SENSEAMP",
            target_pins=["EN"],
            polarity_expectation="active_high",
            consumer_contracts=[sense_contract["contract_name"]],
            generated_logic_contracts=sense_contract["generated_logic_contracts"],
            handoff_constraints=["SENSE_ENABLE_TO_SENSEAMP_EN"],
            reservation_rules=["CONTROL_ROW_SENSE_ENABLE_CHANNEL"],
            metadata_ready=True,
            physical_ready=False,
            blocked_by=[
                "handoff constraints are metadata-only",
                "channel reservation rules are not legal routing",
                "control routing proof is missing",
                "delay timing proof is missing",
            ],
        ),
        _grouped_interface(
            interface_name="TIME_CONTROL_TO_PRECHARGE_INTERFACE",
            source_signals=["precharge_enb", "wl_en_bar"],
            target_macro="PRECHARGE",
            target_pins=["ENB", "PNAND3.C"],
            polarity_expectation="precharge_enb active_low, wl_en_bar active_high_local_secondary",
            consumer_contracts=[precharge_contract["contract_name"]],
            generated_logic_contracts=[
                "PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
                "PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT",
                "PINV_GENERATED_LOGIC_CONTRACT",
            ],
            handoff_constraints=[
                "PRECHARGE_ENB_TO_PRECHARGE_ENB",
                "WL_EN_BAR_TO_PRECHARGE_PNAND3_C",
            ],
            reservation_rules=[
                "CONTROL_ROW_PRECHARGE_ENB_CHANNEL",
                "CONTROL_ROW_WL_EN_BAR_SECONDARY_CHANNEL",
            ],
            metadata_ready=precharge_safe_for_metadata_planning,
            physical_ready=False,
            blocked_by=[
                "PRECHARGE adapter metadata may remain partial",
                "PRECHARGE power-domain closure may remain incomplete",
                "handoff constraints are metadata-only",
                "channel reservation rules are not legal routing",
                "control routing proof is missing",
                "rail continuity proof is missing",
            ],
        ),
        _grouped_interface(
            interface_name="TIME_CONTROL_TO_WORDLINEDRIVER_INTERFACE",
            source_signals=["wordline_enable"],
            target_macro="WORDLINEDRIVER",
            target_pins=["B"],
            polarity_expectation="active_high",
            consumer_contracts=[wordline_contract["contract_name"]],
            generated_logic_contracts=[
                "WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT",
                "PINV_GENERATED_LOGIC_CONTRACT",
            ],
            handoff_constraints=["WORDLINE_ENABLE_TO_WORDLINEDRIVER_B"],
            reservation_rules=["CONTROL_ROW_WORDLINE_ENABLE_CHANNEL"],
            metadata_ready=True,
            physical_ready=False,
            blocked_by=[
                "handoff constraints are metadata-only",
                "channel reservation rules are not legal routing",
                "control routing proof is missing",
                "delay timing proof is missing",
            ],
        ),
    ]

    all_primary_control_interfaces_have_constraints = all(
        any(signal in interface["source_signals"] for interface in grouped_planning_interfaces)
        for signal in ["write_enable", "sense_enable", "precharge_enb", "wordline_enable"]
    )
    all_control_channel_budgets_pass = all(rule["margin"] >= 0 for rule in reservation_rules)
    precharge_metadata_ready_for_planning = precharge_safe_for_metadata_planning in (True, "partial")
    safe_for_metadata_planning = (
        all_primary_control_interfaces_have_constraints
        and all_control_channel_budgets_pass
        and precharge_metadata_ready_for_planning
    )

    unresolved_items = [
        "PRECHARGE adapter metadata may remain partial",
        "PRECHARGE power-domain closure may remain incomplete",
        "handoff constraints are metadata-only",
        "channel reservation rules are not legal routing",
        "abstract envelope is not legal placement",
        "control routing proof is missing",
        "delay timing proof is missing",
        "wen-delay timing proof is missing",
        "rail continuity proof is missing",
        "shared rail is disabled",
        "no DRC/LVS proof exists",
        "standalone integration is not allowed yet",
    ]

    consistency_checks = {
        "time_control_precharge_constraints_bundle_available": True,
        "precharge_adapter_metadata_available": True,
        "precharge_adapter_metadata_closure_status": precharge_closure_status,
        "control_handoff_constraints_available": True,
        "control_channel_reservation_rules_available": True,
        "grouped_planning_interfaces_available": True,
        "all_primary_control_interfaces_have_constraints": all_primary_control_interfaces_have_constraints,
        "all_control_channel_budgets_pass": all_control_channel_budgets_pass,
        "precharge_metadata_ready_for_planning": precharge_metadata_ready_for_planning,
        "precharge_physical_ready": False,
        "safe_for_metadata_planning": safe_for_metadata_planning,
        "safe_for_physical_placement": False,
        "can_enter_time_control_constraint_planning": safe_for_metadata_planning,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
    }

    report = {
        "scope": "step6_28_openyield_time_precharge_control_row_constraints_bundle",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "bundle_mode": "fast_metadata_bundle",
        "source_reports": {
            "time_control_fast_bundle": fast_report.get("scope"),
            "time_control_consumer_contract": consumer_report.get("scope"),
            "time_control_generated_logic_contract": generated_logic_report.get("scope"),
            "gds_pin_audit": gds_pin_audit.get("tech_dir"),
        },
        "precharge_adapter_metadata_closure": precharge_adapter_metadata_closure,
        "control_row_handoff_constraints": handoff_constraints,
        "control_channel_reservation_rules": reservation_rules,
        "grouped_planning_interfaces": grouped_planning_interfaces,
        "consistency_checks": consistency_checks,
        "unresolved_items": unresolved_items,
        "audit_summary": {
            "time_control_precharge_constraints_bundle_available": True,
            "precharge_adapter_metadata_closure_status": precharge_closure_status,
            "control_handoff_constraints_available": True,
            "control_channel_reservation_rules_available": True,
            "grouped_planning_interfaces_available": True,
            "all_control_channel_budgets_pass": all_control_channel_budgets_pass,
            "can_enter_time_control_constraint_planning": safe_for_metadata_planning,
            "can_enter_time_control_physical_placement": False,
            "can_enter_standalone_control_placement": False,
        },
        "can_enter_time_control_constraint_planning": safe_for_metadata_planning,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
        "step_6_29_recommendation": {
            "recommended_next_phase": "time_control_control_row_planning_or_precharge_power_metadata_closure",
            "candidate_directions": [
                "precharge_power_metadata_closure",
                "control_row_region_refinement",
                "control_grouped_fanout_proof",
                "time_control_delay_timing_metadata_refinement",
            ],
            "reason": [
                "The control-row handoff story is now bundled at metadata level and all current channel budgets pass under the current assumptions.",
                "PRECHARGE remains partial because power-domain closure is still incomplete.",
                "The next useful step is to refine control-row planning evidence, not to claim legal routing or physical placement.",
            ],
        },
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": "PRECHARGE_ADAPTER_METADATA_CLOSURE", "kind": "metadata_closure"}]
            + [{"id": item["constraint_name"], "kind": "handoff_constraint"} for item in handoff_constraints]
            + [{"id": item["rule_name"], "kind": "reservation_rule"} for item in reservation_rules]
            + [{"id": item["interface_name"], "kind": "grouped_interface"} for item in grouped_planning_interfaces]
            + [
                {"id": signal, "kind": "control_signal"}
                for signal in ["write_enable", "sense_enable", "precharge_enb", "wordline_enable", "wl_en_bar"]
            ]
        ),
        "edges": (
            [
                {
                    "source": "PRECHARGE_ADAPTER_METADATA_CLOSURE",
                    "target": "TIME_CONTROL_TO_PRECHARGE_INTERFACE",
                    "relation": "supports_metadata",
                }
            ]
            + [
                {
                    "source": item["source_signal"],
                    "target": item["constraint_name"],
                    "relation": "drives_constraint",
                }
                for item in handoff_constraints
            ]
            + [
                {
                    "source": item["constraint_name"],
                    "target": next(
                        rule["rule_name"]
                        for rule in reservation_rules
                        if item["source_signal"] in rule["signals"]
                    ),
                    "relation": "budgeted_by",
                }
                for item in handoff_constraints
            ]
            + [
                {
                    "source": interface["interface_name"],
                    "target": constraint_name,
                    "relation": "contains_constraint",
                }
                for interface in grouped_planning_interfaces
                for constraint_name in interface["handoff_constraints"]
            ]
            + [
                {
                    "source": interface["interface_name"],
                    "target": rule_name,
                    "relation": "reserves_channel",
                }
                for interface in grouped_planning_interfaces
                for rule_name in interface["reservation_rules"]
            ]
        ),
        "summary": report["audit_summary"],
    }

    return report, graph


def build_time_control_precharge_constraints_bundle_markdown(report: dict[str, Any]) -> str:
    handoff_rows = [
        [
            item["constraint_name"],
            item["source_signal"],
            item["source_region"],
            item["target_macro"],
            item["target_pin"],
            item["target_pin_side"],
            item["target_region"],
            item["fanout_count"],
            item["estimated_tracks"],
            item["required_width"],
            item["available_metadata_channel_width"],
            item["budget_margin"],
            item["budget_pass"],
        ]
        for item in report["control_row_handoff_constraints"]
    ]

    reservation_rows = [
        [
            item["rule_name"],
            ", ".join(item["signals"]),
            item["source_region"],
            item["target_region"],
            item["reserved_width"],
            item["required_width"],
            item["margin"],
            item["risk_level"],
            ", ".join(item["shares_channel_with"]) if item["shares_channel_with"] else "-",
            item["exclusive_or_shared"],
        ]
        for item in report["control_channel_reservation_rules"]
    ]

    interface_rows = [
        [
            item["interface_name"],
            ", ".join(item["source_signals"]),
            item["target_macro"],
            ", ".join(item["target_pins"]),
            item["polarity_expectation"],
            item["metadata_ready"],
            item["physical_ready"],
            ", ".join(item["blocked_by"]),
        ]
        for item in report["grouped_planning_interfaces"]
    ]

    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME PRECHARGE + Control-Row Constraints Bundle Report",
        "",
        "This is a metadata-only bundle. It does not claim legal placement, legal routing, timing closure, DRC closure, LVS closure, or standalone integration readiness.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## PRECHARGE Adapter Metadata Closure",
        "",
        "```json",
        json.dumps(report["precharge_adapter_metadata_closure"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Control-Row Handoff Constraints",
        "",
        _md_table(
            [
                "constraint",
                "source signal",
                "source region",
                "target macro",
                "target pin",
                "target pin side",
                "target region",
                "fanout",
                "tracks",
                "required width",
                "channel width",
                "budget margin",
                "pass",
            ],
            handoff_rows,
        ),
        "",
        "## Control Channel Reservation Rules",
        "",
        _md_table(
            [
                "rule",
                "signals",
                "source region",
                "target region",
                "reserved width",
                "required width",
                "margin",
                "risk",
                "shares with",
                "mode",
            ],
            reservation_rows,
        ),
        "",
        "## Grouped Planning Interfaces",
        "",
        _md_table(
            [
                "interface",
                "source signals",
                "target macro",
                "target pins",
                "polarity",
                "metadata ready",
                "physical ready",
                "blocked by",
            ],
            interface_rows,
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
            "## Step 6.29 Recommendation",
            "",
            "```json",
            json.dumps(report["step_6_29_recommendation"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Entry Decisions",
            "",
            f"- can_enter_time_control_constraint_planning: `{report['can_enter_time_control_constraint_planning']}`",
            f"- can_enter_time_control_physical_placement: `{report['can_enter_time_control_physical_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
        ]
    )
    return "\n".join(lines)
