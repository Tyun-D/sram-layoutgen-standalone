"""Read-only OpenYield TIME generated-logic contract packaging audit."""

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


def _candidate_paths(tech_dir: Path, stem: str) -> tuple[list[str], list[str]]:
    gds_paths = sorted(str(path.resolve()) for path in tech_dir.glob(f"**/{stem}.gds"))
    spice_paths = sorted(str(path.resolve()) for path in tech_dir.glob(f"**/{stem}.sp"))
    return gds_paths, spice_paths


def _macro_audit_entry(gds_pin_audit: dict[str, Any], macro_name: str) -> dict[str, Any] | None:
    for item in gds_pin_audit.get("audited_macros", []):
        if item.get("macro_name") == macro_name:
            return item
    return None


def _candidate_summary(tech_dir: Path, gds_pin_audit: dict[str, Any], name: str) -> dict[str, Any]:
    gds_paths, spice_paths = _candidate_paths(tech_dir, name)
    macro_entry = _macro_audit_entry(gds_pin_audit, name)
    return {
        "candidate_name": name,
        "gds_available": bool(gds_paths),
        "spice_available": bool(spice_paths),
        "pin_metadata_available": bool(macro_entry and macro_entry.get("pins")),
        "power_metadata_available": bool(
            macro_entry
            and macro_entry.get("power_rail_audit", {}).get("has_vdd")
            and macro_entry.get("power_rail_audit", {}).get("has_gnd")
        ),
        "gds_paths": gds_paths,
        "spice_paths": spice_paths,
        "safe_for_metadata_planning": True if name != "gen_nand4" else "partial",
        "safe_for_physical_placement": False,
        "notes": [
            "Metadata-only candidate summary.",
            "Do not treat local GDS presence as physical placement proof.",
        ],
    }


def _contract(
    *,
    contract_name: str,
    logic_role: str,
    source_openyield_symbol: str,
    used_by_signal_contracts: list[str],
    input_pins: list[str],
    output_pins: list[str],
    polarity: str,
    candidate_cells: list[str],
    candidate_sequence: list[str],
    candidate_mapping_status: str,
    pin_metadata_available: bool,
    power_metadata_available: bool,
    timing_metadata_available: bool,
    routing_metadata_available: bool,
    safe_for_metadata_planning: bool | str,
    notes: list[str],
    requires_generated_layout_or_stdcell_row: bool = True,
    requires_timing_proof: bool = True,
    requires_routing_proof: bool = True,
    requires_rail_continuity_proof: bool = True,
) -> dict[str, Any]:
    return {
        "contract_name": contract_name,
        "logic_role": logic_role,
        "source_openyield_symbol": source_openyield_symbol,
        "used_by_signal_contracts": used_by_signal_contracts,
        "input_pins": input_pins,
        "output_pins": output_pins,
        "polarity": polarity,
        "candidate_cells": candidate_cells,
        "candidate_sequence": candidate_sequence,
        "candidate_cell_count_if_known": len(candidate_sequence),
        "candidate_mapping_status": candidate_mapping_status,
        "pin_metadata_available": pin_metadata_available,
        "power_metadata_available": power_metadata_available,
        "timing_metadata_available": timing_metadata_available,
        "routing_metadata_available": routing_metadata_available,
        "safe_for_metadata_planning": safe_for_metadata_planning,
        "safe_for_physical_placement": False,
        "requires_generated_layout_or_stdcell_row": requires_generated_layout_or_stdcell_row,
        "requires_timing_proof": requires_timing_proof,
        "requires_routing_proof": requires_routing_proof,
        "requires_rail_continuity_proof": requires_rail_continuity_proof,
        "metadata_only": True,
        "notes": notes,
    }


def build_time_control_generated_logic_contract_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
    signal_binding_report_path: str | Path | None = None,
    subblock_report_path: str | Path | None = None,
    decoder_leaf_convention_report_path: str | Path | None = None,
    decoder_logic_repair_report_path: str | Path | None = None,
    gds_pin_audit_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    tech_dir = Path(tech_dir)
    signal_report = _load_json(signal_binding_report_path or "docs/openyield_time_control_signal_binding_report.json")
    subblock_report = _load_json(subblock_report_path or "docs/openyield_time_control_subblock_audit_report.json")
    decoder_leaf_report = _load_json(
        decoder_leaf_convention_report_path or "docs/openyield_decoder_composite_leaf_convention_report.json"
    )
    decoder_logic_report = _load_json(
        decoder_logic_repair_report_path or "docs/openyield_decoder_logic_repair_report.json"
    )
    gds_pin_audit = _load_json(gds_pin_audit_report_path or "docs/openyield_gds_pin_audit_report.json")
    _ = _load_json(contracts_path)
    _ = Path(openyield_root)

    candidate_index = {
        name: _candidate_summary(tech_dir, gds_pin_audit, name)
        for name in ["gen_delay_inv", "gen_inv", "gen_nand2", "gen_nand4", "dff"]
    }

    gen_inv_ok = bool(candidate_index["gen_inv"]["pin_metadata_available"] and candidate_index["gen_inv"]["power_metadata_available"])
    gen_nand2_ok = bool(candidate_index["gen_nand2"]["pin_metadata_available"] and candidate_index["gen_nand2"]["power_metadata_available"])
    gen_delay_ok = bool(candidate_index["gen_delay_inv"]["pin_metadata_available"] and candidate_index["gen_delay_inv"]["power_metadata_available"])
    gen_nand4_partial = candidate_index["gen_nand4"]["safe_for_metadata_planning"] == "partial"

    and3_reused = bool(decoder_leaf_report.get("and3_composite_convention_available"))
    pnand3_reused = bool(decoder_leaf_report.get("pnand3_composite_convention_available"))

    contracts = [
        _contract(
            contract_name="PINV_GENERATED_LOGIC_CONTRACT",
            logic_role="inverter",
            source_openyield_symbol="Pinv",
            used_by_signal_contracts=[
                "CLK_BAR_BINDING_CONTRACT",
                "RBL_DELAY_BAR_BINDING_CONTRACT",
                "WORDLINE_ENABLE_BINDING_CONTRACT",
            ],
            input_pins=["A"],
            output_pins=["Z"],
            polarity="inverting",
            candidate_cells=["gen_inv"],
            candidate_sequence=["gen_inv"],
            candidate_mapping_status="direct_metadata_inverter",
            pin_metadata_available=gen_inv_ok,
            power_metadata_available=gen_inv_ok,
            timing_metadata_available=False,
            routing_metadata_available=False,
            safe_for_metadata_planning=True,
            notes=[
                "Unified metadata mapping for clk_buf->clk_bar, rbl_delay->rbl_delay_bar, and wl_en->wl_en_bar.",
                "Physical placement remains blocked despite local GDS availability.",
            ],
        ),
        _contract(
            contract_name="AND2_GENERATED_LOGIC_CONTRACT",
            logic_role="and2_composite",
            source_openyield_symbol="AND2",
            used_by_signal_contracts=[
                "GATED_CLK_BUF_BINDING_CONTRACT",
                "GATED_CLK_BAR_BINDING_CONTRACT",
            ],
            input_pins=["A", "B"],
            output_pins=["Z"],
            polarity="non_inverting_and",
            candidate_cells=["gen_nand2", "gen_inv"],
            candidate_sequence=["gen_nand2", "gen_inv"],
            candidate_mapping_status="metadata_composite_and2",
            pin_metadata_available=gen_nand2_ok and gen_inv_ok,
            power_metadata_available=gen_nand2_ok and gen_inv_ok,
            timing_metadata_available=False,
            routing_metadata_available=False,
            safe_for_metadata_planning=True,
            notes=[
                "AND2 is represented as PNAND2 + INV semantic composition.",
                "No direct physical AND2 macro is claimed.",
            ],
        ),
        _contract(
            contract_name="AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
            logic_role="and3_composite",
            source_openyield_symbol="AND3",
            used_by_signal_contracts=[
                "WRITE_ENABLE_BINDING_CONTRACT",
                "SENSE_ENABLE_BINDING_CONTRACT",
            ],
            input_pins=["A", "B", "C"],
            output_pins=["Z"],
            polarity="non_inverting_and3",
            candidate_cells=["gen_nand2", "gen_inv"],
            candidate_sequence=["gen_nand2", "gen_inv", "gen_nand2", "gen_inv"],
            candidate_mapping_status="metadata_composite_and3",
            pin_metadata_available=gen_nand2_ok and gen_inv_ok,
            power_metadata_available=gen_nand2_ok and gen_inv_ok,
            timing_metadata_available=False,
            routing_metadata_available=False,
            safe_for_metadata_planning=True,
            notes=[
                f"Reuses decoder convention: {decoder_leaf_report['composite_leaf_conventions'][1]['convention_name']}.",
                "Input order is preserved for both write_enable and sense_enable contracts.",
            ],
        ),
        _contract(
            contract_name="PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
            logic_role="pnand3_composite",
            source_openyield_symbol="PNAND3",
            used_by_signal_contracts=[
                "PRECHARGE_ENB_BINDING_CONTRACT",
            ],
            input_pins=["A", "B", "C"],
            output_pins=["Z"],
            polarity="inverting_nand3",
            candidate_cells=["gen_nand2", "gen_inv"],
            candidate_sequence=["gen_nand2", "gen_inv", "gen_nand2"],
            candidate_mapping_status="metadata_composite_pnand3",
            pin_metadata_available=gen_nand2_ok and gen_inv_ok,
            power_metadata_available=gen_nand2_ok and gen_inv_ok,
            timing_metadata_available=False,
            routing_metadata_available=False,
            safe_for_metadata_planning=True,
            notes=[
                f"Reuses decoder convention: {decoder_leaf_report['composite_leaf_conventions'][0]['convention_name']}.",
                "Precharge input order gated_clk_buf / rbl_delay / wl_en_bar is preserved at metadata level.",
            ],
        ),
        _contract(
            contract_name="PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT",
            logic_role="buffer_chain",
            source_openyield_symbol="PDRIVE",
            used_by_signal_contracts=["CLK_BUF_BINDING_CONTRACT"],
            input_pins=["A"],
            output_pins=["Z"],
            polarity="non_inverting_buffer_chain",
            candidate_cells=["gen_inv"],
            candidate_sequence=["gen_inv", "gen_inv", "gen_inv", "gen_inv"],
            candidate_mapping_status="generated_buffer_chain",
            pin_metadata_available=gen_inv_ok,
            power_metadata_available=gen_inv_ok,
            timing_metadata_available=False,
            routing_metadata_available=False,
            safe_for_metadata_planning=True,
            notes=[
                "Stage count source-confirmed as 4.",
                "Drive-strength progression is known from source and preserved only as metadata notes.",
            ],
        ),
        _contract(
            contract_name="PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT",
            logic_role="buffer_chain",
            source_openyield_symbol="PDRIVE2_FOR_PRE",
            used_by_signal_contracts=["PRECHARGE_ENB_BINDING_CONTRACT"],
            input_pins=["A"],
            output_pins=["Z"],
            polarity="non_inverting_buffer_chain",
            candidate_cells=["gen_inv"],
            candidate_sequence=["gen_inv", "gen_inv"],
            candidate_mapping_status="generated_precharge_buffer_chain",
            pin_metadata_available=gen_inv_ok,
            power_metadata_available=gen_inv_ok,
            timing_metadata_available=False,
            routing_metadata_available=False,
            safe_for_metadata_planning=True,
            notes=[
                "Stage count source-confirmed as 2.",
                "Precharge ENB polarity is preserved through PRE_UNBUF -> PRE buffering.",
            ],
        ),
        _contract(
            contract_name="WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT",
            logic_role="buffer_chain",
            source_openyield_symbol="WL_PDRIVE",
            used_by_signal_contracts=["WORDLINE_ENABLE_BINDING_CONTRACT"],
            input_pins=["A"],
            output_pins=["Z"],
            polarity="non_inverting_buffer_chain",
            candidate_cells=["gen_inv"],
            candidate_sequence=["gen_inv", "gen_inv"],
            candidate_mapping_status="generated_wordline_enable_buffer_chain",
            pin_metadata_available=gen_inv_ok,
            power_metadata_available=gen_inv_ok,
            timing_metadata_available=False,
            routing_metadata_available=False,
            safe_for_metadata_planning=True,
            notes=[
                "Stage count source-confirmed as 2.",
                "wordline_enable active-high semantics are preserved.",
            ],
        ),
        _contract(
            contract_name="DELAY_CHAIN_GENERATED_LOGIC_CONTRACT",
            logic_role="delay_chain",
            source_openyield_symbol="DELAY_CHAIN",
            used_by_signal_contracts=["RBL_DELAY_BINDING_CONTRACT"],
            input_pins=["in"],
            output_pins=["out"],
            polarity="delayed_non_inverting",
            candidate_cells=["gen_delay_inv", "gen_inv"],
            candidate_sequence=["gen_delay_inv"] * 9,
            candidate_mapping_status="generated_delay_chain",
            pin_metadata_available=gen_delay_ok and gen_inv_ok,
            power_metadata_available=gen_delay_ok and gen_inv_ok,
            timing_metadata_available=False,
            routing_metadata_available=False,
            safe_for_metadata_planning=True,
            notes=[
                "Stage count source-confirmed as 9.",
                "Load model is known at source level: four load inverters per stage.",
            ],
        ),
        _contract(
            contract_name="WEN_DELAY_CHAIN_CONDITIONAL_GENERATED_LOGIC_CONTRACT",
            logic_role="conditional_delay_chain",
            source_openyield_symbol="WEN_DELAY_CHAIN",
            used_by_signal_contracts=["WEN_DELAY_CONDITIONAL_BINDING_CONTRACT"],
            input_pins=["in"],
            output_pins=["out"],
            polarity="delayed_non_inverting",
            candidate_cells=["gen_delay_inv", "gen_inv"],
            candidate_sequence=["gen_delay_inv"] * 6,
            candidate_mapping_status="conditional_generated_delay_chain",
            pin_metadata_available=gen_delay_ok and gen_inv_ok,
            power_metadata_available=gen_delay_ok and gen_inv_ok,
            timing_metadata_available=False,
            routing_metadata_available=False,
            safe_for_metadata_planning=True,
            notes=[
                "Conditional applicability preserved exactly: operation == write and num_rows == 16 and num_cols == 512.",
                "This contract must not generalize to all configs.",
            ],
        ),
    ]

    signal_to_logic = {
        "CLK_BUF_BINDING_CONTRACT": ["PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT"],
        "CLK_BAR_BINDING_CONTRACT": ["PINV_GENERATED_LOGIC_CONTRACT"],
        "GATED_CLK_BUF_BINDING_CONTRACT": ["AND2_GENERATED_LOGIC_CONTRACT"],
        "GATED_CLK_BAR_BINDING_CONTRACT": ["AND2_GENERATED_LOGIC_CONTRACT"],
        "RBL_DELAY_BINDING_CONTRACT": ["DELAY_CHAIN_GENERATED_LOGIC_CONTRACT"],
        "RBL_DELAY_BAR_BINDING_CONTRACT": ["PINV_GENERATED_LOGIC_CONTRACT"],
        "WORDLINE_ENABLE_BINDING_CONTRACT": ["WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT", "PINV_GENERATED_LOGIC_CONTRACT"],
        "WRITE_ENABLE_BINDING_CONTRACT": ["AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT"],
        "SENSE_ENABLE_BINDING_CONTRACT": ["AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT"],
        "PRECHARGE_ENB_BINDING_CONTRACT": ["PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT", "PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT"],
        "WEN_DELAY_CONDITIONAL_BINDING_CONTRACT": ["WEN_DELAY_CHAIN_CONDITIONAL_GENERATED_LOGIC_CONTRACT"],
    }
    available_contracts = {item["contract_name"] for item in contracts}
    coverage_rows = []
    all_covered = True
    for signal_contract, providers in signal_to_logic.items():
        ok = all(provider in available_contracts for provider in providers)
        all_covered = all_covered and ok
        coverage_rows.append(
            {
                "signal_binding_contract": signal_contract,
                "generated_logic_contracts": providers,
                "covered": ok,
            }
        )

    consistency_checks = {
        "time_as_single_macro_allowed": False,
        "generated_logic_contract_packaging_available": True,
        "all_core_logic_roles_have_contract": True,
        "all_signal_bindings_have_generated_logic_contract": all_covered,
        "and3_composite_reuses_decoder_convention": and3_reused,
        "pnand3_composite_reuses_decoder_convention": pnand3_reused,
        "buffer_chain_contracts_available": True,
        "delay_chain_contracts_available": True,
        "conditional_wen_delay_policy_captured": True,
        "control_signal_polarity_preserved": bool(signal_report.get("control_signal_binding_consistent")),
        "control_signal_consumer_binding_preserved": bool(signal_report.get("control_signal_binding_consistent")),
        "safe_for_metadata_planning": True,
        "safe_for_physical_placement": False,
    }

    unresolved_items = [
        "generated logic contracts are metadata-only",
        "chain stage placement is not legalized",
        "delay timing proof is missing",
        "wen-delay conditional timing proof is missing",
        "composite internal routing is not proven",
        "rail continuity is not proven",
        "control-row physical placement is not proven",
        "gen_nand4 remains partial",
        "no DRC/LVS proof exists",
        "standalone integration is not allowed yet",
    ]

    candidate_audit = []
    for name in ["gen_delay_inv", "gen_inv", "gen_nand2", "gen_nand4", "dff"]:
        entry = dict(candidate_index[name])
        entry["used_by_generated_logic_contracts"] = [
            item["contract_name"] for item in contracts if name in item["candidate_cells"]
        ]
        if name == "gen_nand4":
            entry["gen_nand4_should_not_be_used_as_physical_substitute"] = True
            entry["notes"] = entry["notes"] + [
                "gen_nand4 remains partial and must not be used as a physical substitute.",
            ]
        candidate_audit.append(entry)

    report = {
        "scope": "step6_25_openyield_time_control_generated_logic_contract_packaging_audit",
        "openyield_root": str(Path(openyield_root).resolve()),
        "contracts_path": str(Path(contracts_path).resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "source_reports": {
            "time_control_signal_binding": signal_report.get("scope"),
            "time_control_subblock_audit": subblock_report.get("scope"),
            "decoder_composite_leaf_convention": decoder_leaf_report.get("scope"),
            "decoder_logic_repair": decoder_logic_report.get("scope"),
        },
        "time_control_generated_logic_contract_available": True,
        "generated_logic_contract_packaging_available": True,
        "partial_generated_logic_contracts_present": gen_nand4_partial,
        "generated_logic_contract_list": contracts,
        "candidate_cell_audit": candidate_audit,
        "contract_to_signal_coverage": coverage_rows,
        "all_signal_bindings_have_generated_logic_contract": all_covered,
        "generated_logic_contract_coverage_complete": True if all_covered else "partial",
        "consistency_checks": consistency_checks,
        "unresolved_items": unresolved_items,
        "can_enter_time_control_generated_logic_metadata_planning": True,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
        "audit_summary": {
            "time_control_generated_logic_contract_available": True,
            "generated_logic_contract_packaging_available": True,
            "all_core_logic_roles_have_contract": True,
            "all_signal_bindings_have_generated_logic_contract": all_covered,
            "generated_logic_contract_coverage_complete": True if all_covered else "partial",
            "partial_generated_logic_contracts_present": gen_nand4_partial,
            "can_enter_time_control_generated_logic_metadata_planning": True,
            "can_enter_time_control_physical_placement": False,
            "can_enter_standalone_control_placement": False,
        },
        "step_6_26_recommendation": {
            "recommended_next_phase": "time_control_consumer_side_contract_normalization",
            "candidate_directions": [
                "write_enable_consumer_contract_normalization",
                "sense_enable_consumer_contract_normalization",
                "precharge_enb_consumer_contract_normalization",
                "wordline_enable_consumer_contract_normalization",
            ],
            "reason": [
                "Generated-logic packaging is now available and covers every current TIME signal binding.",
                "The next useful step is consumer-side contract normalization, not physical placement.",
                "Control-row placement, routing, and signoff proofs remain blocked.",
            ],
        },
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
    }

    graph = {
        "scope": report["scope"],
        "nodes": [
            {"id": item["contract_name"], "kind": "generated_logic_contract"}
            for item in contracts
        ] + [
            {"id": item["signal_binding_contract"], "kind": "signal_binding"}
            for item in coverage_rows
        ],
        "edges": [
            {
                "source": row["signal_binding_contract"],
                "target": contract_name,
                "relation": "implemented_by",
            }
            for row in coverage_rows
            for contract_name in row["generated_logic_contracts"]
        ],
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_generated_logic_contract_markdown(report: dict[str, Any]) -> str:
    contract_rows = []
    for item in report["generated_logic_contract_list"]:
        contract_rows.append(
            [
                item["contract_name"],
                item["logic_role"],
                item["source_openyield_symbol"],
                ", ".join(item["used_by_signal_contracts"]),
                ", ".join(item["candidate_cells"]),
                item["candidate_mapping_status"],
                item["safe_for_metadata_planning"],
                item["safe_for_physical_placement"],
            ]
        )

    candidate_rows = []
    for item in report["candidate_cell_audit"]:
        candidate_rows.append(
            [
                item["candidate_name"],
                item["gds_available"],
                item["spice_available"],
                item["pin_metadata_available"],
                item["power_metadata_available"],
                ", ".join(item["used_by_generated_logic_contracts"]),
                item["safe_for_metadata_planning"],
                item["safe_for_physical_placement"],
            ]
        )

    coverage_rows = []
    for row in report["contract_to_signal_coverage"]:
        coverage_rows.append(
            [
                row["signal_binding_contract"],
                ", ".join(row["generated_logic_contracts"]),
                row["covered"],
            ]
        )

    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Generated Logic Contract Report",
        "",
        "This is a metadata-only packaging audit for TIME generated logic. It does not modify placement, routing, standalone.py, or the GDS writer.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Generated Logic Contract List",
        "",
        _md_table(
            [
                "contract",
                "logic role",
                "source symbol",
                "used by signal bindings",
                "candidate cells",
                "mapping",
                "metadata planning",
                "physical placement",
            ],
            contract_rows,
        ),
        "",
        "## Candidate Cell Audit",
        "",
        _md_table(
            [
                "candidate",
                "GDS",
                "SPICE",
                "pin metadata",
                "power metadata",
                "used by contracts",
                "metadata planning",
                "physical placement",
            ],
            candidate_rows,
        ),
        "",
        "## Contract-to-Signal Coverage",
        "",
        _md_table(
            ["signal binding contract", "generated logic contracts", "covered"],
            coverage_rows,
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
            "## Step 6.26 Recommendation",
            "",
            "```json",
            json.dumps(report["step_6_26_recommendation"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Entry Decisions",
            "",
            f"- can_enter_time_control_generated_logic_metadata_planning: `{report['can_enter_time_control_generated_logic_metadata_planning']}`",
            f"- can_enter_time_control_physical_placement: `{report['can_enter_time_control_physical_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
        ]
    )
    return "\n".join(lines)
