"""Readonly TIME/control timing proof planning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TARGET_ORDER = [
    "DELAY_CHAIN",
    "WEN_DELAY_CHAIN",
    "PDRIVE",
    "PDRIVE2_FOR_PRE",
    "WL_PDRIVE",
    "PINV",
    "AND2",
    "AND3_COMPOSITE",
    "PNAND3_COMPOSITE",
    "PRECHARGE",
    "DFF_ROW",
    "WRITE_ENABLE_PATH",
    "SENSE_ENABLE_PATH",
    "PRECHARGE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "RBL_DELAY_PATH",
    "GATED_CLOCK_PATH",
]


MODEL_PRIORITY = {
    "gen_delay_inv": "P0",
    "gen_inv": "P0",
    "gen_nand2": "P0",
    "gen_precharge": "P1",
    "gen_wl_driver": "P1",
    "gen_col_mux_vdd_labeled": "P2",
    "dff": "P1",
    "sense_amp": "P1",
    "write_driver": "P1",
    "cell_1rw": "P2",
    "replica_cell_1rw": "P2",
}


def build_time_control_timing_proof_plan_report(
    repo_root: str | Path,
    tech_dir: str | Path,
    timing_metadata_path: str | Path,
    routing_obstacle_path: str | Path,
    legal_placement_readonly_path: str | Path,
    asset_inventory_path: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    tech = _resolve_path(root, tech_dir)
    timing_metadata = _load_json(_resolve_path(root, timing_metadata_path))
    routing_obstacle = _load_json(_resolve_path(root, routing_obstacle_path))
    legal_placement = _load_json(_resolve_path(root, legal_placement_readonly_path))
    asset_inventory = _load_json(_resolve_path(root, asset_inventory_path))

    timing_rows = {row["timing_object"]: row for row in timing_metadata["timing_object_table"]}
    planned_targets = [_build_target_plan(name, timing_rows[name]) for name in TARGET_ORDER]
    plan_map = {row["timing_object"]: row for row in planned_targets}

    model_recovery_plan = _build_model_recovery_plan(
        timing_metadata.get("spice_lib_model_inventory", []),
        asset_inventory,
    )
    ranked_tasks = _build_ranked_tasks()

    blockers = _dedupe(
        timing_metadata.get("blockers", [])
        + [f"{row['timing_object']}: {item}" for row in planned_targets for item in row["blockers"]]
    )

    audit_summary = {
        "time_control_timing_proof_planning_available": True,
        "all_required_timing_proof_targets_planned": len(planned_targets) == len(TARGET_ORDER),
        "all_required_models_identified": len(model_recovery_plan) >= 10,
        "model_recovery_plan_available": True,
        "proof_task_ranking_available": True,
        "can_start_timing_proof_without_main_flow_changes": True,
        "can_enter_generated_logic_model_recovery": True,
        "can_enter_delay_chain_testbench_planning": True,
        "timing_proof_available_now": False,
        "can_enter_physical_timing_closure_now": False,
        "can_enter_routing_proof_planning": True,
        "can_enter_physical_routing_now": False,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    report = {
        "scope": "time_control_timing_proof_planning",
        "repo_root": str(root),
        "tech_dir": str(tech),
        "input_reports_and_assets": {
            "timing_metadata": str(_resolve_path(root, timing_metadata_path)),
            "routing_obstacle": str(_resolve_path(root, routing_obstacle_path)),
            "legal_placement_readonly": str(_resolve_path(root, legal_placement_readonly_path)),
            "asset_inventory": str(_resolve_path(root, asset_inventory_path)),
        },
        "audit_summary": audit_summary,
        "timing_proof_target_plan_table": planned_targets,
        "delay_chain_proof_plan": plan_map["DELAY_CHAIN"],
        "wen_delay_chain_proof_plan": plan_map["WEN_DELAY_CHAIN"],
        "pdrive_wordline_precharge_drive_proof_plan": [
            plan_map["PDRIVE"],
            plan_map["WL_PDRIVE"],
            plan_map["PDRIVE2_FOR_PRE"],
        ],
        "write_sense_enable_proof_plan": [
            plan_map["WRITE_ENABLE_PATH"],
            plan_map["SENSE_ENABLE_PATH"],
        ],
        "precharge_timing_exception_proof_plan": [
            plan_map["PNAND3_COMPOSITE"],
            plan_map["PRECHARGE_ENABLE_PATH"],
            plan_map["PRECHARGE"],
            plan_map["PDRIVE2_FOR_PRE"],
        ],
        "dff_row_gated_clock_proof_plan": [
            plan_map["DFF_ROW"],
            plan_map["GATED_CLOCK_PATH"],
        ],
        "model_recovery_characterization_plan": model_recovery_plan,
        "ranked_timing_proof_tasks": ranked_tasks,
        "blockers": blockers,
        "next_recommended_proof_task": "recover_generated_logic_spice_or_timing_model_inventory",
        "boundary_assertions": {
            "proof_plan_is_not_proof_result": True,
            "model_inventory_is_not_model_availability": True,
            "spice_file_existence_is_not_characterized_timing_model": True,
            "routing_proof_planning_is_not_extracted_rc": True,
            "timing_proof_is_not_timing_closure": True,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
        "fallback_sources": {
            "timing_metadata_source_used": timing_metadata.get("scope"),
            "routing_obstacle_source_used": routing_obstacle.get("scope"),
            "legal_placement_source_used": legal_placement.get("scope"),
            "asset_inventory_source_used": asset_inventory.get("scope"),
            "markdown_fallback_used": False,
        },
    }
    graph = _build_graph(planned_targets, model_recovery_plan, ranked_tasks, report["audit_summary"])
    return {"report": report, "graph": graph}


def _build_target_plan(name: str, meta: dict[str, Any]) -> dict[str, Any]:
    leaf_macros = list(meta.get("known_leaf_macro", []))
    source_signals = list(meta.get("source_signals", []))
    target_signals = list(meta.get("target_signals", []))
    classification = meta.get("timing_proof_readiness_classification")

    required_spice_models = _required_spice_models(name, leaf_macros)
    required_liberty_models = _required_liberty_models(name, leaf_macros)
    required_load_models = _required_load_models(name, meta)
    required_rc_models = _required_rc_models(name)
    required_corner_definitions = _required_corner_definitions(name)
    required_waveform_checks = _required_waveform_checks(name)
    required_replica_calibration = bool(meta.get("requires_replica_path_calibration"))
    required_consumer_pin_loads = _required_consumer_pin_loads(name)
    required_input_slew_assumptions = _required_input_slew_assumptions(name)
    required_output_load_assumptions = _required_output_load_assumptions(name)
    required_path_endpoints = _required_path_endpoints(name, source_signals, target_signals)
    required_success_metric = _required_success_metric(name)
    minimal_proof_setup = _minimal_proof_setup(name, meta)
    proof_steps = _proof_steps(name, meta)
    blockers = _plan_blockers(name, meta)
    readiness_level = _readiness_level(name, classification)

    return {
        "timing_object": name,
        "current_metadata_status": "available" if meta.get("timing_metadata_available") else "missing",
        "current_blocker_classification": classification,
        "required_spice_models": required_spice_models,
        "required_liberty_models": required_liberty_models,
        "required_load_models": required_load_models,
        "required_rc_models": required_rc_models,
        "required_corner_definitions": required_corner_definitions,
        "required_waveform_checks": required_waveform_checks,
        "required_replica_calibration": required_replica_calibration,
        "required_consumer_pin_loads": required_consumer_pin_loads,
        "required_input_slew_assumptions": required_input_slew_assumptions,
        "required_output_load_assumptions": required_output_load_assumptions,
        "required_path_endpoints": required_path_endpoints,
        "required_success_metric": required_success_metric,
        "minimal_proof_setup": minimal_proof_setup,
        "proof_steps": proof_steps,
        "readiness_level": readiness_level,
        "can_start_proof_without_main_flow_changes": True,
        "requires_standalone_integration": name in {"DFF_ROW", "GATED_CLOCK_PATH"},
        "requires_routing_extraction": True,
        "requires_physical_layout": name in {"DFF_ROW", "GATED_CLOCK_PATH"},
        "requires_precharge_power_resolution": name in {"PRECHARGE", "PRECHARGE_ENABLE_PATH", "PDRIVE2_FOR_PRE", "PNAND3_COMPOSITE"},
        "can_claim_timing_proof_now": False,
        "can_claim_timing_closure_now": False,
        "blockers": blockers,
        "next_minimal_action": _next_minimal_action(name, classification),
        "notes": _plan_notes(name, meta),
    }


def _required_spice_models(name: str, leaf_macros: list[str]) -> list[str]:
    extra: list[str] = []
    if name in {"WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH"}:
        extra.extend(["write_driver", "sense_amp"])
    if name in {"PRECHARGE", "PRECHARGE_ENABLE_PATH"}:
        extra.append("gen_precharge")
    if name in {"WORDLINE_ENABLE_PATH", "WL_PDRIVE"}:
        extra.append("gen_wl_driver")
    if name in {"DFF_ROW", "GATED_CLOCK_PATH"}:
        extra.append("dff")
    return _dedupe(leaf_macros + extra)


def _required_liberty_models(name: str, leaf_macros: list[str]) -> list[str]:
    models = _required_spice_models(name, leaf_macros)
    return [f"{item}.lib_or_equivalent_delay_model" for item in models]


def _required_load_models(name: str, meta: dict[str, Any]) -> list[str]:
    rows = []
    known = meta.get("known_load_model")
    if known:
        rows.append(known)
    if name == "DELAY_CHAIN":
        rows.append("four_load_inverters_per_stage")
    if name == "WEN_DELAY_CHAIN":
        rows.append("conditional_write_branch_load_for_write_16x512_only")
    if name in {"PDRIVE", "WL_PDRIVE", "PDRIVE2_FOR_PRE"}:
        rows.extend(["fanout_load_model", "target_pin_load_model"])
    if name == "WRITE_ENABLE_PATH":
        rows.append("write_driver.EN_pin_load")
    if name == "SENSE_ENABLE_PATH":
        rows.append("sense_amp.EN_pin_load")
    if name == "PRECHARGE_ENABLE_PATH":
        rows.append("gen_precharge.ENB_pin_load")
    if name == "WORDLINE_ENABLE_PATH":
        rows.append("gen_wl_driver.B_pin_load")
    if name in {"DFF_ROW", "GATED_CLOCK_PATH"}:
        rows.append("clock_consumer_capacitance_model")
    return _dedupe(rows)


def _required_rc_models(name: str) -> list[str]:
    rows = ["interconnect_rc_extraction_or_bounded_estimate"]
    if name in {"DELAY_CHAIN", "RBL_DELAY_PATH"}:
        rows.append("replica_bitline_rc_model")
    if name in {"WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH", "PRECHARGE_ENABLE_PATH", "WORDLINE_ENABLE_PATH"}:
        rows.append("enable_net_route_rc_model")
    if name in {"DFF_ROW", "GATED_CLOCK_PATH"}:
        rows.append("clock_route_rc_model")
    return rows


def _required_corner_definitions(name: str) -> list[str]:
    rows = ["PVT_corner_definition"]
    if name in {"DELAY_CHAIN", "RBL_DELAY_PATH", "WEN_DELAY_CHAIN"}:
        rows.append("replica_delay_margin_corner")
    if name in {"PRECHARGE", "PRECHARGE_ENABLE_PATH"}:
        rows.append("precharge_recovery_corner")
    if name in {"DFF_ROW", "GATED_CLOCK_PATH"}:
        rows.append("clock_setup_hold_corner")
    return rows


def _required_waveform_checks(name: str) -> list[str]:
    rows: list[str] = []
    if name in {"DELAY_CHAIN", "WEN_DELAY_CHAIN", "GATED_CLOCK_PATH"}:
        rows.append("waveform_shape_and_pulse_width_check")
    if name in {"PRECHARGE", "PRECHARGE_ENABLE_PATH", "PDRIVE2_FOR_PRE"}:
        rows.append("active_low_precharge_enable_waveform_check")
    if name in {"WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH"}:
        rows.append("enable_arrival_window_vs_consumer_check")
    return rows


def _required_consumer_pin_loads(name: str) -> list[str]:
    return {
        "WRITE_ENABLE_PATH": ["write_driver.EN"],
        "SENSE_ENABLE_PATH": ["sense_amp.EN"],
        "PRECHARGE_ENABLE_PATH": ["gen_precharge.ENB"],
        "WORDLINE_ENABLE_PATH": ["gen_wl_driver.B"],
        "DFF_ROW": ["dff.CLK"],
        "GATED_CLOCK_PATH": ["ADDR_DFF.CLK", "DATA_DFF.CLK", "DFF_BUF.CLK"],
    }.get(name, [])


def _required_input_slew_assumptions(name: str) -> list[str]:
    return {
        "DELAY_CHAIN": ["rbl_input_slew"],
        "WEN_DELAY_CHAIN": ["rbl_delay_bar_input_slew"],
        "PDRIVE": ["clk_input_slew"],
        "PDRIVE2_FOR_PRE": ["pre_unbuf_input_slew"],
        "WL_PDRIVE": ["gated_clk_bar_input_slew"],
        "PINV": ["upstream_buffer_output_slew"],
        "AND2": ["cs_input_slew", "clk_path_input_slew"],
        "AND3_COMPOSITE": ["enable_logic_input_slew_bundle"],
        "PNAND3_COMPOSITE": ["precharge_logic_input_slew_bundle"],
        "PRECHARGE": ["PRE_input_slew"],
        "DFF_ROW": ["clk_buf_input_slew"],
        "WRITE_ENABLE_PATH": ["w_en_input_slew"],
        "SENSE_ENABLE_PATH": ["s_en_input_slew"],
        "PRECHARGE_ENABLE_PATH": ["PRE_and_wl_en_bar_input_slew"],
        "WORDLINE_ENABLE_PATH": ["wl_en_input_slew"],
        "RBL_DELAY_PATH": ["rbl_input_slew"],
        "GATED_CLOCK_PATH": ["clk_and_cs_input_slew"],
    }.get(name, ["input_slew_assumption_required"])


def _required_output_load_assumptions(name: str) -> list[str]:
    return {
        "DELAY_CHAIN": ["distributed_inverter_load_plus_consumer_pin_load"],
        "WEN_DELAY_CHAIN": ["conditional_write_branch_consumer_load"],
        "PDRIVE": ["clock_fanout_output_load"],
        "PDRIVE2_FOR_PRE": ["precharge_enable_output_load"],
        "WL_PDRIVE": ["wordline_enable_output_load"],
        "PINV": ["single_stage_inverter_output_load"],
        "AND2": ["gated_clock_output_load"],
        "AND3_COMPOSITE": ["w_en_or_s_en_output_load"],
        "PNAND3_COMPOSITE": ["PRE_UNBUF_output_load"],
        "PRECHARGE": ["bitline_precharge_device_gate_load"],
        "DFF_ROW": ["clocked_register_data_load"],
        "WRITE_ENABLE_PATH": ["write_driver_enable_load"],
        "SENSE_ENABLE_PATH": ["sense_amp_enable_load"],
        "PRECHARGE_ENABLE_PATH": ["precharge_ENB_load"],
        "WORDLINE_ENABLE_PATH": ["wordline_driver_enable_load"],
        "RBL_DELAY_PATH": ["replica_delay_path_load"],
        "GATED_CLOCK_PATH": ["gated_clock_fanout_load"],
    }.get(name, ["output_load_assumption_required"])


def _required_path_endpoints(name: str, source_signals: list[str], target_signals: list[str]) -> list[str]:
    if name == "DELAY_CHAIN":
        return ["rbl -> rbl_delay"]
    if name == "WEN_DELAY_CHAIN":
        return ["rbl_delay_bar -> rbl_delay_bar_wen -> w_en path"]
    if name == "WRITE_ENABLE_PATH":
        return ["w_en -> write_driver.EN"]
    if name == "SENSE_ENABLE_PATH":
        return ["s_en -> sense_amp.EN"]
    if name == "PRECHARGE_ENABLE_PATH":
        return ["PRE_UNBUF -> PRE -> gen_precharge.ENB"]
    if name == "WORDLINE_ENABLE_PATH":
        return ["gated_clk_bar -> wl_en -> gen_wl_driver.B"]
    if name == "DFF_ROW":
        return ["clk_buf -> dff.CLK"]
    if name == "GATED_CLOCK_PATH":
        return ["clk -> clk_buf -> clk_bar/gated_clk_buf/gated_clk_bar"]
    return _dedupe(source_signals + target_signals)


def _required_success_metric(name: str) -> str:
    mapping = {
        "DELAY_CHAIN": "bounded delay across corners with replica calibration and waveform integrity",
        "WEN_DELAY_CHAIN": "conditional write-only delay proof for 16x512 without over-generalization",
        "PDRIVE": "clock buffer chain delay/slew bound at all named consumers",
        "PDRIVE2_FOR_PRE": "PRE driver delay/slew bound with precharge exception explicitly retained",
        "WL_PDRIVE": "wl_en arrival and slew bound at wordline-enable consumers",
        "PINV": "single-inversion helper delay bound under declared load set",
        "AND2": "gated clock logic delay bound with cs/clock slew corners",
        "AND3_COMPOSITE": "logical enable generation bound at output consumer pins",
        "PNAND3_COMPOSITE": "PRE_UNBUF timing bound before final precharge drive stage",
        "PRECHARGE": "precharge ENB handoff timing bound, without claiming physical closure",
        "DFF_ROW": "clock arrival and capture assumptions documented for dff row",
        "WRITE_ENABLE_PATH": "w_en reaches write_driver.EN within declared enable window",
        "SENSE_ENABLE_PATH": "s_en reaches sense_amp.EN within declared sense window",
        "PRECHARGE_ENABLE_PATH": "PRE/ENB relationship proven under active-low semantics",
        "WORDLINE_ENABLE_PATH": "wl_en reaches gen_wl_driver.B with active-high semantics preserved",
        "RBL_DELAY_PATH": "replica delay path bound from rbl to downstream consumers",
        "GATED_CLOCK_PATH": "clock gating path delay/slew/pulse width bounded at gated clock consumers",
    }
    return mapping[name]


def _minimal_proof_setup(name: str, meta: dict[str, Any]) -> list[str]:
    steps = [
        "reuse current metadata report as structural source of truth",
        "bind leaf macro names and consumer endpoints exactly as reported",
        "declare PVT corner set and success metric before simulation",
    ]
    if name in {"DELAY_CHAIN", "WEN_DELAY_CHAIN"}:
        steps.extend(
            [
                "prepare chain-level SPICE or equivalent delay model for gen_delay_inv",
                "instantiate declared stages with explicit load-per-stage assumptions",
                "include interconnect RC estimate and waveform probes",
            ]
        )
    elif name in {"PDRIVE", "WL_PDRIVE", "PDRIVE2_FOR_PRE", "PINV", "AND2", "AND3_COMPOSITE", "PNAND3_COMPOSITE"}:
        steps.extend(
            [
                "prepare generated-logic leaf model inventory",
                "construct focused path-level testbench with declared fanout/load assumptions",
            ]
        )
    elif name in {"WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH", "PRECHARGE_ENABLE_PATH", "WORDLINE_ENABLE_PATH"}:
        steps.extend(
            [
                "compose producer logic + consumer pin load handoff testbench",
                "include route RC estimate from obstacle report as bounded placeholder",
            ]
        )
    elif name in {"DFF_ROW", "GATED_CLOCK_PATH"}:
        steps.extend(
            [
                "prepare dff clock pin timing model or equivalent SPICE harness",
                "define clock route/load abstraction without modifying standalone",
            ]
        )
    elif name == "PRECHARGE":
        steps.extend(
            [
                "retain precharge_no_local_gnd_exception in setup notes",
                "treat proof as planning-only until power exception is resolved",
            ]
        )
    return _dedupe(steps)


def _proof_steps(name: str, meta: dict[str, Any]) -> list[str]:
    steps = [
        "inventory required models, loads, corners, and route abstractions",
        "build target-specific testbench or equivalent delay abstraction",
        "run per-corner delay/slew/waveform measurement",
        "compare measured results against declared success metric",
        "record proof artifact boundaries and unresolved assumptions",
    ]
    if name == "DELAY_CHAIN":
        steps.insert(1, "recover_or_characterize_gen_delay_inv_timing_model")
        steps.insert(3, "calibrate replica path assumptions against rbl/load model")
    if name == "WEN_DELAY_CHAIN":
        steps.insert(1, "preserve conditional scope: write + 16x512 only")
    if name in {"WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH"}:
        steps.insert(3, "check enable arrival window at consumer enable pin")
    if name in {"PRECHARGE", "PRECHARGE_ENABLE_PATH", "PDRIVE2_FOR_PRE"}:
        steps.insert(3, "retain precharge power exception and avoid closure claim")
    if name in {"DFF_ROW", "GATED_CLOCK_PATH"}:
        steps.insert(3, "check clock pulse width / setup-hold assumptions at dff consumers")
    return _dedupe(steps)


def _plan_blockers(name: str, meta: dict[str, Any]) -> list[str]:
    blockers = list(meta.get("blockers", []))
    if name in {"WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH"}:
        blockers.append("consumer enable pin load not yet numerically modeled")
        blockers.append("enable arrival window not yet quantified")
    if name in {"PDRIVE", "WL_PDRIVE", "PDRIVE2_FOR_PRE"}:
        blockers.append("generated logic fanout load model missing")
    if name == "DELAY_CHAIN":
        blockers.append("gen_delay_inv timing model missing")
    if name == "WEN_DELAY_CHAIN":
        blockers.append("conditional write-branch model missing")
    if name in {"DFF_ROW", "GATED_CLOCK_PATH"}:
        blockers.append("clock tree or clock route model missing")
    return _dedupe(blockers)


def _next_minimal_action(name: str, classification: str) -> str:
    if name == "DELAY_CHAIN":
        return "recover_or_characterize_gen_delay_inv_timing_model"
    if name == "WEN_DELAY_CHAIN":
        return "plan_conditional_wen_delay_chain_testbench_for_write_16x512"
    if name in {"PDRIVE", "WL_PDRIVE", "PDRIVE2_FOR_PRE", "PINV", "AND2", "AND3_COMPOSITE", "PNAND3_COMPOSITE"}:
        return "recover_generated_logic_spice_or_timing_model_inventory"
    if name in {"WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH"}:
        return "define_consumer_enable_pin_load_and_enable_window_model"
    if name in {"PRECHARGE", "PRECHARGE_ENABLE_PATH"}:
        return "retain_precharge_exception_and_plan_power_resolution_inputs"
    if name in {"DFF_ROW", "GATED_CLOCK_PATH"}:
        return "prepare_dff_clock_path_model_plan"
    if name == "WORDLINE_ENABLE_PATH":
        return "define_wordline_enable_consumer_load_model"
    if name == "RBL_DELAY_PATH":
        return "combine_delay_chain_and_rbl_consumer_rc_assumptions"
    return f"resolve_{classification}"


def _plan_notes(name: str, meta: dict[str, Any]) -> list[str]:
    notes = list(meta.get("notes", []))
    if name == "DELAY_CHAIN":
        notes.extend(
            [
                "stage_count = 9",
                "leaf = gen_delay_inv",
                "load_model_needed = four_load_inverters_per_stage",
                "requires_gen_delay_inv_spice_or_equivalent_model = True",
                "requires_input_slew = True",
                "requires_output_load = True",
                "requires_corner_definition = True",
                "requires_replica_path_calibration = True",
                "requires_routing_rc = True",
                "requires_waveform_check = True",
                "can_claim_delay_proof_now = False",
            ]
        )
    if name == "WEN_DELAY_CHAIN":
        notes.extend(
            [
                "stage_count = 6",
                "leaf = gen_delay_inv",
                "conditional_scope = write + 16x512 only",
                "requires_write_path_timing_model = True",
                "requires_gen_delay_inv_model = True",
                "requires_rc = True",
                "requires_waveform_check = True",
                "can_claim_wen_delay_proof_now = False",
            ]
        )
    if name in {"PDRIVE", "WL_PDRIVE", "PDRIVE2_FOR_PRE"}:
        notes.extend(
            [
                "requires_gen_inv_timing_model = True",
                "requires_fanout_load_model = True",
                "requires_target_pin_load = True",
                "requires_routing_rc = True",
                "pdrive_timing_proof_available_now = False",
            ]
        )
    if name in {"WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH"}:
        notes.extend(
            [
                "requires_consumer_enable_pin_load = True",
                "requires_logic_path_stage_count_resolution = True",
                "requires_routing_rc = True",
                "requires_enable_arrival_window = True",
                "handoff_timing_proof_available_now = False",
            ]
        )
    if name in {"PRECHARGE", "PRECHARGE_ENABLE_PATH"}:
        notes.extend(
            [
                "precharge_no_local_gnd_exception = True",
                "precharge_power_exception_retained = True",
                "precharge_timing_proof_available_now = False",
                "precharge_safe_for_timing_proof_planning = True",
                "precharge_safe_for_timing_closure = False",
                "requires_precharge_power_resolution_for_physical_timing = True",
            ]
        )
    if name in {"DFF_ROW", "GATED_CLOCK_PATH"}:
        notes.extend(
            [
                "clock_distribution_proven = False",
                "dff_row_timing_proof_available_now = False",
                "standalone_integration_required = True",
                "requires_clock_tree_or_clock_route_model = True",
            ]
        )
    return _dedupe(notes)


def _readiness_level(name: str, classification: str) -> str:
    if classification == "blocked_by_precharge_power_exception":
        return "planning_only_precharge_exception"
    if classification == "blocked_by_standalone_clock_integration":
        return "planning_ready_clock_model_missing"
    if classification == "blocked_by_missing_spice_or_lib":
        return "planning_ready_model_recovery_needed"
    if classification == "blocked_by_missing_stage_count":
        return "planning_ready_path_resolution_needed"
    return "planning_ready"


def _build_model_recovery_plan(
    model_inventory: list[dict[str, Any]],
    asset_inventory: dict[str, Any],
) -> list[dict[str, Any]]:
    asset_spice = {
        row.get("cell_or_macro"): row
        for row in asset_inventory.get("spice_cdl_inventory", {}).get("items", [])
    }
    rows = []
    for item in model_inventory:
        macro = item["macro_name"]
        spice_exists = bool(item.get("spice_exists"))
        lib_exists = bool(item.get("lib_exists"))
        asset = asset_spice.get(macro, {})
        rows.append(
            {
                "model_name": macro,
                "macro_or_cell": macro,
                "current_assets": _dedupe(
                    ([f"spice:{asset.get('spice_path')}"] if asset.get("spice_path") else [])
                    + ([note for note in item.get("notes", []) if note.startswith("gds path:")])
                    + (["lib:not_found"] if not lib_exists else [])
                ),
                "spice_available": spice_exists,
                "lib_available": lib_exists,
                "gds_available": any(str(note).startswith("gds path:") for note in item.get("notes", [])),
                "can_recover_from_existing_repo": spice_exists or any(str(note).startswith("gds path:") for note in item.get("notes", [])),
                "requires_manual_model_creation": not spice_exists and not lib_exists,
                "requires_characterization": True,
                "requires_pdk_device_models": True,
                "requires_testbench": True,
                "required_testbench_type": _model_testbench_type(macro),
                "priority": MODEL_PRIORITY.get(macro, "P3"),
                "unblocks": _model_unblocks(macro),
            }
        )
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    rows.sort(key=lambda row: (order.get(row["priority"], 9), row["model_name"]))
    return rows


def _model_testbench_type(macro: str) -> str:
    return {
        "gen_delay_inv": "delay_chain_stage_sweep",
        "gen_inv": "inverter_slew_load_sweep",
        "gen_nand2": "nand2_slew_load_sweep",
        "gen_precharge": "precharge_enable_handoff_sweep",
        "gen_wl_driver": "wordline_enable_handoff_sweep",
        "gen_col_mux_vdd_labeled": "column_mux_handoff_reference_sweep",
        "dff": "clock_to_q_setup_hold_sweep",
        "sense_amp": "sense_enable_handoff_sweep",
        "write_driver": "write_enable_handoff_sweep",
        "cell_1rw": "replica_bitline_load_reference_sweep",
        "replica_cell_1rw": "replica_delay_reference_sweep",
    }.get(macro, "manual_model_inventory_recovery")


def _model_unblocks(macro: str) -> list[str]:
    return {
        "gen_delay_inv": ["DELAY_CHAIN", "WEN_DELAY_CHAIN", "RBL_DELAY_PATH"],
        "gen_inv": ["PDRIVE", "PDRIVE2_FOR_PRE", "WL_PDRIVE", "PINV", "AND2", "AND3_COMPOSITE", "PNAND3_COMPOSITE"],
        "gen_nand2": ["AND2", "AND3_COMPOSITE", "PNAND3_COMPOSITE", "WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH", "PRECHARGE_ENABLE_PATH"],
        "gen_precharge": ["PRECHARGE", "PRECHARGE_ENABLE_PATH"],
        "gen_wl_driver": ["WL_PDRIVE", "WORDLINE_ENABLE_PATH"],
        "gen_col_mux_vdd_labeled": ["future_read_path_handoff_reference_only"],
        "dff": ["DFF_ROW", "GATED_CLOCK_PATH"],
        "sense_amp": ["SENSE_ENABLE_PATH"],
        "write_driver": ["WRITE_ENABLE_PATH"],
        "cell_1rw": ["RBL_DELAY_PATH"],
        "replica_cell_1rw": ["DELAY_CHAIN", "RBL_DELAY_PATH"],
    }.get(macro, ["manual_classification_needed"])


def _build_ranked_tasks() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "task_name": "recover_generated_logic_spice_or_timing_model_inventory",
            "why_first": "generated logic macros remain the dominant blocker across delay, clock, and enable paths",
            "required_inputs": ["time_control_timing_metadata_report", "repo_physical_asset_inventory", "generated_logic_contract_report"],
            "expected_output": "source-backed inventory of recoverable SPICE/LIB/timing-model assets and remaining gaps",
            "does_not_modify_main_flow": True,
            "can_run_readonly": True,
            "unblocks": ["DELAY_CHAIN", "WEN_DELAY_CHAIN", "PDRIVE", "WL_PDRIVE", "PINV", "AND2", "AND3_COMPOSITE", "PNAND3_COMPOSITE"],
            "risk": "low",
            "pass_criteria": "all generated logic leaf macros classified as recoverable, characterize-needed, or missing with evidence",
            "fail_criteria": "model sources remain ambiguous or untracked",
        },
        {
            "rank": 2,
            "task_name": "gen_inv_gen_nand2_gen_delay_inv_characterization_plan",
            "why_first": "these three leaves cover most timing-sensitive TIME/control logic",
            "required_inputs": ["generated_logic_model_inventory", "pdk_device_models", "leaf pin metadata"],
            "expected_output": "characterization matrix, corners, slews, loads, and reusable testbench specs",
            "does_not_modify_main_flow": True,
            "can_run_readonly": True,
            "unblocks": ["PDRIVE", "WL_PDRIVE", "PINV", "AND2", "AND3_COMPOSITE", "PNAND3_COMPOSITE", "DELAY_CHAIN", "WEN_DELAY_CHAIN"],
            "risk": "medium",
            "pass_criteria": "all required generated leaves have a concrete characterization recipe",
            "fail_criteria": "testbench scope still undefined",
        },
        {
            "rank": 3,
            "task_name": "delay_chain_spice_testbench_plan",
            "why_first": "delay_chain is the most timing-sensitive metadata block and gates replica-path proof",
            "required_inputs": ["gen_delay_inv_model_plan", "replica_cell_load_reference", "routing_rc_assumptions"],
            "expected_output": "DELAY_CHAIN proof harness plan with stage, load, RC, corner, and waveform probes",
            "does_not_modify_main_flow": True,
            "can_run_readonly": True,
            "unblocks": ["DELAY_CHAIN", "RBL_DELAY_PATH"],
            "risk": "medium",
            "pass_criteria": "plan explicitly covers 9 stages, 4 loads/stage, replica calibration, and waveform checks",
            "fail_criteria": "plan omits RC, calibration, or endpoint definitions",
        },
        {
            "rank": 4,
            "task_name": "wen_delay_chain_conditional_testbench_plan",
            "why_first": "the write+16x512 exception must stay scoped and must not leak into general timing assumptions",
            "required_inputs": ["gen_delay_inv_model_plan", "conditional_wen_binding_contract", "write_path_load_assumptions"],
            "expected_output": "conditional-only WEN delay chain proof harness plan",
            "does_not_modify_main_flow": True,
            "can_run_readonly": True,
            "unblocks": ["WEN_DELAY_CHAIN", "WRITE_ENABLE_PATH"],
            "risk": "medium",
            "pass_criteria": "special-case scope is preserved exactly and write-path dependency is explicit",
            "fail_criteria": "conditional branch is generalized or underspecified",
        },
        {
            "rank": 5,
            "task_name": "pdrive_enable_path_load_model_plan",
            "why_first": "clock/enable fanout and consumer pin loads are currently metadata-only",
            "required_inputs": ["signal_binding_report", "consumer_contracts", "routing_obstacle_report"],
            "expected_output": "load model bundle for PDRIVE, WL_PDRIVE, WRITE_ENABLE_PATH, and SENSE_ENABLE_PATH",
            "does_not_modify_main_flow": True,
            "can_run_readonly": True,
            "unblocks": ["PDRIVE", "WL_PDRIVE", "WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH", "WORDLINE_ENABLE_PATH"],
            "risk": "low",
            "pass_criteria": "all consumer loads and arrival windows are explicitly named and bounded",
            "fail_criteria": "consumer-side load assumptions remain implicit",
        },
        {
            "rank": 6,
            "task_name": "dff_clock_path_model_plan",
            "why_first": "clock proof stays blocked until dff consumers and gated clock route assumptions are modeled",
            "required_inputs": ["dff_spice_asset", "timing_metadata_report", "routing_obstacle_report"],
            "expected_output": "DFF_ROW/GATED_CLOCK proof harness plan with setup/hold and pulse-width checks",
            "does_not_modify_main_flow": True,
            "can_run_readonly": True,
            "unblocks": ["DFF_ROW", "GATED_CLOCK_PATH"],
            "risk": "medium",
            "pass_criteria": "clock consumer loads and route model assumptions are explicit",
            "fail_criteria": "clock route remains abstract without measurable success metric",
        },
        {
            "rank": 7,
            "task_name": "precharge_timing_exception_resolution_plan",
            "why_first": "precharge remains a known exception and must be quarantined before any closure claim",
            "required_inputs": ["precharge_constraint_bundle", "routing_obstacle_report", "power_rail_continuity_report"],
            "expected_output": "exception-retaining plan for PRE path timing proof inputs and physical blockers",
            "does_not_modify_main_flow": True,
            "can_run_readonly": True,
            "unblocks": ["PRECHARGE", "PRECHARGE_ENABLE_PATH", "PDRIVE2_FOR_PRE", "PNAND3_COMPOSITE"],
            "risk": "medium",
            "pass_criteria": "precharge power exception is preserved while proof inputs are clearly separated from closure",
            "fail_criteria": "report conflates planning with signoff or claims physical timing readiness",
        },
    ]


def _build_graph(
    targets: list[dict[str, Any]],
    models: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    nodes = [{"id": "proof_planning", "kind": "root", "label": "time_control_timing_proof_planning"}]
    edges = []
    for row in targets:
        node_id = f"target:{row['timing_object']}"
        nodes.append({"id": node_id, "kind": "timing_target", "label": row["timing_object"]})
        edges.append({"from": "proof_planning", "to": node_id, "relation": "plans"})
        for model in row["required_spice_models"]:
            model_id = f"model:{model}"
            if not any(node["id"] == model_id for node in nodes):
                nodes.append({"id": model_id, "kind": "model", "label": model})
            edges.append({"from": node_id, "to": model_id, "relation": "requires_model"})
    for task in tasks:
        task_id = f"task:{task['rank']}"
        nodes.append({"id": task_id, "kind": "task", "label": task["task_name"]})
        edges.append({"from": "proof_planning", "to": task_id, "relation": "ranked_task"})
        for item in task["unblocks"]:
            edges.append({"from": task_id, "to": f"target:{item}", "relation": "unblocks"})
    return {"scope": "time_control_timing_proof_planning", "nodes": nodes, "edges": edges, "summary": summary}


def format_time_control_timing_proof_plan_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield TIME Control Timing Proof Planning Report",
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
            "## Timing Proof Target Plan Table",
            "",
            _md_table(
                ["object", "classification", "readiness", "next action", "proof now", "closure now"],
                [
                    [
                        row["timing_object"],
                        row["current_blocker_classification"],
                        row["readiness_level"],
                        row["next_minimal_action"],
                        row["can_claim_timing_proof_now"],
                        row["can_claim_timing_closure_now"],
                    ]
                    for row in report["timing_proof_target_plan_table"]
                ],
            ),
            "",
            "## DELAY_CHAIN Proof Plan",
            "",
            "```json",
            json.dumps(report["delay_chain_proof_plan"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## WEN_DELAY_CHAIN Proof Plan",
            "",
            "```json",
            json.dumps(report["wen_delay_chain_proof_plan"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## PDRIVE / WL_PDRIVE / PRE Drive Proof Plan",
            "",
            "```json",
            json.dumps(report["pdrive_wordline_precharge_drive_proof_plan"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Write / Sense Enable Proof Plan",
            "",
            "```json",
            json.dumps(report["write_sense_enable_proof_plan"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## PRECHARGE Timing Exception Proof Plan",
            "",
            "```json",
            json.dumps(report["precharge_timing_exception_proof_plan"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## DFF Row / Gated Clock Proof Plan",
            "",
            "```json",
            json.dumps(report["dff_row_gated_clock_proof_plan"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Model Recovery / Characterization Plan",
            "",
            _md_table(
                ["model", "spice", "lib", "priority", "testbench", "unblocks"],
                [
                    [
                        row["model_name"],
                        row["spice_available"],
                        row["lib_available"],
                        row["priority"],
                        row["required_testbench_type"],
                        ", ".join(row["unblocks"]),
                    ]
                    for row in report["model_recovery_characterization_plan"]
                ],
            ),
            "",
            "## Ranked Proof Tasks",
            "",
            _md_table(
                ["rank", "task", "why first", "unblocks", "risk"],
                [
                    [
                        row["rank"],
                        row["task_name"],
                        row["why_first"],
                        ", ".join(row["unblocks"]),
                        row["risk"],
                    ]
                    for row in report["ranked_timing_proof_tasks"]
                ],
            ),
            "",
            "## Blockers",
            "",
            _list_block(report["blockers"]),
            "",
            "## Boundary Assertions",
            "",
            "```json",
            json.dumps(report["boundary_assertions"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Next Recommended Proof Task",
            "",
            f"- `{report['next_recommended_proof_task']}`",
        ]
    )


def _resolve_path(root: Path, path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return (root / p).resolve()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def _list_block(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out
