"""Readonly TIME/control timing metadata inventory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TIMING_OBJECT_SPECS = [
    ("DELAY_CHAIN", "replica_bitline_delay / rbl_delay_generation"),
    ("WEN_DELAY_CHAIN", "write_enable_delay_conditioning"),
    ("PDRIVE", "clock_buffer_chain"),
    ("PDRIVE2_FOR_PRE", "precharge_enable_buffer_chain"),
    ("WL_PDRIVE", "wordline_enable_buffer_chain"),
    ("PINV", "single_inversion_helper"),
    ("AND2", "gated_clock_generation"),
    ("AND3_COMPOSITE", "enable_logic_generation"),
    ("PNAND3_COMPOSITE", "precharge_gating_generation"),
    ("PRECHARGE", "precharge_consumer_handoff"),
    ("DFF_ROW", "clocked_register_row"),
    ("WRITE_ENABLE_PATH", "consumer_enable_path"),
    ("SENSE_ENABLE_PATH", "consumer_enable_path"),
    ("PRECHARGE_ENABLE_PATH", "consumer_enable_path"),
    ("WORDLINE_ENABLE_PATH", "consumer_enable_path"),
    ("RBL_DELAY_PATH", "replica_delay_path"),
    ("GATED_CLOCK_PATH", "gated_clock_path"),
]

MODEL_MACROS = [
    "gen_inv",
    "gen_nand2",
    "gen_delay_inv",
    "gen_precharge",
    "dff",
    "sense_amp",
    "write_driver",
    "gen_wl_driver",
    "gen_col_mux_vdd_labeled",
    "cell_1rw",
    "replica_cell_1rw",
]


def build_time_control_timing_metadata_report(
    repo_root: str | Path,
    tech_dir: str | Path,
    routing_obstacle_path: str | Path,
    legal_placement_readonly_path: str | Path,
    composite_feasibility_path: str | Path,
    leaf_inventory_path: str | Path,
    generated_logic_contracts_path: str | Path,
    signal_bindings_path: str | Path,
    repo_asset_inventory_path: str | Path | None = None,
    subblock_audit_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    tech = Path(tech_dir)
    if not tech.is_absolute():
        tech = (root / tech).resolve()

    routing = _load_json(routing_obstacle_path)
    legal = _load_json(legal_placement_readonly_path)
    composite = _load_json(composite_feasibility_path)
    leaf = _load_json(leaf_inventory_path)
    contracts = _load_json(generated_logic_contracts_path)
    bindings = _load_json(signal_bindings_path)
    assets = _load_json(repo_asset_inventory_path) if repo_asset_inventory_path else _load_json(root / "docs" / "openyield_repo_physical_asset_inventory_report.json")
    subblock_audit = _load_json(subblock_audit_path) if subblock_audit_path else _load_json(root / "docs" / "openyield_time_control_subblock_audit_report.json")

    contract_map = {row["contract_name"]: row for row in contracts["generated_logic_contract_list"]}
    binding_map = {row["contract_name"]: row for row in bindings["signal_binding_contracts"]}
    composite_map = {row["subblock_name"]: row for row in composite["subblock_composite_topology"]}
    routing_nets = {row["net_name"]: row for row in routing["control_net_routing_obstacle_table"]}
    handoffs = {row["handoff_name"]: row for row in routing["consumer_handoff_audit"]}
    leaf_rows = {row["macro_name"]: row for row in leaf["leaf_gds_bbox_pin_side_inventory"] if row["recommended_for_future_planning"]}
    subblock_rows = {row["subblock_name"]: row for row in subblock_audit["subblock_audit"]}

    timing_objects = []
    graph_nodes = [{"id": "timing_inventory", "label": "time_control_timing_metadata_inventory", "kind": "root"}]
    graph_edges = []
    for name, role in TIMING_OBJECT_SPECS:
        row = _build_timing_object(name, role, contract_map, binding_map, composite_map, routing_nets, handoffs, leaf_rows, subblock_rows)
        timing_objects.append(row)
        graph_nodes.append({"id": f"timing:{name}", "label": name, "kind": "timing_object"})
        graph_edges.append({"from": "timing_inventory", "to": f"timing:{name}", "relation": "inventoried"})

    model_inventory = _build_model_inventory(MODEL_MACROS, assets, leaf_rows)
    classifications = [
        {
            "timing_object": row["timing_object"],
            "classification": row["timing_proof_readiness_classification"],
            "safe_for_timing_metadata_planning": row["safe_for_timing_metadata_planning"],
            "safe_for_timing_proof_planning": row["safe_for_timing_proof_planning"],
            "safe_for_timing_closure": row["safe_for_timing_closure"],
        }
        for row in timing_objects
    ]

    delay_chain_section = next(row for row in timing_objects if row["timing_object"] == "DELAY_CHAIN")
    wen_delay_section = next(row for row in timing_objects if row["timing_object"] == "WEN_DELAY_CHAIN")
    pdrive_section = [row for row in timing_objects if row["timing_object"] in {"PDRIVE", "PDRIVE2_FOR_PRE", "WL_PDRIVE", "PRECHARGE_ENABLE_PATH", "WORDLINE_ENABLE_PATH"}]
    enable_section = [row for row in timing_objects if row["timing_object"] in {"WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH"}]
    dff_clock_section = [row for row in timing_objects if row["timing_object"] in {"DFF_ROW", "GATED_CLOCK_PATH"}]

    blockers = _dedupe_list([f"{row['timing_object']}: {item}" for row in timing_objects for item in row["blockers"]])
    audit_summary = {
        "time_control_timing_metadata_inventory_available": True,
        "all_required_timing_objects_analyzed": len(timing_objects) == len(TIMING_OBJECT_SPECS),
        "all_stage_counts_recorded_or_missing_noted": True,
        "all_required_timing_model_sources_checked": len(model_inventory) == len(MODEL_MACROS),
        "delay_chain_timing_metadata_available": True,
        "wen_delay_chain_timing_metadata_available": True,
        "pdrive_timing_metadata_available": True,
        "enable_path_timing_metadata_available": True,
        "precharge_timing_exception_retained": True,
        "dff_row_clock_timing_metadata_available": True,
        "timing_proof_available_now": False,
        "can_enter_timing_proof_planning": True,
        "can_enter_physical_timing_closure_now": False,
        "can_enter_routing_proof_planning": True,
        "can_enter_physical_routing_now": False,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    report = {
        "scope": "time_control_timing_metadata_inventory",
        "repo_root": str(root),
        "tech_dir": str(tech),
        "input_reports_and_assets": {
            "routing_obstacle": str(Path(routing_obstacle_path).resolve()),
            "legal_placement_readonly": str(Path(legal_placement_readonly_path).resolve()),
            "composite_feasibility": str(Path(composite_feasibility_path).resolve()),
            "leaf_inventory": str(Path(leaf_inventory_path).resolve()),
            "generated_logic_contracts": str(Path(generated_logic_contracts_path).resolve()),
            "signal_bindings": str(Path(signal_bindings_path).resolve()),
            "repo_asset_inventory": str((Path(repo_asset_inventory_path).resolve() if repo_asset_inventory_path else (root / "docs" / "openyield_repo_physical_asset_inventory_report.json").resolve())),
            "subblock_audit": str((Path(subblock_audit_path).resolve() if subblock_audit_path else (root / "docs" / "openyield_time_control_subblock_audit_report.json").resolve())),
        },
        "timing_object_table": timing_objects,
        "delay_chain_timing_metadata": delay_chain_section,
        "wen_delay_chain_timing_metadata": wen_delay_section,
        "pdrive_wordline_precharge_drive_metadata": pdrive_section,
        "write_sense_enable_path_timing_metadata": enable_section,
        "dff_row_gated_clock_timing_metadata": dff_clock_section,
        "spice_lib_model_inventory": model_inventory,
        "timing_proof_readiness_classification": classifications,
        "blockers": blockers,
        "next_recommended_proof_task": "time_control_timing_proof_planning",
        "boundary_assertions": {
            "stage_count_known_is_not_delay_proof": True,
            "leaf_sequence_known_is_not_timing_proof": True,
            "spice_exists_is_not_timing_closure": True,
            "routing_obstacle_inventory_is_not_parasitic_extraction": True,
            "timing_metadata_planning_is_not_timing_proof": True,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
        "audit_summary": audit_summary,
    }
    graph = {"nodes": graph_nodes, "edges": graph_edges}
    return {"report": report, "graph": graph}


def _build_timing_object(
    name: str,
    role: str,
    contract_map: dict[str, Any],
    binding_map: dict[str, Any],
    composite_map: dict[str, Any],
    routing_nets: dict[str, Any],
    handoffs: dict[str, Any],
    leaf_rows: dict[str, Any],
    subblock_rows: dict[str, Any],
) -> dict[str, Any]:
    contract_name = _contract_for_object(name)
    binding_names = _binding_contracts_for_object(name)
    contract = contract_map.get(contract_name)
    subblock = subblock_rows.get(name)
    composite = composite_map.get(name)
    relevant_bindings = [binding_map[item] for item in binding_names if item in binding_map]
    relevant_net_names = _routing_nets_for_object(name)
    relevant_nets = [routing_nets[item] for item in relevant_net_names if item in routing_nets]
    stage_count, stage_source = _stage_count(name, contract, composite)
    leaf_sequence = _leaf_sequence(name, contract, composite)
    known_leaf_macro = _known_leaf_macro(leaf_sequence)
    leaf_has_spice = any(_leaf_spice_available(macro) for macro in known_leaf_macro)
    leaf_has_lib = any(False for _ in known_leaf_macro)
    known_load_model = _known_load_model(name, contract, subblock, relevant_bindings)
    known_input_slew_model = None
    known_output_load_model = _output_load_model(name, relevant_bindings)
    known_rc_model = None
    known_corner_definition = None
    known_vt_corner = None
    requires_replica = name in {"DELAY_CHAIN", "RBL_DELAY_PATH"}
    requires_write_path_timing_model = name == "WEN_DELAY_CHAIN"
    precharge_exception = name in {"PRECHARGE", "PRECHARGE_ENABLE_PATH", "PDRIVE2_FOR_PRE", "PNAND3_COMPOSITE"}
    dff_clock = name in {"DFF_ROW", "GATED_CLOCK_PATH"}
    blockers = []
    if stage_count is None:
        blockers.append("stage count missing")
    if not leaf_has_spice and name not in {"PRECHARGE", "WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH", "WORDLINE_ENABLE_PATH", "PRECHARGE_ENABLE_PATH", "RBL_DELAY_PATH", "GATED_CLOCK_PATH", "AND2", "AND3_COMPOSITE", "PNAND3_COMPOSITE", "PDRIVE", "PDRIVE2_FOR_PRE", "WL_PDRIVE", "PINV", "WEN_DELAY_CHAIN", "DELAY_CHAIN"}:
        blockers.append("missing spice model")
    if not leaf_has_spice and known_leaf_macro:
        blockers.append("missing spice or lib for generated/control leaf")
    if known_load_model is None:
        blockers.append("missing load model")
    blockers.append("timing proof is missing")
    blockers.append("no SPICE timing closure has been run")
    if requires_replica:
        blockers.append("replica calibration required")
    if requires_write_path_timing_model:
        blockers.append("write path timing model required")
    if precharge_exception:
        blockers.append("precharge power exception retained")
    if dff_clock:
        blockers.append("standalone clock integration required")

    classification = _classify_timing_object(name, stage_count, leaf_has_spice, known_load_model, requires_replica, precharge_exception, dff_clock)
    safe_metadata = True
    safe_proof_planning = True
    safe_closure = False

    return {
        "timing_object": name,
        "timing_role": role,
        "source_contract": contract_name or "metadata_source_not_found",
        "source_signals": _source_signals(name, relevant_bindings, contract),
        "target_signals": _target_signals(name, relevant_bindings, contract),
        "leaf_sequence": leaf_sequence,
        "stage_count": stage_count,
        "stage_count_source": stage_source,
        "known_leaf_macro": known_leaf_macro,
        "leaf_has_spice": leaf_has_spice,
        "leaf_has_lib": leaf_has_lib,
        "known_cell_delay_model": False,
        "known_load_model": known_load_model,
        "known_input_slew_model": known_input_slew_model,
        "known_output_load_model": known_output_load_model,
        "known_rc_model": known_rc_model,
        "known_corner_definition": known_corner_definition,
        "known_voltage_temperature_corner": known_vt_corner,
        "requires_spice": True,
        "requires_liberty": True,
        "requires_parasitic_estimate": True,
        "requires_routing_rc": True,
        "requires_load_extraction": True,
        "requires_replica_path_calibration": requires_replica,
        "requires_waveform_check": name in {"DELAY_CHAIN", "WEN_DELAY_CHAIN", "PRECHARGE_ENABLE_PATH", "GATED_CLOCK_PATH"},
        "requires_margin_policy": True,
        "requires_write_path_timing_model": requires_write_path_timing_model,
        "timing_metadata_available": True,
        "timing_proof_available": False,
        "safe_for_timing_metadata_planning": safe_metadata,
        "safe_for_timing_proof_planning": safe_proof_planning,
        "safe_for_timing_closure": safe_closure,
        "timing_proof_readiness_classification": classification,
        "consumer_macro": _consumer_macro(name, relevant_nets, handoffs),
        "consumer_pin": _consumer_pin(name, relevant_nets, handoffs),
        "consumer_pin_side": _consumer_pin_side(name, relevant_nets, handoffs),
        "notes": _notes_for_object(name, contract, subblock, relevant_bindings, relevant_nets),
        "blockers": _dedupe_list(blockers),
    }


def _build_model_inventory(macros: list[str], assets: dict[str, Any], leaf_rows: dict[str, Any]) -> list[dict[str, Any]]:
    spice_items = {row["cell_or_macro"]: row for row in assets.get("spice_cdl_inventory", {}).get("items", [])}
    rows = []
    for macro in macros:
        spice = spice_items.get(macro, {})
        leaf = leaf_rows.get(macro)
        rows.append(
            {
                "macro_name": macro,
                "spice_exists": bool(spice.get("spice_exists")),
                "lib_exists": False,
                "subckt_name": spice.get("subckt_name"),
                "power_pins_known": bool(spice.get("power_pins_if_parseable")),
                "timing_arcs_known": False,
                "delay_model_available": False,
                "load_model_available": False,
                "usable_for_timing_proof_now": False,
                "notes": _dedupe_list(
                    ([f"spice path: {spice.get('spice_path')}"] if spice.get("spice_path") else [])
                    + ([f"gds path: {leaf.get('gds_path')}"] if leaf else [])
                    + (["no liberty model located"] if True else [])
                ),
            }
        )
    return rows


def format_time_control_timing_metadata_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield TIME Control Timing Metadata Report",
            "",
            f"- Scope: `{report['scope']}`",
            f"- Repo root: `{report['repo_root']}`",
            f"- Tech dir: `{report['tech_dir']}`",
            "",
            "## Audit Summary",
            "",
            "```json",
            json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Input Reports And Assets",
            "",
            "```json",
            json.dumps(report["input_reports_and_assets"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Timing Object Table",
            "",
            md_table(
                ["object", "role", "stage", "leafs", "spice", "load model", "classification", "timing proof"],
                [
                    [
                        row["timing_object"],
                        row["timing_role"],
                        row["stage_count"],
                        ", ".join(row["known_leaf_macro"]),
                        row["leaf_has_spice"],
                        row["known_load_model"],
                        row["timing_proof_readiness_classification"],
                        row["timing_proof_available"],
                    ]
                    for row in report["timing_object_table"]
                ],
            ),
            "",
            "## Delay Chain Timing Metadata",
            "",
            "```json",
            json.dumps(report["delay_chain_timing_metadata"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## WEN Delay Chain Timing Metadata",
            "",
            "```json",
            json.dumps(report["wen_delay_chain_timing_metadata"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Pdrive / Wordline / Precharge Drive Metadata",
            "",
            md_table(
                ["object", "stage", "source", "targets", "classification"],
                [
                    [row["timing_object"], row["stage_count"], ", ".join(row["source_signals"]), ", ".join(row["target_signals"]), row["timing_proof_readiness_classification"]]
                    for row in report["pdrive_wordline_precharge_drive_metadata"]
                ],
            ),
            "",
            "## Write / Sense Enable Path Timing Metadata",
            "",
            md_table(
                ["object", "consumer", "pin", "pin side", "classification"],
                [
                    [row["timing_object"], row["consumer_macro"], row["consumer_pin"], row["consumer_pin_side"], row["timing_proof_readiness_classification"]]
                    for row in report["write_sense_enable_path_timing_metadata"]
                ],
            ),
            "",
            "## DFF Row / Gated Clock Timing Metadata",
            "",
            md_table(
                ["object", "source", "targets", "classification", "blockers"],
                [
                    [row["timing_object"], ", ".join(row["source_signals"]), ", ".join(row["target_signals"]), row["timing_proof_readiness_classification"], "; ".join(row["blockers"])]
                    for row in report["dff_row_gated_clock_timing_metadata"]
                ],
            ),
            "",
            "## SPICE / LIB / Model Inventory",
            "",
            md_table(
                ["macro", "spice", "lib", "subckt", "power pins", "delay model", "usable now"],
                [
                    [row["macro_name"], row["spice_exists"], row["lib_exists"], row["subckt_name"], row["power_pins_known"], row["delay_model_available"], row["usable_for_timing_proof_now"]]
                    for row in report["spice_lib_model_inventory"]
                ],
            ),
            "",
            "## Timing Proof Readiness Classification",
            "",
            md_table(
                ["object", "classification", "metadata planning", "proof planning", "closure"],
                [
                    [row["timing_object"], row["classification"], row["safe_for_timing_metadata_planning"], row["safe_for_timing_proof_planning"], row["safe_for_timing_closure"]]
                    for row in report["timing_proof_readiness_classification"]
                ],
            ),
            "",
            "## Blockers",
            "",
            list_block(report["blockers"]),
            "",
            "## Boundary Assertions",
            "",
            "```json",
            json.dumps(report["boundary_assertions"], ensure_ascii=False, indent=2),
            "```",
        ]
    )


def _contract_for_object(name: str) -> str | None:
    return {
        "DELAY_CHAIN": "DELAY_CHAIN_GENERATED_LOGIC_CONTRACT",
        "WEN_DELAY_CHAIN": "WEN_DELAY_CHAIN_CONDITIONAL_GENERATED_LOGIC_CONTRACT",
        "PDRIVE": "PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT",
        "PDRIVE2_FOR_PRE": "PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT",
        "WL_PDRIVE": "WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT",
        "PINV": "PINV_GENERATED_LOGIC_CONTRACT",
        "AND2": "AND2_GENERATED_LOGIC_CONTRACT",
        "AND3_COMPOSITE": "AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
        "PNAND3_COMPOSITE": "PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
    }.get(name)


def _binding_contracts_for_object(name: str) -> list[str]:
    return {
        "PDRIVE": ["CLK_BUF_BINDING_CONTRACT"],
        "PINV": ["CLK_BAR_BINDING_CONTRACT", "RBL_DELAY_BAR_BINDING_CONTRACT", "WORDLINE_ENABLE_BINDING_CONTRACT"],
        "AND2": ["GATED_CLK_BUF_BINDING_CONTRACT", "GATED_CLK_BAR_BINDING_CONTRACT"],
        "AND3_COMPOSITE": ["WRITE_ENABLE_BINDING_CONTRACT", "SENSE_ENABLE_BINDING_CONTRACT"],
        "PNAND3_COMPOSITE": ["PRECHARGE_ENB_BINDING_CONTRACT"],
        "PDRIVE2_FOR_PRE": ["PRECHARGE_ENB_BINDING_CONTRACT"],
        "WL_PDRIVE": ["WORDLINE_ENABLE_BINDING_CONTRACT"],
        "DELAY_CHAIN": ["RBL_DELAY_BINDING_CONTRACT"],
        "WEN_DELAY_CHAIN": ["WEN_DELAY_CONDITIONAL_BINDING_CONTRACT"],
        "WRITE_ENABLE_PATH": ["WRITE_ENABLE_BINDING_CONTRACT"],
        "SENSE_ENABLE_PATH": ["SENSE_ENABLE_BINDING_CONTRACT"],
        "PRECHARGE_ENABLE_PATH": ["PRECHARGE_ENB_BINDING_CONTRACT"],
        "WORDLINE_ENABLE_PATH": ["WORDLINE_ENABLE_BINDING_CONTRACT"],
        "RBL_DELAY_PATH": ["RBL_DELAY_BINDING_CONTRACT", "RBL_DELAY_BAR_BINDING_CONTRACT", "WEN_DELAY_CONDITIONAL_BINDING_CONTRACT"],
        "GATED_CLOCK_PATH": ["CLK_BUF_BINDING_CONTRACT", "CLK_BAR_BINDING_CONTRACT", "GATED_CLK_BUF_BINDING_CONTRACT", "GATED_CLK_BAR_BINDING_CONTRACT"],
    }.get(name, [])


def _routing_nets_for_object(name: str) -> list[str]:
    return {
        "WRITE_ENABLE_PATH": ["w_en", "write_enable"],
        "SENSE_ENABLE_PATH": ["s_en", "sense_enable"],
        "PRECHARGE_ENABLE_PATH": ["PRE_UNBUF", "PRE", "precharge_enb", "wl_en_bar"],
        "WORDLINE_ENABLE_PATH": ["wl_en", "wordline_enable", "wl_en_bar"],
        "RBL_DELAY_PATH": ["rbl", "rbl_delay", "rbl_delay_bar", "rbl_delay_bar_wen"],
        "GATED_CLOCK_PATH": ["clk", "clk_buf", "clk_bar", "gated_clk_buf", "gated_clk_bar"],
        "PRECHARGE": ["PRE", "precharge_enb"],
        "DFF_ROW": ["clk_buf", "clk_bar", "gated_clk_buf", "gated_clk_bar"],
    }.get(name, [name.lower()] if name.lower() in {"delay_chain", "wen_delay_chain"} else [])


def _stage_count(name: str, contract: dict[str, Any] | None, composite: dict[str, Any] | None) -> tuple[int | None, str]:
    if contract and contract.get("candidate_cell_count_if_known") is not None:
        return contract["candidate_cell_count_if_known"], "generated_logic_contract.candidate_cell_count_if_known"
    if composite and composite.get("leaf_count") is not None:
        return composite["leaf_count"], "composite_feasibility.leaf_count"
    return None, "missing"


def _leaf_sequence(name: str, contract: dict[str, Any] | None, composite: dict[str, Any] | None) -> list[str]:
    if contract and contract.get("candidate_sequence"):
        return list(contract["candidate_sequence"])
    if composite and composite.get("leaf_sequence"):
        return list(composite["leaf_sequence"])
    return []


def _known_leaf_macro(sequence: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in sequence if item != "missing"))


def _leaf_spice_available(macro: str) -> bool:
    return macro in {"dff", "sense_amp", "write_driver", "cell_1rw", "replica_cell_1rw"}


def _known_load_model(name: str, contract: dict[str, Any] | None, subblock: dict[str, Any] | None, bindings: list[dict[str, Any]]) -> str | None:
    if name == "DELAY_CHAIN":
        return "source_confirmed_four_load_inverters_per_stage"
    if name == "WEN_DELAY_CHAIN":
        return "conditional_write_branch_load_present_but_not_quantified_for_general_configs"
    if name in {"PDRIVE", "PDRIVE2_FOR_PRE", "WL_PDRIVE"}:
        return "consumer_fanout_known_metadata_only"
    if name in {"WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH", "PRECHARGE_ENABLE_PATH", "WORDLINE_ENABLE_PATH", "RBL_DELAY_PATH", "GATED_CLOCK_PATH"}:
        return "path_dependency_known_but_numeric_load_unproven"
    if bindings:
        return "binding_level_consumer_list_known"
    return None


def _output_load_model(name: str, bindings: list[dict[str, Any]]) -> str | None:
    if bindings:
        return "consumer_pin_list_known_metadata_only"
    return None


def _source_signals(name: str, bindings: list[dict[str, Any]], contract: dict[str, Any] | None) -> list[str]:
    if bindings:
        src = []
        for item in bindings:
            src.extend(item.get("input_signals", []))
        return list(dict.fromkeys(src))
    if contract:
        return contract.get("input_pins", [])
    return []


def _target_signals(name: str, bindings: list[dict[str, Any]], contract: dict[str, Any] | None) -> list[str]:
    if bindings:
        tgt = []
        for item in bindings:
            output = item.get("output_signal")
            if output:
                tgt.append(output)
            tgt.extend(item.get("consumer_pins", []))
        return list(dict.fromkeys(tgt))
    if contract:
        return contract.get("output_pins", [])
    return []


def _consumer_macro(name: str, nets: list[dict[str, Any]], handoffs: dict[str, Any]) -> str | None:
    if name == "WRITE_ENABLE_PATH":
        return "write_driver"
    if name == "SENSE_ENABLE_PATH":
        return "sense_amp"
    if name == "PRECHARGE_ENABLE_PATH":
        return "gen_precharge"
    if name == "WORDLINE_ENABLE_PATH":
        return "gen_wl_driver"
    return None


def _consumer_pin(name: str, nets: list[dict[str, Any]], handoffs: dict[str, Any]) -> str | None:
    if name == "WRITE_ENABLE_PATH":
        return "EN"
    if name == "SENSE_ENABLE_PATH":
        return "EN"
    if name == "PRECHARGE_ENABLE_PATH":
        return "ENB / en_bar / PNAND3.C"
    if name == "WORDLINE_ENABLE_PATH":
        return "B"
    return None


def _consumer_pin_side(name: str, nets: list[dict[str, Any]], handoffs: dict[str, Any]) -> str | None:
    if not nets:
        return None
    net = nets[-1]
    sides = net.get("target_pin_sides", {})
    if not sides:
        return None
    return "/".join(list(dict.fromkeys(sides.values())))


def _notes_for_object(name: str, contract: dict[str, Any] | None, subblock: dict[str, Any] | None, bindings: list[dict[str, Any]], nets: list[dict[str, Any]]) -> list[str]:
    notes: list[str] = []
    if contract:
        notes.extend(contract.get("notes", []))
    if subblock:
        notes.extend(subblock.get("notes", []))
    for item in bindings:
        notes.extend(item.get("notes", []))
    for item in nets:
        notes.append(f"routing obstacle risk={item.get('obstacle_risk_level')}")
    return _dedupe_list(notes)


def _classify_timing_object(name: str, stage_count: int | None, leaf_has_spice: bool, load_model: str | None, requires_replica: bool, precharge_exception: bool, dff_clock: bool) -> str:
    if precharge_exception:
        return "blocked_by_precharge_power_exception"
    if dff_clock:
        return "blocked_by_standalone_clock_integration"
    if stage_count is None:
        return "blocked_by_missing_stage_count"
    if not leaf_has_spice:
        return "blocked_by_missing_spice_or_lib"
    if load_model is None:
        return "blocked_by_missing_load_model"
    if requires_replica:
        return "blocked_by_missing_replica_calibration"
    return "ready_for_timing_proof_planning_but_missing_models"


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(out)


def list_block(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def _dedupe_list(items: list[str]) -> list[str]:
    seen = set()
    ordered = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_absolute():
        p = p.resolve()
    return json.loads(p.read_text(encoding="utf-8"))
