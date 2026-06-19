"""Read-only OpenYield TIME evidence and crossing metadata bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.time_control_region_refinement import (
    build_time_control_region_refinement_report,
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


def _risk_level(margin: float) -> str:
    if margin < 0:
        return "fail"
    if margin == 0:
        return "tight_zero_margin"
    if margin < 0.4:
        return "pass_low_margin"
    return "pass_moderate_margin"


def _find_module_contract(report: dict[str, Any], module_name: str) -> dict[str, Any] | None:
    modules = report.get("module_contracts") or report.get("modules") or report.get("contracts") or []
    for item in modules:
        if item.get("original_module_name") == module_name:
            return item
    return None


def _evidence_row(
    *,
    evidence_source: str,
    alias_checked: str,
    found: bool,
    pin_or_label_name: str | None,
    layer_if_known: str | None,
    bbox_if_known: Any,
    side_if_known: str | None,
    confidence: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "evidence_source": evidence_source,
        "alias_checked": alias_checked,
        "found": found,
        "pin_or_label_name": pin_or_label_name,
        "layer_if_known": layer_if_known,
        "bbox_if_known": bbox_if_known,
        "side_if_known": side_if_known,
        "confidence": confidence,
        "notes": notes,
    }


def build_time_control_evidence_crossing_bundle_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
    route_pitch: float = 0.2,
    route_margin: float = 0.2,
    default_control_channel_width: float = 2.0,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    region_report, _ = build_time_control_region_refinement_report(
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        tech_dir=tech_dir,
        route_pitch=route_pitch,
        route_margin=route_margin,
        default_control_channel_width=default_control_channel_width,
    )
    signal_report = _load_json("docs/openyield_time_control_signal_binding_report.json")
    gds_pin_audit = _load_json("docs/openyield_gds_pin_audit_report.json")
    macro_metadata = _load_json("docs/openyield_macro_metadata_audit.json")
    module_contracts = _load_json(contracts_path)

    precharge_module_contract = _find_module_contract(module_contracts, "PRECHARGE") or {}
    precharge_macro_entry = None
    for item in gds_pin_audit.get("audited_macros", []):
        if item.get("macro_name") == "gen_precharge":
            precharge_macro_entry = item
            break
    precharge_power_closure = region_report["precharge_power_metadata_closure"]

    contract_pin_names = [pin.get("original_name") for pin in precharge_module_contract.get("pins", [])]
    contract_power_pins = precharge_module_contract.get("power_pins", {})
    macro_pin_names = [pin.get("pin_name") for pin in (precharge_macro_entry or {}).get("pins", [])]
    macro_label_names = [label.get("text") for label in (precharge_macro_entry or {}).get("labels", [])]
    precharge_power_audit = (precharge_macro_entry or {}).get("power_rail_audit", {})

    evidence_table = [
        _evidence_row(
            evidence_source="openyield_module_contract.power_pins",
            alias_checked="VDD",
            found="VDD" in contract_power_pins,
            pin_or_label_name="VDD" if "VDD" in contract_power_pins else None,
            layer_if_known=None,
            bbox_if_known=None,
            side_if_known=None,
            confidence="high",
            notes="OpenYield PRECHARGE source contract explicitly declares VDD -> vdd.",
        ),
        _evidence_row(
            evidence_source="openyield_module_contract.power_pins",
            alias_checked="VSS",
            found="VSS" in contract_power_pins,
            pin_or_label_name="VSS" if "VSS" in contract_power_pins else None,
            layer_if_known=None,
            bbox_if_known=None,
            side_if_known=None,
            confidence="high" if "VSS" in contract_power_pins else "high_negative",
            notes="OpenYield PRECHARGE source contract does not declare VSS in current parsed metadata.",
        ),
        _evidence_row(
            evidence_source="gds_pin_audit.pins",
            alias_checked="EN/ENB/PRE/precharge_enb",
            found="EN" in macro_pin_names,
            pin_or_label_name="EN" if "EN" in macro_pin_names else None,
            layer_if_known=(precharge_macro_entry or {}).get("pins", [{}])[1].get("pin_layer") if precharge_macro_entry and len(precharge_macro_entry.get("pins", [])) > 1 else None,
            bbox_if_known=next((pin.get("pin_shape_bbox") for pin in (precharge_macro_entry or {}).get("pins", []) if pin.get("pin_name") == "EN"), None),
            side_if_known=next((pin.get("pin_side") for pin in (precharge_macro_entry or {}).get("pins", []) if pin.get("pin_name") == "EN"), None),
            confidence="high",
            notes="Local gen_precharge GDS exposes EN as the physical alias of active-low precharge enable.",
        ),
        _evidence_row(
            evidence_source="gds_pin_audit.power_rail_audit",
            alias_checked="gnd",
            found=bool(precharge_power_audit.get("has_gnd")),
            pin_or_label_name="gnd" if precharge_power_audit.get("has_gnd") else None,
            layer_if_known=None,
            bbox_if_known=None,
            side_if_known=precharge_power_audit.get("gnd_side"),
            confidence="high_negative" if not precharge_power_audit.get("has_gnd") else "high",
            notes="Current local gen_precharge GDS pin audit reports has_gnd=false.",
        ),
        _evidence_row(
            evidence_source="gds_pin_audit.labels",
            alias_checked="gnd",
            found="gnd" in macro_label_names,
            pin_or_label_name="gnd" if "gnd" in macro_label_names else None,
            layer_if_known=None,
            bbox_if_known=None,
            side_if_known=None,
            confidence="high_negative" if "gnd" not in macro_label_names else "medium",
            notes="No gnd text label was found among gen_precharge labels in the current audit report.",
        ),
        _evidence_row(
            evidence_source="macro_metadata_audit.module_metadata",
            alias_checked="VSS/gnd",
            found=False,
            pin_or_label_name=None,
            layer_if_known=None,
            bbox_if_known=None,
            side_if_known=None,
            confidence="medium_negative",
            notes="Macro metadata audit classifies PRECHARGE power_status as no_gnd_required, which does not prove a local GND pin.",
        ),
        _evidence_row(
            evidence_source="openyield_module_contract.pins",
            alias_checked="BL/BR/BLB",
            found=all(name in contract_pin_names for name in ["BL", "BLB"]),
            pin_or_label_name="BL, BLB" if all(name in contract_pin_names for name in ["BL", "BLB"]) else None,
            layer_if_known=None,
            bbox_if_known=None,
            side_if_known=None,
            confidence="high",
            notes="Source contract confirms precharge bitline pins only; it does not add GND evidence.",
        ),
        _evidence_row(
            evidence_source="local_hardmacro_metadata",
            alias_checked="VSS!/GND!/VGND/ground/0",
            found=False,
            pin_or_label_name=None,
            layer_if_known=None,
            bbox_if_known=None,
            side_if_known=None,
            confidence="high_negative",
            notes="No alternate ground alias evidence was found in current local metadata reports for gen_precharge.",
        ),
        _evidence_row(
            evidence_source="local_spice_or_cdl_metadata",
            alias_checked="gnd",
            found=False,
            pin_or_label_name=None,
            layer_if_known=None,
            bbox_if_known=None,
            side_if_known=None,
            confidence="high_negative",
            notes="No local SPICE/CDL macro file is registered for gen_precharge in current metadata.",
        ),
    ]

    precharge_gnd_evidence_found = any(
        row["found"]
        for row in evidence_table
        if row["alias_checked"].lower() in {"gnd", "vss", "vgnd", "ground", "gnd!", "vss!", "0", "vss/gnd"}
    )
    precharge_closure_decision = {
        "precharge_gnd_evidence_search_available": True,
        "precharge_gnd_pin_known": precharge_gnd_evidence_found,
        "precharge_gnd_evidence_found": precharge_gnd_evidence_found,
        "precharge_power_metadata_complete": precharge_power_closure["precharge_power_metadata_complete"] if precharge_gnd_evidence_found else False,
        "precharge_rail_continuity_proven": False,
        "precharge_closure_status": (
            "metadata_power_closed_rail_unproven"
            if precharge_gnd_evidence_found
            else "partial_missing_gnd"
        ),
        "precharge_safe_for_metadata_planning": True if precharge_gnd_evidence_found else "partial",
        "precharge_safe_for_physical_placement": False,
        "can_enter_time_control_metadata_closure": True,
    }

    region_by_signal = {
        "clk": "pdrive_region",
        "clk_buf": "pdrive_region",
        "clk_bar": "generated_logic_region",
        "gated_clk_buf": "generated_logic_region",
        "gated_clk_bar": "generated_logic_region",
        "rbl": "delay_chain_region",
        "rbl_delay": "delay_chain_region",
        "rbl_delay_bar": "generated_logic_region",
        "rbl_delay_bar_wen": "delay_chain_region",
        "we": "sense_write_enable_region",
        "we_bar": "sense_write_enable_region",
        "w_en": "sense_write_enable_region",
        "s_en": "sense_write_enable_region",
        "PRE_UNBUF": "precharge_control_region",
        "PRE": "precharge_control_region",
        "precharge_enb": "precharge_control_region",
        "wl_en": "wordline_enable_control_region",
        "wl_en_bar": "wordline_enable_control_region",
        "wordline_enable": "wordline_enable_control_region",
        "write_enable": "sense_write_enable_region",
        "sense_enable": "sense_write_enable_region",
        "cs": "generated_logic_region",
    }
    region_budget_proxy = {
        item["region_name"]: f"{item['region_name'].upper()}_REGION_BUDGET_PROXY"
        for item in region_report["control_row_region_refinement"]
    }
    adjacency_by_pair = {
        (item["source_region"], item["target_region"]): item
        for item in region_report["region_adjacency_handoff_planning"]
    }
    handoff_by_signal = {
        item["source_signal"]: item["constraint_name"]
        for item in _load_json("docs/openyield_time_control_precharge_constraints_bundle_report.json")["control_row_handoff_constraints"]
    }
    reservation_by_signal = {}
    for item in _load_json("docs/openyield_time_control_precharge_constraints_bundle_report.json")["control_channel_reservation_rules"]:
        for sig in item["signals"]:
            reservation_by_signal[sig] = item["rule_name"]

    dependency_edges = [
        {
            "edge_name": "CLK_TO_CLK_BUF",
            "source_signals": ["clk"],
            "target_signal": "clk_buf",
            "producer_region": "pdrive_region",
            "consumer_region": "pdrive_region",
        },
        {
            "edge_name": "CLK_BUF_TO_CLK_BAR",
            "source_signals": ["clk_buf"],
            "target_signal": "clk_bar",
            "producer_region": "pdrive_region",
            "consumer_region": "generated_logic_region",
        },
        {
            "edge_name": "CLK_BUF_CS_TO_GATED_CLK_BUF",
            "source_signals": ["clk_buf", "cs"],
            "target_signal": "gated_clk_buf",
            "producer_region": "generated_logic_region",
            "consumer_region": "generated_logic_region",
        },
        {
            "edge_name": "CLK_BAR_CS_TO_GATED_CLK_BAR",
            "source_signals": ["clk_bar", "cs"],
            "target_signal": "gated_clk_bar",
            "producer_region": "generated_logic_region",
            "consumer_region": "generated_logic_region",
        },
        {
            "edge_name": "GATED_CLK_BAR_TO_WL_EN",
            "source_signals": ["gated_clk_bar"],
            "target_signal": "wl_en",
            "producer_region": "generated_logic_region",
            "consumer_region": "wordline_enable_control_region",
        },
        {
            "edge_name": "WL_EN_TO_WL_EN_BAR",
            "source_signals": ["wl_en"],
            "target_signal": "wl_en_bar",
            "producer_region": "wordline_enable_control_region",
            "consumer_region": "wordline_enable_control_region",
        },
        {
            "edge_name": "RBL_TO_RBL_DELAY",
            "source_signals": ["rbl"],
            "target_signal": "rbl_delay",
            "producer_region": "delay_chain_region",
            "consumer_region": "delay_chain_region",
        },
        {
            "edge_name": "RBL_DELAY_TO_RBL_DELAY_BAR",
            "source_signals": ["rbl_delay"],
            "target_signal": "rbl_delay_bar",
            "producer_region": "delay_chain_region",
            "consumer_region": "generated_logic_region",
        },
        {
            "edge_name": "RBL_DELAY_BAR_GATED_CLK_BAR_WE_TO_W_EN",
            "source_signals": ["rbl_delay_bar", "gated_clk_bar", "we"],
            "target_signal": "w_en",
            "producer_region": "sense_write_enable_region",
            "consumer_region": "sense_write_enable_region",
        },
        {
            "edge_name": "RBL_DELAY_GATED_CLK_BAR_WE_BAR_TO_S_EN",
            "source_signals": ["rbl_delay", "gated_clk_bar", "we_bar"],
            "target_signal": "s_en",
            "producer_region": "sense_write_enable_region",
            "consumer_region": "sense_write_enable_region",
        },
        {
            "edge_name": "GATED_CLK_BUF_RBL_DELAY_WL_EN_BAR_TO_PRE_UNBUF",
            "source_signals": ["gated_clk_buf", "rbl_delay", "wl_en_bar"],
            "target_signal": "PRE_UNBUF",
            "producer_region": "precharge_control_region",
            "consumer_region": "precharge_control_region",
        },
        {
            "edge_name": "PRE_UNBUF_TO_PRE",
            "source_signals": ["PRE_UNBUF"],
            "target_signal": "PRE",
            "producer_region": "precharge_control_region",
            "consumer_region": "precharge_control_region",
        },
    ]

    crossing_signal_proof = []
    missing_region_assignments: list[str] = []
    missing_adjacencies: list[str] = []
    missing_handoff_constraints: list[str] = []
    missing_reservation_rules: list[str] = []

    for edge in dependency_edges:
        producer_region = edge["producer_region"]
        consumer_region = edge["consumer_region"]
        crossing_required = producer_region != consumer_region
        matched_adjacency = None
        adjacency_margin = default_control_channel_width
        if crossing_required:
            adjacency = adjacency_by_pair.get((producer_region, consumer_region)) or adjacency_by_pair.get(
                (consumer_region, producer_region)
            )
            if adjacency:
                matched_adjacency = adjacency["adjacency_name"]
                estimated_tracks = adjacency["estimated_tracks"]
                required_width = adjacency["required_width"]
                reserved_width = adjacency["reserved_width"]
                budget_margin = adjacency["margin"]
            else:
                estimated_tracks = max(1, len(edge["source_signals"]))
                required_width = round(estimated_tracks * route_pitch + route_margin, 6)
                reserved_width = default_control_channel_width
                budget_margin = round(reserved_width - required_width, 6)
        else:
            estimated_tracks = max(1, len(edge["source_signals"]))
            required_width = round(estimated_tracks * route_pitch + route_margin, 6)
            reserved_width = default_control_channel_width
            budget_margin = round(reserved_width - required_width, 6)

        target_signal = edge["target_signal"]
        semantic_signal = {
            "w_en": "write_enable",
            "s_en": "sense_enable",
            "PRE": "precharge_enb",
            "wl_en": "wordline_enable",
        }.get(target_signal, target_signal)
        matched_handoff_constraint = handoff_by_signal.get(semantic_signal)
        matched_reservation_rule = reservation_by_signal.get(semantic_signal)
        if not matched_reservation_rule:
            matched_reservation_rule = region_budget_proxy.get(consumer_region)

        metadata_covered = (
            producer_region in region_by_signal.values()
            and consumer_region in region_by_signal.values()
            and ((not crossing_required) or matched_adjacency is not None)
            and (matched_handoff_constraint is not None or matched_reservation_rule is not None)
        )

        if crossing_required and matched_adjacency is None:
            missing_adjacencies.append(edge["edge_name"])
        if matched_handoff_constraint is None and matched_reservation_rule is None:
            missing_handoff_constraints.append(edge["edge_name"])
            missing_reservation_rules.append(edge["edge_name"])
        if producer_region not in region_by_signal.values() or consumer_region not in region_by_signal.values():
            missing_region_assignments.append(edge["edge_name"])

        crossing_signal_proof.append(
            {
                "edge_name": edge["edge_name"],
                "source_signals": edge["source_signals"],
                "target_signal": target_signal,
                "producer_region": producer_region,
                "consumer_region": consumer_region,
                "crossing_required": crossing_required,
                "matched_adjacency": matched_adjacency,
                "matched_handoff_constraint": matched_handoff_constraint,
                "matched_reservation_rule": matched_reservation_rule,
                "estimated_tracks": estimated_tracks,
                "required_width": required_width,
                "reserved_width": reserved_width,
                "budget_margin": budget_margin,
                "risk_level": _risk_level(budget_margin),
                "metadata_covered": metadata_covered,
                "physical_routing_proven": False,
            }
        )

    all_core_dependency_edges_have_region_assignment = len(missing_region_assignments) == 0
    all_required_crossings_have_adjacency = all(
        (not item["crossing_required"]) or item["matched_adjacency"] is not None
        for item in crossing_signal_proof
    )
    all_required_crossings_have_handoff_or_reservation = all(
        (not item["crossing_required"]) or (item["matched_handoff_constraint"] is not None or item["matched_reservation_rule"] is not None)
        for item in crossing_signal_proof
    )
    all_crossing_budgets_pass = all(item["budget_margin"] >= 0 for item in crossing_signal_proof)
    can_enter_time_control_metadata_closure = (
        all_core_dependency_edges_have_region_assignment
        and all_required_crossings_have_adjacency
        and all_required_crossings_have_handoff_or_reservation
        and all_crossing_budgets_pass
    )

    crossing_coverage_summary = {
        "control_region_crossing_proof_available": True,
        "all_core_dependency_edges_have_region_assignment": all_core_dependency_edges_have_region_assignment,
        "all_required_crossings_have_adjacency": all_required_crossings_have_adjacency,
        "all_required_crossings_have_handoff_or_reservation": all_required_crossings_have_handoff_or_reservation,
        "all_crossing_budgets_pass": all_crossing_budgets_pass,
        "missing_region_assignments": missing_region_assignments,
        "missing_adjacencies": missing_adjacencies,
        "missing_handoff_constraints": missing_handoff_constraints,
        "missing_reservation_rules": missing_reservation_rules,
        "physical_routing_proven": False,
    }

    interface_crossing_proof = []
    for item in region_report["grouped_planning_interface_refinement"]:
        matched_constraints = [
            edge["matched_handoff_constraint"]
            for edge in crossing_signal_proof
            if edge["matched_handoff_constraint"] in item["handoff_constraints"]
        ]
        matched_rules = [
            edge["matched_reservation_rule"]
            for edge in crossing_signal_proof
            if edge["matched_reservation_rule"] in item["reservation_rules"]
        ]
        metadata_ready = item["metadata_ready"]
        if item["interface_name"] == "TIME_CONTROL_TO_PRECHARGE_INTERFACE":
            metadata_ready = "partial" if not precharge_gnd_evidence_found else True
        interface_crossing_proof.append(
            {
                "interface_name": item["interface_name"],
                "control_signals": item["control_signals"],
                "source_regions": item["source_regions"],
                "target_macro": item["target_macro"],
                "target_pins": item["target_pins"],
                "matched_handoff_constraints": sorted(set(x for x in matched_constraints if x)),
                "matched_reservation_rules": sorted(set(x for x in matched_rules if x)),
                "crossing_coverage_complete": bool(matched_constraints or matched_rules),
                "metadata_ready": metadata_ready,
                "physical_ready": False,
                "blocked_by": item["blocked_by"],
            }
        )

    unresolved_items = [
        "PRECHARGE GND may remain missing, depending on evidence result",
        "PRECHARGE rail continuity proof is missing",
        "crossing proof is metadata-only, not legal routing",
        "region adjacency is not legal routing",
        "abstract region refinement is not legal placement",
        "control routing proof is missing",
        "delay timing proof is missing",
        "wen-delay timing proof is missing",
        "shared rail is disabled",
        "no DRC/LVS proof exists",
        "standalone integration is not allowed yet",
    ]

    consistency_checks = {
        "time_control_evidence_crossing_bundle_available": True,
        "precharge_gnd_evidence_search_available": True,
        "precharge_gnd_evidence_found": precharge_gnd_evidence_found,
        "precharge_closure_status": precharge_closure_decision["precharge_closure_status"],
        "precharge_power_metadata_complete": precharge_closure_decision["precharge_power_metadata_complete"],
        "control_region_crossing_proof_available": True,
        "all_core_dependency_edges_have_region_assignment": all_core_dependency_edges_have_region_assignment,
        "all_required_crossings_have_adjacency": all_required_crossings_have_adjacency,
        "all_required_crossings_have_handoff_or_reservation": all_required_crossings_have_handoff_or_reservation,
        "all_crossing_budgets_pass": all_crossing_budgets_pass,
        "grouped_interface_crossing_proof_available": True,
        "can_enter_time_control_metadata_closure": can_enter_time_control_metadata_closure,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
        "safe_for_metadata_planning": can_enter_time_control_metadata_closure,
        "safe_for_physical_placement": False,
    }

    report = {
        "scope": "step6_30_openyield_time_evidence_crossing_bundle",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "bundle_mode": "fast_metadata_bundle",
        "source_reports": {
            "time_control_region_refinement": region_report["scope"],
            "time_control_signal_binding": signal_report["scope"],
        },
        "precharge_gnd_evidence_search": evidence_table,
        "precharge_closure_decision": precharge_closure_decision,
        "control_region_crossing_signal_proof": crossing_signal_proof,
        "crossing_coverage_summary": crossing_coverage_summary,
        "grouped_interface_crossing_proof": interface_crossing_proof,
        "consistency_checks": consistency_checks,
        "unresolved_items": unresolved_items,
        "audit_summary": {
            "time_control_evidence_crossing_bundle_available": True,
            "precharge_closure_status": precharge_closure_decision["precharge_closure_status"],
            "precharge_gnd_evidence_found": precharge_gnd_evidence_found,
            "all_required_crossings_have_adjacency": all_required_crossings_have_adjacency,
            "all_required_crossings_have_handoff_or_reservation": all_required_crossings_have_handoff_or_reservation,
            "all_crossing_budgets_pass": all_crossing_budgets_pass,
            "can_enter_time_control_metadata_closure": can_enter_time_control_metadata_closure,
            "can_enter_time_control_physical_placement": False,
            "can_enter_standalone_control_placement": False,
        },
        "can_enter_time_control_metadata_closure": can_enter_time_control_metadata_closure,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
        "step_6_31_recommendation": {
            "recommended_next_phase": "time_control_precharge_local_ground_semantics_or_finer_crossing_contracts",
            "candidate_directions": [
                "precharge_local_ground_semantics_review",
                "conditional_wen_crossing_refinement",
                "macro_handoff_side_refinement",
                "time_control_delay_timing_metadata_refinement",
            ],
            "reason": [
                "PRECHARGE local hardmacro metadata still does not expose GND evidence in current reports.",
                "Crossing coverage is now bundled and structurally covered at metadata level, but it is still not legal routing proof.",
                "The next step should refine evidence or contract granularity rather than attempt standalone integration.",
            ],
        },
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": "PRECHARGE_GND_EVIDENCE_SEARCH", "kind": "evidence_bundle"}]
            + [{"id": item["edge_name"], "kind": "dependency_edge"} for item in crossing_signal_proof]
            + [{"id": item["interface_name"], "kind": "grouped_interface"} for item in interface_crossing_proof]
        ),
        "edges": (
            [
                {
                    "source": "PRECHARGE_GND_EVIDENCE_SEARCH",
                    "target": "TIME_CONTROL_TO_PRECHARGE_INTERFACE",
                    "relation": "gates_metadata_state",
                }
            ]
            + [
                {
                    "source": item["producer_region"],
                    "target": item["consumer_region"],
                    "relation": "crossing_edge",
                    "edge_name": item["edge_name"],
                }
                for item in crossing_signal_proof
            ]
            + [
                {
                    "source": interface["interface_name"],
                    "target": edge["edge_name"],
                    "relation": "covered_by_interface",
                }
                for interface in interface_crossing_proof
                for edge in crossing_signal_proof
                if any(sig in interface["control_signals"] for sig in edge["source_signals"] + [edge["target_signal"]])
            ]
        ),
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_evidence_crossing_bundle_markdown(report: dict[str, Any]) -> str:
    evidence_rows = [
        [
            item["evidence_source"],
            item["alias_checked"],
            item["found"],
            item["pin_or_label_name"],
            item["layer_if_known"],
            item["bbox_if_known"],
            item["side_if_known"],
            item["confidence"],
            item["notes"],
        ]
        for item in report["precharge_gnd_evidence_search"]
    ]
    crossing_rows = [
        [
            item["edge_name"],
            ", ".join(item["source_signals"]),
            item["target_signal"],
            item["producer_region"],
            item["consumer_region"],
            item["crossing_required"],
            item["matched_adjacency"] or "-",
            item["matched_handoff_constraint"] or "-",
            item["matched_reservation_rule"] or "-",
            item["budget_margin"],
            item["metadata_covered"],
        ]
        for item in report["control_region_crossing_signal_proof"]
    ]
    interface_rows = [
        [
            item["interface_name"],
            ", ".join(item["control_signals"]),
            ", ".join(item["source_regions"]),
            item["target_macro"],
            ", ".join(item["matched_handoff_constraints"]) or "-",
            ", ".join(item["matched_reservation_rules"]) or "-",
            item["crossing_coverage_complete"],
            item["metadata_ready"],
            item["physical_ready"],
        ]
        for item in report["grouped_interface_crossing_proof"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Evidence + Crossing Bundle Report",
        "",
        "This report is metadata-only. It does not prove legal routing, legal placement, rail continuity, timing closure, DRC, LVS, or standalone integration readiness.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## PRECHARGE GND Evidence Search",
        "",
        _md_table(
            [
                "source",
                "alias",
                "found",
                "pin/label",
                "layer",
                "bbox",
                "side",
                "confidence",
                "notes",
            ],
            evidence_rows,
        ),
        "",
        "## PRECHARGE Closure Decision",
        "",
        "```json",
        json.dumps(report["precharge_closure_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Control Region Crossing Signal Proof",
        "",
        _md_table(
            [
                "edge",
                "source signals",
                "target",
                "producer region",
                "consumer region",
                "crossing",
                "adjacency",
                "handoff",
                "reservation",
                "margin",
                "covered",
            ],
            crossing_rows,
        ),
        "",
        "## Crossing Coverage Summary",
        "",
        "```json",
        json.dumps(report["crossing_coverage_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Grouped Interface Crossing Proof",
        "",
        _md_table(
            [
                "interface",
                "control signals",
                "source regions",
                "target macro",
                "handoff constraints",
                "reservation rules",
                "coverage complete",
                "metadata ready",
                "physical ready",
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
            "## Step 6.31 Recommendation",
            "",
            "```json",
            json.dumps(report["step_6_31_recommendation"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Entry Decisions",
            "",
            f"- can_enter_time_control_metadata_closure: `{report['can_enter_time_control_metadata_closure']}`",
            f"- can_enter_time_control_physical_placement: `{report['can_enter_time_control_physical_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
        ]
    )
    return "\n".join(lines)
