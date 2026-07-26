"""Readonly DELAY_CHAIN four-load inverter stage model planning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_four_load_inverter_stage_model_report(
    repo_root: str | Path,
    tech_dir: str | Path,
    gen_delay_inv_recovery_path: str | Path,
    delay_chain_plan_path: str | Path,
    leaf_inventory_path: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    tech = _resolve_path(root, tech_dir)
    recovery = _load_json(_resolve_path(root, gen_delay_inv_recovery_path))
    delay_plan = _load_json(_resolve_path(root, delay_chain_plan_path))
    leaf_inventory = _load_json(_resolve_path(root, leaf_inventory_path))

    time_generate = root.parents[1] / "third_party" / "OpenYield" / "sram_compiler" / "subcircuits" / "time_generate.py"
    standard_cell = root.parents[1] / "third_party" / "OpenYield" / "sram_compiler" / "subcircuits" / "standard_cell.py"
    time_lines = time_generate.read_text(encoding="utf-8").splitlines()
    std_lines = standard_cell.read_text(encoding="utf-8").splitlines()

    source_evidence = _build_source_evidence(time_generate, standard_cell, time_lines, std_lines)
    candidate_bindings = _build_candidate_bindings(recovery, leaf_inventory)
    stage_contracts = _build_stage_contracts()
    spice_template = _build_spice_template_implication(candidate_bindings[0], stage_contracts)
    artifact_contract = _build_artifact_contract()
    blockers = _build_blockers(recovery, delay_plan)
    next_task = "delay_chain_testbench_template_contract"

    summary = {
        "four_load_inverter_stage_model_plan_available": True,
        "source_four_load_pattern_found": True,
        "load_count_per_stage_confirmed": True,
        "all_stage_load_contracts_available": True,
        "load_inverter_binding_decision_available": True,
        "load_capacitance_quantified": False,
        "load_pin_order_validated_by_spice": False,
        "can_emit_symbolic_load_testbench_template_now": True,
        "can_run_delay_chain_testbench_now": False,
        "can_claim_delay_proof_now": False,
        "can_claim_timing_closure_now": False,
        "can_enter_delay_chain_testbench_template_contract": True,
        "can_enter_pvt_corner_definition_plan": True,
        "can_enter_replica_load_calibration_plan": True,
        "can_enter_wen_delay_chain_conditional_testbench_plan": True,
        "can_enter_physical_timing_closure_now": False,
        "can_enter_physical_routing_now": False,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    report = {
        "scope": "four_load_inverter_stage_model_plan",
        "repo_root": str(root),
        "tech_dir": str(tech),
        "input_reports_and_assets": {
            "gen_delay_inv_recovery": str(_resolve_path(root, gen_delay_inv_recovery_path)),
            "delay_chain_plan": str(_resolve_path(root, delay_chain_plan_path)),
            "leaf_inventory": str(_resolve_path(root, leaf_inventory_path)),
            "time_generate_source": str(time_generate),
            "standard_cell_source": str(standard_cell),
            "gen_delay_inv_gds": str(tech / "gds_lib" / "openram_replacements" / "gen_delay_inv.gds"),
            "gen_inv_gds": str(tech / "gds_lib" / "openram_replacements" / "gen_inv.gds"),
        },
        "audit_summary": summary,
        "source_evidence": source_evidence,
        "load_inverter_same_as_delay_stage_source": True,
        "load_count_source_confirmed": True,
        "load_capacitance_quantified": False,
        "four_load_count_known": True,
        "four_load_capacitance_value_known": False,
        "requires_characterization_or_cap_estimation": True,
        "load_inverter_same_as_delay_stage_source_decision": {
            "load_inverter_same_as_delay_stage_source": True,
            "load_count_source_confirmed": True,
            "load_capacitance_quantified": False,
            "reason": "DelayChain instantiates both dinv* and dload_* with the same self.inv.NAME leaf.",
        },
        "load_inverter_candidate_binding_comparison": candidate_bindings,
        "recommended_planning_binding": "same_source_Pinv_as_delay_stage",
        "fallback_planning_binding": "symbolic_inverter_load_only",
        "per_stage_load_model_contract": stage_contracts,
        "spice_template_implication": spice_template,
        "load_model_artifact_contract": artifact_contract,
        "blockers": blockers,
        "next_recommended_proof_task": next_task,
        "boundary_assertions": {
            "generator_source_is_not_validated_spice": True,
            "load_inverter_contract_is_not_characterization_result": True,
            "load_count_confirmation_is_not_load_capacitance_value": True,
            "symbolic_template != executable_simulation": True,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
    }
    graph = _build_graph(report)
    return {"report": report, "graph": graph}


def format_four_load_inverter_stage_model_markdown(report: dict[str, Any]) -> str:
    binding_rows = [
        [
            row["candidate_name"],
            row["same_as_delay_stage"],
            row["matches_source_instance_pattern"],
            row["has_validated_spice"],
            row["has_validated_load_cap"],
            row["recommended_for_planning"],
            row["recommended_for_simulation_now"],
            row["risk"],
        ]
        for row in report["load_inverter_candidate_binding_comparison"]
    ]
    stage_rows = [
        [
            row["stage_index"],
            row["driver_instance"],
            row["driver_input"],
            row["driver_output"],
            row["load_instance_count"],
            row["load_cell_candidate"],
            row["load_model_type"],
            row["safe_for_testbench_template"],
            row["safe_for_simulation_now"],
        ]
        for row in report["per_stage_load_model_contract"]
    ]
    artifact_rows = [
        [
            row["artifact_name"],
            row["artifact_type"],
            row["allowed_now"],
            row["requires_manual_review"],
            row["requires_pdk_binding"],
            row["requires_characterization"],
            row["is_validated_load_model"],
            row["is_timing_proof"],
        ]
        for row in report["load_model_artifact_contract"]["artifacts"]
    ]
    lines = [
        "# OpenYield Four-Load Inverter Stage Model Report",
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
        "## Source Evidence",
        "",
        "```json",
        json.dumps(report["source_evidence"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Load Inverter Candidate Binding Comparison",
        "",
        _md_table(
            ["candidate", "same source", "matches source pattern", "validated spice", "validated load cap", "planning", "simulate now", "risk"],
            binding_rows,
        ),
        "",
        "## Per-Stage Load Model Contract",
        "",
        _md_table(
            ["stage", "driver", "input", "output", "load count", "load candidate", "model type", "template safe", "simulate now"],
            stage_rows,
        ),
        "",
        "## SPICE Template Implication",
        "",
        "```json",
        json.dumps(report["spice_template_implication"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Load Model Artifact Contract",
        "",
        _md_table(
            ["artifact", "type", "allowed now", "manual review", "pdk binding", "characterization", "validated load model", "timing proof"],
            artifact_rows,
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


def _build_source_evidence(
    time_generate: Path,
    standard_cell: Path,
    time_lines: list[str],
    std_lines: list[str],
) -> dict[str, Any]:
    source_line_numbers = [
        299,
        306,
        321,
        333,
        336,
        337,
        341,
        343,
        347,
        348,
        352,
        355,
        356,
    ]
    return {
        "source_file": str(time_generate),
        "source_symbol_or_function": ["DelayChain.add_delay_chain", "Pinv"],
        "source_lines_if_available": source_line_numbers + [5, 10, 16, 24, 25, 26, 31, 33],
        "source_uses_same_inv_for_delay_and_load": True,
        "source_load_instance_pattern": "dload_<stage>_<slot> instances all use self.inv.NAME, same as dinv<stage>",
        "source_load_count_per_stage": 4,
        "source_load_stage_count": 9,
        "source_load_nodes": {
            "stage_0": {"driver_output": "dout_1", "load_outputs": [f"n_0_{i}" for i in range(4)]},
            "stage_1_to_7": "driver outputs dout_2..dout_8 each fan out to n_<stage>_0..3",
            "stage_8": {"driver_output": "out", "load_outputs": [f"n_8_{i}" for i in range(4)]},
        },
        "source_mentions_load_transistor_sizing": True,
        "source_mentions_load_pin_order": True,
        "source_mentions_load_power_pins": True,
        "source_evidence_strength": "high",
        "source_limitations": [
            "The source proves instance topology and shared leaf origin, but not a validated SPICE subckt file.",
            "The source proves Pinv node order (VDD, VSS, A, Z) for the Python generator leaf, not a validated exported .SUBCKT order for gen_delay_inv/gen_inv.",
            "The source does not quantify the effective input capacitance of each load inverter.",
        ],
        "supporting_source_blocks": {
            "delay_chain_block": _extract_block(time_lines, 299, 356),
            "pinv_block": _extract_block(std_lines, 5, 34),
        },
        "derived_conclusions": {
            "load_inverter_same_as_delay_stage_source": True,
            "load_count_source_confirmed": True,
            "load_capacitance_quantified": False,
            "four_load_count_known": True,
            "four_load_capacitance_value_known": False,
            "requires_characterization_or_cap_estimation": True,
        },
    }


def _build_candidate_bindings(recovery: dict[str, Any], leaf_inventory: dict[str, Any]) -> list[dict[str, Any]]:
    gen_delay_inv_leaf = _find_leaf(leaf_inventory, "gen_delay_inv", "openram_replacements")
    gen_inv_leaf = _find_leaf(leaf_inventory, "gen_inv", "openram_replacements")
    recovery_contract = recovery.get("candidate_subckt_contract", {})
    return [
        {
            "candidate_name": "same_source_Pinv_as_delay_stage",
            "source_basis": "DelayChain uses self.inv.NAME for both dinv* and dload_*; Pinv is the exact source leaf.",
            "gds_basis": "No direct GDS leaf named PINV1; planning-only binding stays at source-generator level.",
            "spice_basis": "standard_cell.py defines Pinv transistor topology with NODES=('VDD','VSS','A','Z'), but it is not validated SPICE in this step.",
            "pin_order_basis": ["VDD", "VSS", "A", "Z"],
            "same_as_delay_stage": True,
            "matches_source_instance_pattern": True,
            "has_validated_spice": False,
            "has_validated_load_cap": False,
            "requires_manual_netlist_materialization": True,
            "requires_characterization": True,
            "risk": "medium",
            "recommended_for_planning": True,
            "recommended_for_simulation_now": False,
            "notes": "Best source-faithful planning binding. Strong for topology, still non-runnable.",
        },
        {
            "candidate_name": "gen_delay_inv_candidate_subckt",
            "source_basis": "Previous recovery step can materialize a candidate gen_delay_inv contract from DelayChain source.",
            "gds_basis": gen_delay_inv_leaf.get("gds_path"),
            "spice_basis": "Candidate-only subckt contract from recovery report; not validated, not runnable now.",
            "pin_order_basis": recovery_contract.get("candidate_pin_order", ["A", "Z", "vdd", "gnd"]),
            "same_as_delay_stage": False,
            "matches_source_instance_pattern": False,
            "has_validated_spice": False,
            "has_validated_load_cap": False,
            "requires_manual_netlist_materialization": True,
            "requires_characterization": True,
            "risk": "medium",
            "recommended_for_planning": False,
            "recommended_for_simulation_now": False,
            "notes": "Useful canonical alias for future template packaging, but the source names Pinv rather than gen_delay_inv.",
        },
        {
            "candidate_name": "gen_inv_openram_replacement",
            "source_basis": "Leaf inventory shows gen_inv exists and is inverter-like, but DelayChain source never names gen_inv for dload_*.",
            "gds_basis": gen_inv_leaf.get("gds_path"),
            "spice_basis": "No validated gen_inv SPICE model is present in current planning inputs.",
            "pin_order_basis": ["A", "Z", "vdd", "gnd"],
            "same_as_delay_stage": False,
            "matches_source_instance_pattern": False,
            "has_validated_spice": False,
            "has_validated_load_cap": False,
            "requires_manual_netlist_materialization": True,
            "requires_characterization": True,
            "risk": "high",
            "recommended_for_planning": False,
            "recommended_for_simulation_now": False,
            "notes": "Do not bind directly now. Similar geometry/function is not enough to prove the load model.",
        },
        {
            "candidate_name": "symbolic_inverter_load_only",
            "source_basis": "Conservative abstraction: source proves four inverter loads per stage without proving numerical capacitance.",
            "gds_basis": "No physical leaf commitment required.",
            "spice_basis": "May be represented as placeholder inverter-load metadata only; not executable now.",
            "pin_order_basis": ["input=stage_output", "output=dummy_node", "supplies=power_aliases"],
            "same_as_delay_stage": False,
            "matches_source_instance_pattern": True,
            "has_validated_spice": False,
            "has_validated_load_cap": False,
            "requires_manual_netlist_materialization": False,
            "requires_characterization": True,
            "risk": "low",
            "recommended_for_planning": True,
            "recommended_for_simulation_now": False,
            "notes": "Best fallback when we need a testbench contract without overclaiming electrical values.",
        },
    ]


def _build_stage_contracts() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stage in range(9):
        if stage == 0:
            driver_input = "in"
            driver_output = "dout_1"
        elif stage == 8:
            driver_input = "dout_8"
            driver_output = "out"
        else:
            driver_input = f"dout_{stage}"
            driver_output = f"dout_{stage + 1}"
        rows.append(
            {
                "stage_index": stage,
                "driver_instance": f"dinv{stage}",
                "driver_input": driver_input,
                "driver_output": driver_output,
                "load_instance_count": 4,
                "load_instance_names": [f"dload_{stage}_{slot}" for slot in range(4)],
                "load_input_node": driver_output,
                "load_output_nodes": [f"n_{stage}_{slot}" for slot in range(4)],
                "load_cell_candidate": "same_source_Pinv_as_delay_stage",
                "load_cell_pin_order_candidate": ["VDD", "VSS", "A", "Z"],
                "load_cell_pin_order_validated_by_spice": False,
                "load_capacitance_value": None,
                "load_capacitance_known": False,
                "load_model_type": "four_parallel_inverter_gate_loads",
                "load_model_status": "source_confirmed_count_only_not_quantified",
                "requires_gen_delay_inv_model": True,
                "requires_load_inverter_model": True,
                "requires_pdk_device_model": True,
                "requires_characterization": True,
                "safe_for_testbench_template": True,
                "safe_for_simulation_now": False,
            }
        )
    return rows


def _build_spice_template_implication(
    recommended_binding: dict[str, Any],
    stage_contracts: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "template_load_strategy": "planning_only_four_parallel_inverter_loads_per_stage",
        "load_subckt_name_candidate": "PINV1",
        "load_pin_order_candidate": recommended_binding["pin_order_basis"],
        "load_connection_pattern": {
            "rule": "each load inverter input connects to the current stage output, each load inverter output connects to a unique dummy node",
            "stage_0_example": {
                "driver_output": stage_contracts[0]["driver_output"],
                "load_instances": [
                    {
                        "instance_name": name,
                        "input_node": stage_contracts[0]["load_input_node"],
                        "output_node": out,
                    }
                    for name, out in zip(stage_contracts[0]["load_instance_names"], stage_contracts[0]["load_output_nodes"])
                ],
            },
        },
        "load_output_treatment": "dummy load outputs must remain isolated metadata nodes and must not be treated as real signal path endpoints",
        "floating_load_outputs_allowed": True,
        "requires_dummy_output_load_handling": True,
        "requires_body_tie_policy": True,
        "requires_pdk_model_binding": True,
        "requires_validation_before_run": True,
        "can_emit_template_with_symbolic_loads": True,
        "can_run_template_now": False,
        "notes": [
            "The source proves stage fanout topology, not quantitative capacitance.",
            "A future template may normalize PINV1 into a canonical alias such as gen_delay_inv, but that alias is not validated now.",
            "Dummy load outputs are bookkeeping nodes only.",
        ],
    }


def _build_artifact_contract() -> dict[str, Any]:
    artifacts = [
        {
            "artifact_name": "four_load_inverter_stage_contract.json",
            "artifact_type": "planning_contract_json",
            "allowed_now": True,
            "requires_manual_review": True,
            "requires_pdk_binding": False,
            "requires_characterization": False,
            "is_validated_load_model": False,
            "is_timing_proof": False,
            "notes": "Allowed now as planning-only load contract.",
        },
        {
            "artifact_name": "delay_chain_load_model_notes.md",
            "artifact_type": "planning_notes_markdown",
            "allowed_now": True,
            "requires_manual_review": False,
            "requires_pdk_binding": False,
            "requires_characterization": False,
            "is_validated_load_model": False,
            "is_timing_proof": False,
            "notes": "Allowed now as human-readable explanation.",
        },
        {
            "artifact_name": "delay_chain_symbolic_load_template.sp",
            "artifact_type": "symbolic_spice_template",
            "allowed_now": True,
            "requires_manual_review": True,
            "requires_pdk_binding": True,
            "requires_characterization": True,
            "is_validated_load_model": False,
            "is_timing_proof": False,
            "notes": "Allowed only as a non-runnable or clearly non-validated template.",
        },
        {
            "artifact_name": "validated_four_load_model.sp",
            "artifact_type": "validated_spice_model",
            "allowed_now": False,
            "requires_manual_review": True,
            "requires_pdk_binding": True,
            "requires_characterization": True,
            "is_validated_load_model": True,
            "is_timing_proof": False,
            "notes": "Forbidden now.",
        },
        {
            "artifact_name": "load_capacitance_extracted.json",
            "artifact_type": "quantified_load_extract",
            "allowed_now": False,
            "requires_manual_review": True,
            "requires_pdk_binding": True,
            "requires_characterization": True,
            "is_validated_load_model": True,
            "is_timing_proof": False,
            "notes": "Forbidden now because capacitance is not characterized.",
        },
        {
            "artifact_name": "measured_delay_result.json",
            "artifact_type": "measurement_result",
            "allowed_now": False,
            "requires_manual_review": True,
            "requires_pdk_binding": True,
            "requires_characterization": True,
            "is_validated_load_model": False,
            "is_timing_proof": True,
            "notes": "Forbidden now because no SPICE run is authorized.",
        },
        {
            "artifact_name": "timing_closed_report.md",
            "artifact_type": "timing_closure_claim",
            "allowed_now": False,
            "requires_manual_review": True,
            "requires_pdk_binding": True,
            "requires_characterization": True,
            "is_validated_load_model": False,
            "is_timing_proof": True,
            "notes": "Forbidden now because no delay proof or closure may be claimed.",
        },
    ]
    return {"artifacts": artifacts}


def _build_blockers(recovery: dict[str, Any], delay_plan: dict[str, Any]) -> list[str]:
    return _dedupe(
        [
            "The four-load count is source-confirmed, but the effective load capacitance per inverter is not quantified.",
            "No validated SPICE pin order exists for gen_delay_inv or gen_inv in the current input set.",
            "No PDK transistor model include path is bound for executable simulation.",
            "A future load template still needs manual netlist materialization and characterization.",
            "Replica bitline calibration remains required before any delay proof.",
        ]
        + list(recovery.get("blockers", []))
        + list(delay_plan.get("blockers", []))
    )


def _build_graph(report: dict[str, Any]) -> dict[str, Any]:
    nodes = [
        {"id": "source:DelayChain", "kind": "source", "label": "DelayChain"},
        {"id": "source:Pinv", "kind": "source", "label": "Pinv"},
        {"id": "binding:recommended", "kind": "decision", "label": report["recommended_planning_binding"]},
    ]
    edges = [
        {"from": "source:DelayChain", "to": "source:Pinv", "relation": "instantiates"},
        {"from": "source:Pinv", "to": "binding:recommended", "relation": "supports"},
    ]
    for candidate in report["load_inverter_candidate_binding_comparison"]:
        node_id = f"candidate:{candidate['candidate_name']}"
        nodes.append({"id": node_id, "kind": "binding_candidate", "label": candidate["candidate_name"]})
        edges.append({"from": "source:DelayChain", "to": node_id, "relation": "candidate_binding"})
        if candidate["recommended_for_planning"]:
            edges.append({"from": node_id, "to": "binding:recommended", "relation": "recommended_path"})
    for row in report["per_stage_load_model_contract"]:
        stage_id = f"stage:{row['stage_index']}"
        nodes.append({"id": stage_id, "kind": "delay_stage", "label": row["driver_instance"]})
        edges.append({"from": "source:DelayChain", "to": stage_id, "relation": "contains"})
        for load_name in row["load_instance_names"]:
            load_id = f"load:{load_name}"
            nodes.append({"id": load_id, "kind": "load_instance", "label": load_name})
            edges.append({"from": stage_id, "to": load_id, "relation": "fans_out_to"})
    return {
        "scope": report["scope"],
        "nodes": nodes,
        "edges": edges,
        "summary": report["audit_summary"],
    }


def _find_leaf(payload: dict[str, Any], macro_name: str, variant_name: str) -> dict[str, Any]:
    for row in payload.get("leaf_gds_bbox_pin_side_inventory", []):
        if row.get("macro_name") == macro_name and row.get("variant_name") == variant_name:
            return row
    return {}


def _extract_block(lines: list[str], start_1: int, end_1: int) -> list[dict[str, Any]]:
    rows = []
    for line_no in range(start_1, min(end_1, len(lines)) + 1):
        rows.append({"line": line_no, "text": lines[line_no - 1].rstrip()})
    return rows


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
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out
