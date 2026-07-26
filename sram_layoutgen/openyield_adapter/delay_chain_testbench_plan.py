"""Readonly DELAY_CHAIN SPICE testbench planning.

This module builds a planning-only report for the OpenYield DELAY_CHAIN timing
object. It does not emit runnable SPICE, does not validate timing models, and
does not authorize any physical-flow change.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_delay_chain_testbench_plan_report(
    repo_root: str | Path,
    tech_dir: str | Path,
    model_recovery_path: str | Path,
    timing_proof_plan_path: str | Path,
    timing_metadata_path: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    tech = _resolve_path(root, tech_dir)
    model_recovery = _load_json(_resolve_path(root, model_recovery_path))
    timing_proof = _load_json(_resolve_path(root, timing_proof_plan_path))
    timing_metadata = _load_json(_resolve_path(root, timing_metadata_path))
    generated_logic_contract = _load_optional_json(root / "docs" / "openyield_time_control_generated_logic_contract_report.json")
    signal_binding = _load_optional_json(root / "docs" / "openyield_time_control_signal_binding_report.json")
    asset_inventory = _load_optional_json(root / "docs" / "openyield_repo_physical_asset_inventory_report.json")

    delay_metadata = _find_timing_object(timing_metadata, "DELAY_CHAIN")
    delay_proof = _find_timing_object(timing_proof, "DELAY_CHAIN", table_key="timing_proof_target_plan_table")
    model_row = _find_model(model_recovery, "gen_delay_inv")
    generated_contract = _find_generated_logic_contract(generated_logic_contract, "DELAY_CHAIN_GENERATED_LOGIC_CONTRACT")
    signal_row = _find_signal_binding(signal_binding, "rbl_delay")

    stage_count = _coalesce(
        delay_metadata.get("stage_count"),
        generated_contract.get("candidate_cell_count_if_known"),
        9,
    )
    stage_plan = _build_stage_plan(stage_count)
    pdk_candidates = _find_pdk_model_candidates(tech)
    artifact_contract = _build_artifact_contract()
    corner_plan = _build_corner_plan()
    measurement_plan = _build_measurement_plan()
    model_dependencies = _build_model_dependencies(model_row, pdk_candidates)
    ranked_tasks = _build_ranked_tasks()
    testbench_plan = _build_testbench_plan(
        stage_count=stage_count,
        model_row=model_row,
        generated_contract=generated_contract,
        signal_row=signal_row,
        pdk_candidates=pdk_candidates,
    )
    blockers = _dedupe(
        [
            "gen_delay_inv has no usable SPICE or Liberty model yet.",
            "PDK transistor model path is not yet proven in current planning inputs.",
            "PVT corner definitions remain unspecified for execution.",
            "Replica bitline RC/load calibration is not yet quantified.",
            "Input slew values are not yet quantified.",
            "Output load values are not yet quantified.",
            "Waveform threshold levels are not yet quantified.",
            "No executable simulation is authorized in this step.",
        ]
        + list(delay_metadata.get("blockers", []))
        + list(delay_proof.get("blockers", []))
        + list(model_recovery.get("blockers", []))
    )

    audit_summary = {
        "delay_chain_spice_testbench_plan_available": True,
        "delay_chain_structure_captured": True,
        "stage_count_confirmed": stage_count == 9,
        "four_load_inverter_policy_captured": True,
        "model_dependencies_identified": True,
        "measurement_plan_available": True,
        "corner_plan_available": True,
        "artifact_contract_available": True,
        "can_emit_testbench_template_now": True,
        "can_run_testbench_now": False,
        "can_claim_delay_proof_now": False,
        "can_claim_timing_closure_now": False,
        "can_enter_gen_delay_inv_transistor_netlist_recovery_plan": True,
        "can_enter_four_load_inverter_stage_model_plan": True,
        "can_enter_wen_delay_chain_conditional_testbench_plan": True,
        "can_enter_physical_timing_closure_now": False,
        "can_enter_physical_routing_now": False,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    report = {
        "scope": "delay_chain_spice_testbench_plan",
        "repo_root": str(root),
        "tech_dir": str(tech),
        "input_reports_and_assets": {
            "model_recovery": str(_resolve_path(root, model_recovery_path)),
            "timing_proof_plan": str(_resolve_path(root, timing_proof_plan_path)),
            "timing_metadata": str(_resolve_path(root, timing_metadata_path)),
            "generated_logic_contract": str(root / "docs" / "openyield_time_control_generated_logic_contract_report.json"),
            "signal_binding": str(root / "docs" / "openyield_time_control_signal_binding_report.json"),
            "repo_asset_inventory": str(root / "docs" / "openyield_repo_physical_asset_inventory_report.json"),
        },
        "audit_summary": audit_summary,
        "delay_chain_structure_plan": {
            "timing_object": "DELAY_CHAIN",
            "timing_role": "replica_bitline_delay / rbl_delay_generation",
            "source_signal": "rbl",
            "target_signal": "rbl_delay",
            "leaf": "gen_delay_inv",
            "stage_count": stage_count,
            "load_model_source": "source_confirmed_four_load_inverters_per_stage",
            "requires_replica_path_calibration": True,
            "requires_parasitic_estimate": True,
            "requires_waveform_check": True,
            "can_claim_delay_proof_now": False,
            "stage_plan": stage_plan,
        },
        "per_stage_load_plan": stage_plan,
        "spice_testbench_plan": testbench_plan,
        "artifact_contract": artifact_contract,
        "corner_plan": corner_plan,
        "corner_definition_available": False,
        "measurement_plan": measurement_plan,
        "model_dependency_table": model_dependencies,
        "ranked_next_tasks": ranked_tasks,
        "blockers": blockers,
        "next_recommended_proof_task": "gen_delay_inv_transistor_netlist_recovery_plan",
        "boundary_assertions": {
            "testbench_plan != executable_simulation": True,
            "testbench_template != validated_timing_model": True,
            "generated_source != SPICE_model": True,
            "stage_count != delay_proof": True,
            "load_policy != quantified_load_proof": True,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
        "fallback_sources": {
            "generated_logic_contract_used": generated_logic_contract.get("scope") if generated_logic_contract else None,
            "signal_binding_used": signal_binding.get("scope") if signal_binding else None,
            "asset_inventory_used": asset_inventory.get("scope") if asset_inventory else None,
            "filesystem_pdk_scan_used": True,
            "markdown_fallback_used": False,
        },
    }
    graph = _build_graph(report)
    return {"report": report, "graph": graph}


def format_delay_chain_testbench_plan_markdown(report: dict[str, Any]) -> str:
    artifact_rows = [
        [
            row["artifact_name"],
            row["artifact_type"],
            row["allowed_now"],
            row["requires_model_before_use"],
            row["requires_user_approval_before_simulation"],
            row["is_proof_result"],
        ]
        for row in report["artifact_contract"]["future_artifacts"]
    ]
    corner_rows = [
        [
            row["corner_name"],
            row["process_corner"],
            row["voltage"],
            row["temperature"],
            row["requires_user_or_pdk_definition"],
            row["safe_to_use_for_planning"],
        ]
        for row in report["corner_plan"]
    ]
    measurement_rows = [
        [
            row["measurement_name"],
            row["from_node"],
            row["to_node"],
            row["edge"],
            row["threshold_policy"],
            row["can_evaluate_now"],
        ]
        for row in report["measurement_plan"]
    ]
    model_rows = [
        [
            row["model_name"],
            row["current_status"],
            row["source_candidate"],
            row["can_use_now"],
            row["requires_characterization"],
            row["blocker_level"],
        ]
        for row in report["model_dependency_table"]
    ]
    task_rows = [
        [
            idx + 1,
            row["task_name"],
            row["can_do_readonly"],
            row["modifies_main_flow"],
            ", ".join(row["unblocks"]),
        ]
        for idx, row in enumerate(report["ranked_next_tasks"])
    ]

    lines = [
        "# OpenYield Delay Chain Testbench Plan Report",
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
        "## DELAY_CHAIN Structure Plan",
        "",
        "```json",
        json.dumps(report["delay_chain_structure_plan"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## SPICE Testbench Plan",
        "",
        "```json",
        json.dumps(report["spice_testbench_plan"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Artifact Contract",
        "",
        _md_table(
            ["artifact", "type", "allowed now", "model before use", "approval before sim", "is proof result"],
            artifact_rows,
        ),
        "",
        "## Corner Plan",
        "",
        _md_table(
            ["corner", "process", "voltage", "temperature", "needs definition", "planning safe"],
            corner_rows,
        ),
        "",
        "## Measurement Plan",
        "",
        _md_table(
            ["measurement", "from", "to", "edge", "threshold", "can evaluate now"],
            measurement_rows,
        ),
        "",
        "## Model Dependency Table",
        "",
        _md_table(
            ["model", "status", "source candidate", "can use now", "needs characterization", "blocker"],
            model_rows,
        ),
        "",
        "## Ranked Next Tasks",
        "",
        _md_table(
            ["rank", "task", "readonly", "modifies main flow", "unblocks"],
            task_rows,
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
    return "\n".join(lines)


def _build_stage_plan(stage_count: int) -> list[dict[str, Any]]:
    rows = []
    for index in range(stage_count):
        rows.append(
            {
                "stage_index": index + 1,
                "stage_i.input": "rbl" if index == 0 else f"planned_stage_{index}_out",
                "stage_i.output": "rbl_delay" if index == stage_count - 1 else f"planned_stage_{index + 1}_out",
                "stage_i.load_inverters": 4,
                "stage_i.load_model_status": "source_confirmed_count_only_not_quantified",
                "stage_i.requires_gen_delay_inv_model": True,
                "stage_i.requires_input_slew": True,
                "stage_i.requires_output_load": True,
                "stage_i.requires_rc": True,
            }
        )
    return rows


def _build_testbench_plan(
    *,
    stage_count: int,
    model_row: dict[str, Any],
    generated_contract: dict[str, Any],
    signal_row: dict[str, Any],
    pdk_candidates: list[str],
) -> dict[str, Any]:
    required_pin_order = ["A", "Z", "vdd", "gnd"]
    required_generated_logic_models = [
        {
            "model_name": "gen_delay_inv",
            "status": "missing_usable_spice_or_lib",
            "source": model_row.get("recovery_source_type"),
        },
        {
            "model_name": "gen_inv",
            "status": "needed_for_four_load_stage_model",
            "source": "future_four_load_inverter_stage_model_plan",
        },
    ]
    return {
        "testbench_name": "openyield_delay_chain_stage9_plan_only",
        "target_timing_object": "DELAY_CHAIN",
        "chain_stage_count": stage_count,
        "leaf_macro": "gen_delay_inv",
        "leaf_model_status": "recoverable_from_generator_source_but_not_usable_now",
        "leaf_model_source": model_row.get("recovery_source_type", "unknown"),
        "required_subckt_name": "gen_delay_inv",
        "required_pin_order": required_pin_order,
        "required_pin_order_status": "candidate_from_gds_pin_metadata_not_validated_spice_order",
        "input_signal": "rbl",
        "output_signal": "rbl_delay",
        "input_slew_parameters": {
            "slew_name": "rbl_input_slew",
            "value": None,
            "known": False,
            "source_of_value": "requires_user_or_characterization_definition",
        },
        "supply_parameters": {
            "vdd": None,
            "gnd": "0_reference_only",
            "voltage_known": False,
            "source_of_value": "requires_user_or_pdk_definition",
        },
        "temperature_parameters": {
            "temperature": None,
            "temperature_known": False,
            "source_of_value": "requires_user_or_pdk_definition",
        },
        "corner_parameters": [
            "PVT_corner_definition",
            "replica_delay_margin_corner",
        ],
        "load_model": "source_confirmed_four_load_inverters_per_stage",
        "per_stage_load_policy": "attach four inverter loads to each stage output as planning-only symbolic load",
        "four_load_inverters_per_stage_encoded": True,
        "output_load_policy": "final stage requires consumer pin load plus distributed stage load placeholder",
        "rc_placeholder_policy": "use named RC placeholders only; no quantified RC may be claimed now",
        "replica_calibration_policy": "must calibrate chain result against replica bitline RC/load before proof",
        "waveform_probe_points": [
            "rbl",
            "planned_stage_1_out",
            "planned_stage_5_out",
            "rbl_delay",
        ],
        "delay_measurement_points": [
            {
                "name": "rbl_to_rbl_delay",
                "from": "rbl",
                "to": "rbl_delay",
                "status": "planning_only",
            }
        ],
        "slew_measurement_points": [
            {"name": "rbl_input_slew", "node": "rbl", "status": "requires_voltage_thresholds"},
            {"name": "rbl_delay_output_slew", "node": "rbl_delay", "status": "requires_voltage_thresholds"},
        ],
        "pulse_width_measurement_points": [
            {"name": "rbl_delay_pulse_width", "node": "rbl_delay", "status": "requires_simulation"}
        ],
        "success_metrics": [
            "bounded delay across corners with replica calibration and waveform integrity",
            "all nine stages instantiated in template structure",
            "four-load-per-stage policy preserved in template metadata",
        ],
        "failure_metrics": [
            "missing gen_delay_inv model",
            "missing PDK transistor model",
            "missing corner definition",
            "missing replica RC/load calibration",
            "missing waveform threshold policy",
        ],
        "required_includes": _dedupe(
            [candidate for candidate in pdk_candidates]
            + [path for path in model_row.get("python_generator_paths", [])]
        ),
        "required_device_models": ["PDK transistor models"],
        "required_generated_logic_models": required_generated_logic_models,
        "required_artifacts_before_run": [
            "gen_delay_inv transistor-level subckt",
            "four-load inverter stage model",
            "PVT corner definition",
            "replica bitline RC/load model",
            "consumer pin load model",
            "measurement threshold definition",
        ],
        "can_emit_testbench_template_now": True,
        "can_run_testbench_now": False,
        "can_claim_delay_proof_now": False,
        "can_claim_timing_closure_now": False,
        "blockers": [
            "No validated gen_delay_inv SPICE model exists yet.",
            "No validated PDK device model include path is bound in current report.",
            "No numerical corner/slew/load values are authorized in this step.",
            "No replica calibration data exists yet.",
        ],
        "contract_evidence": {
            "generated_logic_contract_name": generated_contract.get("contract_name"),
            "generated_logic_contract_input_pins": generated_contract.get("input_pins"),
            "generated_logic_contract_output_pins": generated_contract.get("output_pins"),
            "signal_binding_output_signal": signal_row.get("output_signal"),
        },
    }


def _build_artifact_contract() -> dict[str, Any]:
    rows = []
    for artifact_name, artifact_type, allowed_now, is_proof_result, notes in [
        (
            "delay_chain_testbench_template.sp",
            "spice_testbench_template",
            True,
            False,
            "Template only; may describe structure without authorizing simulation.",
        ),
        (
            "delay_chain_testbench_config.json",
            "testbench_config_json",
            True,
            False,
            "May hold symbolic corners/slews/loads with null values.",
        ),
        (
            "delay_chain_measurement_spec.json",
            "measurement_spec_json",
            True,
            False,
            "Measurement points may be defined before simulation.",
        ),
        (
            "delay_chain_corner_spec.json",
            "corner_spec_json",
            True,
            False,
            "Corner names may be reserved without numerical values.",
        ),
        (
            "delay_chain_plan.md",
            "README / md report",
            True,
            False,
            "Human-readable planning note is allowed.",
        ),
        (
            "delay_chain_measured_delay_result.json",
            "measured_delay_result",
            False,
            True,
            "Forbidden now because this step does not run simulation.",
        ),
        (
            "delay_chain_timing_closed_report.md",
            "timing_closed_report",
            False,
            True,
            "Forbidden now because no proof or closure may be claimed.",
        ),
        (
            "delay_chain_validated.lib",
            "validated_liberty",
            False,
            True,
            "Forbidden now because characterization has not been done.",
        ),
        (
            "delay_chain_extracted_rc.spef",
            "extracted_rc",
            False,
            True,
            "Forbidden now because physical extraction is out of scope.",
        ),
        (
            "delay_chain_route.gds",
            "physical_routing",
            False,
            True,
            "Forbidden now because no routing/GDS generation is authorized.",
        ),
        (
            "time_control_delay_chain.gds",
            "gds_layout",
            False,
            True,
            "Forbidden now because this is not a layout step.",
        ),
    ]:
        rows.append(
            {
                "artifact_name": artifact_name,
                "artifact_type": artifact_type,
                "allowed_now": allowed_now,
                "requires_model_before_use": artifact_type in {
                    "spice_testbench_template",
                    "testbench_config_json",
                    "measurement_spec_json",
                    "corner_spec_json",
                },
                "requires_user_approval_before_simulation": artifact_type in {
                    "spice_testbench_template",
                    "testbench_config_json",
                    "measurement_spec_json",
                    "corner_spec_json",
                },
                "is_proof_result": is_proof_result,
                "notes": notes,
            }
        )
    return {
        "future_artifacts": rows,
        "allowed_types_now": [
            "spice_testbench_template",
            "testbench_config_json",
            "measurement_spec_json",
            "corner_spec_json",
            "README / md report",
        ],
        "forbidden_types_now": [
            "measured_delay_result",
            "timing_closed_report",
            "validated_liberty",
            "extracted_rc",
            "physical_routing",
            "gds_layout",
        ],
    }


def _build_corner_plan() -> list[dict[str, Any]]:
    return [
        {
            "corner_name": "PVT_corner_definition",
            "process_corner": None,
            "voltage": None,
            "temperature": None,
            "voltage_known": False,
            "temperature_known": False,
            "source_of_corner": "required_by_timing_proof_plan_but_not_defined_yet",
            "requires_user_or_pdk_definition": True,
            "safe_to_use_for_planning": True,
        },
        {
            "corner_name": "replica_delay_margin_corner",
            "process_corner": None,
            "voltage": None,
            "temperature": None,
            "voltage_known": False,
            "temperature_known": False,
            "source_of_corner": "required_for_replica_path_calibration_but_not_defined_yet",
            "requires_user_or_pdk_definition": True,
            "safe_to_use_for_planning": True,
        },
    ]


def _build_measurement_plan() -> list[dict[str, Any]]:
    return [
        {
            "measurement_name": "chain_delay_rbl_to_rbl_delay",
            "from_node": "rbl",
            "to_node": "rbl_delay",
            "trigger": "input transition threshold crossing",
            "target": "output transition threshold crossing",
            "edge": "matching_edge_required_but_not_quantified",
            "threshold_policy": "requires_voltage_level_definition",
            "requires_voltage_level": True,
            "requires_simulation": True,
            "can_evaluate_now": False,
        },
        {
            "measurement_name": "input_slew_at_rbl",
            "from_node": "rbl",
            "to_node": "rbl",
            "trigger": "same_node_slew_measurement",
            "target": "same_node_slew_measurement",
            "edge": "input_edge_to_be_defined",
            "threshold_policy": "requires_voltage_level_definition",
            "requires_voltage_level": True,
            "requires_simulation": True,
            "can_evaluate_now": False,
        },
        {
            "measurement_name": "output_slew_at_rbl_delay",
            "from_node": "rbl_delay",
            "to_node": "rbl_delay",
            "trigger": "same_node_slew_measurement",
            "target": "same_node_slew_measurement",
            "edge": "output_edge_to_be_defined",
            "threshold_policy": "requires_voltage_level_definition",
            "requires_voltage_level": True,
            "requires_simulation": True,
            "can_evaluate_now": False,
        },
        {
            "measurement_name": "pulse_width_at_rbl_delay",
            "from_node": "rbl_delay",
            "to_node": "rbl_delay",
            "trigger": "first threshold crossing",
            "target": "return crossing on same node",
            "edge": "pulse_width_policy_to_be_defined",
            "threshold_policy": "requires_voltage_level_definition",
            "requires_voltage_level": True,
            "requires_simulation": True,
            "can_evaluate_now": False,
        },
    ]


def _build_model_dependencies(model_row: dict[str, Any], pdk_candidates: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "model_name": "gen_delay_inv",
            "needed_for": ["DELAY_CHAIN stage instantiation", "chain delay measurement"],
            "current_status": "recoverable_from_generator_source_but_missing_usable_spice",
            "source_candidate": _first_or_none(model_row.get("python_generator_paths", [])),
            "can_recover_from_generator": True,
            "can_use_now": False,
            "requires_manual_netlist_creation": True,
            "requires_characterization": True,
            "requires_pdk_device_model": True,
            "requires_validation": True,
            "blocker_level": "critical",
        },
        {
            "model_name": "gen_inv",
            "needed_for": ["four-load inverter stage model"],
            "current_status": "recoverable_from_generator_source_but_missing_usable_spice",
            "source_candidate": "openyield generator source or future recovered netlist",
            "can_recover_from_generator": True,
            "can_use_now": False,
            "requires_manual_netlist_creation": True,
            "requires_characterization": True,
            "requires_pdk_device_model": True,
            "requires_validation": True,
            "blocker_level": "high",
        },
        {
            "model_name": "PDK transistor models",
            "needed_for": ["leaf transistor simulation", "load inverter simulation"],
            "current_status": "path_not_proven_in_current_report_set",
            "source_candidate": _first_or_none(pdk_candidates),
            "can_recover_from_generator": False,
            "can_use_now": False,
            "requires_manual_netlist_creation": False,
            "requires_characterization": False,
            "requires_pdk_device_model": True,
            "requires_validation": True,
            "blocker_level": "critical",
        },
        {
            "model_name": "four-load inverter model",
            "needed_for": ["per-stage distributed load encoding"],
            "current_status": "count_known_value_unknown",
            "source_candidate": "future four_load_inverter_stage_model_plan",
            "can_recover_from_generator": True,
            "can_use_now": False,
            "requires_manual_netlist_creation": True,
            "requires_characterization": True,
            "requires_pdk_device_model": True,
            "requires_validation": True,
            "blocker_level": "high",
        },
        {
            "model_name": "replica bitline RC/load model",
            "needed_for": ["replica path calibration", "rbl to rbl_delay realism"],
            "current_status": "metadata_only_not_quantified",
            "source_candidate": "replica_cell_1rw.sp + future RC/load calibration plan",
            "can_recover_from_generator": False,
            "can_use_now": False,
            "requires_manual_netlist_creation": False,
            "requires_characterization": True,
            "requires_pdk_device_model": True,
            "requires_validation": True,
            "blocker_level": "critical",
        },
        {
            "model_name": "consumer pin load model",
            "needed_for": ["final stage output load policy"],
            "current_status": "consumer_list_known_but_load_value_unknown",
            "source_candidate": "Pinv.A / AND3.A / PNAND3.B metadata",
            "can_recover_from_generator": False,
            "can_use_now": False,
            "requires_manual_netlist_creation": False,
            "requires_characterization": True,
            "requires_pdk_device_model": False,
            "requires_validation": True,
            "blocker_level": "high",
        },
    ]


def _build_ranked_tasks() -> list[dict[str, Any]]:
    return [
        {
            "task_name": "gen_delay_inv_transistor_netlist_recovery_plan",
            "why_needed": "DELAY_CHAIN cannot instantiate a credible leaf without a recoverable transistor-level gen_delay_inv subckt.",
            "inputs": ["generated_logic_model_recovery_report", "OpenYield generator source", "gds pin metadata"],
            "outputs": ["recovery plan", "candidate subckt contract", "pin-order validation plan"],
            "can_do_readonly": True,
            "modifies_main_flow": False,
            "pass_criteria": "gen_delay_inv recovery path and pin contract are explicit and source-backed.",
            "fail_criteria": "leaf subckt contract remains ambiguous.",
            "unblocks": ["delay_chain_testbench_template_contract", "four_load_inverter_stage_model_plan"],
        },
        {
            "task_name": "four_load_inverter_stage_model_plan",
            "why_needed": "The source confirms four loads per stage, but not their quantified electrical model.",
            "inputs": ["gen_inv recovery evidence", "DELAY_CHAIN source metadata"],
            "outputs": ["load inverter model plan", "stage-load encoding policy"],
            "can_do_readonly": True,
            "modifies_main_flow": False,
            "pass_criteria": "four-load-per-stage symbolic structure and future model path are explicit.",
            "fail_criteria": "distributed load remains hand-wavy or untracked.",
            "unblocks": ["delay_chain_testbench_template_contract"],
        },
        {
            "task_name": "delay_chain_testbench_template_contract",
            "why_needed": "A template contract is needed before any future simulation request can be scoped safely.",
            "inputs": ["delay_chain_spice_testbench_plan", "gen_delay_inv recovery plan", "load model plan"],
            "outputs": ["spice_testbench_template contract", "config json schema", "measurement schema"],
            "can_do_readonly": True,
            "modifies_main_flow": False,
            "pass_criteria": "template fields, includes, probes, and forbidden claims are explicit.",
            "fail_criteria": "template boundary vs executable simulation remains blurred.",
            "unblocks": ["pvt_corner_definition_plan", "waveform_measurement_spec_plan"],
        },
        {
            "task_name": "pvt_corner_definition_plan",
            "why_needed": "No voltage/temperature/process values are currently authorized for execution.",
            "inputs": ["PDK model location", "timing proof plan corner names"],
            "outputs": ["corner_spec_json plan", "corner naming policy"],
            "can_do_readonly": True,
            "modifies_main_flow": False,
            "pass_criteria": "corner names, ownership, and missing-value boundary are explicit.",
            "fail_criteria": "corner values are guessed or left implicit.",
            "unblocks": ["can_run_testbench_now_future_gate"],
        },
        {
            "task_name": "replica_load_calibration_plan",
            "why_needed": "The DELAY_CHAIN role is replica-bitline delay generation, so isolated inverter timing is insufficient.",
            "inputs": ["replica_cell_1rw.sp", "timing metadata", "RBL_DELAY_PATH assumptions"],
            "outputs": ["replica RC/load calibration plan", "consumer load attachment plan"],
            "can_do_readonly": True,
            "modifies_main_flow": False,
            "pass_criteria": "replica path calibration inputs and acceptance boundary are explicit.",
            "fail_criteria": "chain timing is treated as proof without replica calibration.",
            "unblocks": ["can_claim_delay_proof_now_future_gate"],
        },
        {
            "task_name": "waveform_measurement_spec_plan",
            "why_needed": "Delay/slew/pulse width all require threshold policy and probe definitions before simulation.",
            "inputs": ["delay_chain_testbench_plan", "corner plan", "leaf model plan"],
            "outputs": ["measurement_spec_json", "threshold policy placeholder contract"],
            "can_do_readonly": True,
            "modifies_main_flow": False,
            "pass_criteria": "all measurement points and missing threshold dependencies are explicit.",
            "fail_criteria": "measurement semantics remain implicit.",
            "unblocks": ["future_delay_chain_simulation_request"],
        },
    ]


def _build_graph(report: dict[str, Any]) -> dict[str, Any]:
    nodes = [
        {"id": "delay_chain", "kind": "timing_object", "label": "DELAY_CHAIN"},
        {"id": "signal:rbl", "kind": "signal", "label": "rbl"},
        {"id": "signal:rbl_delay", "kind": "signal", "label": "rbl_delay"},
    ]
    edges = [
        {"from": "signal:rbl", "to": "delay_chain", "relation": "drives"},
        {"from": "delay_chain", "to": "signal:rbl_delay", "relation": "produces"},
    ]
    for row in report["per_stage_load_plan"]:
        stage_id = f"stage:{row['stage_index']}"
        nodes.append({"id": stage_id, "kind": "delay_stage", "label": f"stage_{row['stage_index']}"})
        edges.append({"from": "delay_chain", "to": stage_id, "relation": "contains"})
        edges.append({"from": stage_id, "to": "model:gen_delay_inv", "relation": "requires_model"})
    for model in report["model_dependency_table"]:
        model_id = f"model:{model['model_name']}"
        if not any(node["id"] == model_id for node in nodes):
            nodes.append({"id": model_id, "kind": "model_dependency", "label": model["model_name"]})
        edges.append({"from": "delay_chain", "to": model_id, "relation": "depends_on"})
    for idx, task in enumerate(report["ranked_next_tasks"], start=1):
        task_id = f"task:{idx}"
        nodes.append({"id": task_id, "kind": "next_task", "label": task["task_name"]})
        edges.append({"from": "delay_chain", "to": task_id, "relation": "next_task"})
    return {
        "scope": report["scope"],
        "nodes": nodes,
        "edges": edges,
        "summary": report["audit_summary"],
    }


def _find_timing_object(payload: dict[str, Any], name: str, table_key: str = "timing_object_table") -> dict[str, Any]:
    for row in payload.get(table_key, []):
        if row.get("timing_object") == name:
            return row
    return {}


def _find_model(payload: dict[str, Any], macro_name: str) -> dict[str, Any]:
    for key in ("p0_generated_logic_model_inventory", "secondary_macro_model_inventory", "hardmacro_model_inventory"):
        for row in payload.get(key, []):
            if row.get("macro_name") == macro_name:
                return row
    return {}


def _find_generated_logic_contract(payload: dict[str, Any], contract_name: str) -> dict[str, Any]:
    for row in payload.get("generated_logic_contract_list", []):
        if row.get("contract_name") == contract_name:
            return row
    return {}


def _find_signal_binding(payload: dict[str, Any], signal_name: str) -> dict[str, Any]:
    for row in payload.get("signal_binding_contracts", []):
        if row.get("signal_name") == signal_name:
            return row
    return {}


def _find_pdk_model_candidates(tech_dir: Path) -> list[str]:
    patterns = ("*.sp", "*.spi", "*.spice", "*.model", "*.lib", "*.scs")
    roots = [tech_dir / "models", tech_dir / "model", tech_dir / "tech"]
    matches: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for pattern in patterns:
            for path in root.rglob(pattern):
                if any(token in path.name.lower() for token in ("nmos", "pmos", "model", "tt", "ss", "ff", "fet", "bsim")):
                    matches.append(str(path.resolve()))
    return _dedupe(matches)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load_json(path)


def _resolve_path(root: Path, path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return (root / p).resolve()


def _coalesce(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _first_or_none(items: list[str] | None) -> str | None:
    if not items:
        return None
    return items[0]


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
