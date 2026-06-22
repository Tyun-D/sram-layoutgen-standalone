"""Readonly gen_delay_inv transistor netlist recovery planning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


KEYWORDS = [
    "gen_delay_inv",
    "delay_inv",
    "DelayChain",
    "DELAY_CHAIN",
    "inverter",
    "inv",
    "load inverter",
    "four load",
    "subckt",
    "pmos",
    "nmos",
    "width",
    "length",
    "drive",
    "stage",
]


def build_gen_delay_inv_netlist_recovery_report(
    repo_root: str | Path,
    tech_dir: str | Path,
    delay_chain_plan_path: str | Path,
    model_recovery_path: str | Path,
    leaf_inventory_path: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    tech = _resolve_path(root, tech_dir)
    delay_chain_plan = _load_json(_resolve_path(root, delay_chain_plan_path))
    model_recovery = _load_json(_resolve_path(root, model_recovery_path))
    leaf_inventory = _load_json(_resolve_path(root, leaf_inventory_path))

    source_file = root.parents[1] / "third_party" / "OpenYield" / "sram_compiler" / "subcircuits" / "time_generate.py"
    source_lines = source_file.read_text(encoding="utf-8").splitlines()
    source_evidence = _build_source_evidence(source_file, source_lines)

    model_row = _find_model(model_recovery, "gen_delay_inv")
    recommended_leaf = _find_leaf(leaf_inventory, "gen_delay_inv", "openram_replacements")
    fallback_leaf = _find_leaf(leaf_inventory, "gen_delay_inv", "default_gds_lib")
    gds_evidence = _build_gds_evidence(recommended_leaf, fallback_leaf)

    candidate_subckt_contract = _build_candidate_subckt_contract()
    recovery_requirements = _build_recovery_requirements(source_evidence)
    artifact_contract = _build_artifact_contract()
    decision = _build_recovery_decision()

    blockers = _dedupe(
        [
            "No existing validated SPICE subckt for gen_delay_inv was found.",
            "GDS pin labels provide candidate logical pins only, not validated SPICE pin order.",
            "Transistor sizing is source-visible in DelayChain construction, but Pinv internal implementation still needs manual recovery review.",
            "PDK model include path is not bound in current plan.",
            "Body connection policy is not proven from current source/GDS evidence alone.",
            "No characterization or simulation has been run.",
        ]
        + model_recovery.get("blockers", [])
        + delay_chain_plan.get("blockers", [])
    )

    audit_summary = {
        "gen_delay_inv_transistor_netlist_recovery_plan_available": True,
        "source_evidence_found": True,
        "gds_pin_evidence_found": True,
        "candidate_subckt_contract_available": True,
        "candidate_pin_order_available": True,
        "candidate_pin_order_validated_by_spice": False,
        "transistor_sizing_known": False,
        "pdk_device_model_bound": False,
        "can_emit_candidate_subckt_template_now": True,
        "can_emit_validated_spice_now": False,
        "can_enter_four_load_inverter_stage_model_plan": True,
        "can_enter_delay_chain_testbench_template_contract": True,
        "can_run_delay_chain_testbench_now": False,
        "can_claim_delay_proof_now": False,
        "can_claim_timing_closure_now": False,
        "can_enter_physical_timing_closure_now": False,
        "can_enter_physical_routing_now": False,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    report = {
        "scope": "gen_delay_inv_transistor_netlist_recovery_plan",
        "repo_root": str(root),
        "tech_dir": str(tech),
        "input_reports_and_assets": {
            "delay_chain_plan": str(_resolve_path(root, delay_chain_plan_path)),
            "model_recovery": str(_resolve_path(root, model_recovery_path)),
            "leaf_inventory": str(_resolve_path(root, leaf_inventory_path)),
            "source_file": str(source_file),
            "recommended_gds": str(tech / "gds_lib" / "openram_replacements" / "gen_delay_inv.gds"),
            "default_gds": str(tech / "gds_lib" / "gen_delay_inv.gds"),
        },
        "audit_summary": audit_summary,
        "source_evidence": source_evidence,
        "gds_leaf_evidence": gds_evidence,
        "candidate_subckt_contract": candidate_subckt_contract,
        "transistor_level_recovery_requirements": recovery_requirements,
        "recovery_decision": decision,
        "future_artifact_contract": artifact_contract,
        "blockers": blockers,
        "next_recommended_proof_task": "four_load_inverter_stage_model_plan",
        "boundary_assertions": {
            "generator_source_is_not_validated_spice": True,
            "gds_pin_order_is_not_validated_spice_pin_order": True,
            "candidate_subckt_contract_is_not_validated_model": True,
            "recovery_plan_is_not_characterization_result": True,
            "recovery_plan_is_not_timing_proof": True,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
        "fallback_sources": {
            "delay_chain_plan_source_used": delay_chain_plan.get("scope"),
            "model_recovery_source_used": model_recovery.get("scope"),
            "leaf_inventory_source_used": leaf_inventory.get("scope"),
            "filesystem_source_scan_used": True,
            "markdown_fallback_used": False,
        },
    }
    graph = _build_graph(report)
    return {"report": report, "graph": graph}


def format_gen_delay_inv_netlist_recovery_markdown(report: dict[str, Any]) -> str:
    artifact_rows = [
        [
            row["artifact_name"],
            row["artifact_type"],
            row["allowed_now"],
            row["requires_manual_review"],
            row["requires_pdk_model_binding"],
            row["requires_characterization"],
            row["is_validated_model"],
            row["is_timing_proof"],
        ]
        for row in report["future_artifact_contract"]["artifacts"]
    ]
    req_rows = [[k, v["value_known"], v["source"], v["requires_manual_or_pdk_definition"]] for k, v in report["transistor_level_recovery_requirements"].items()]

    lines = [
        "# OpenYield gen_delay_inv Netlist Recovery Plan",
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
        "## GDS / Leaf Evidence",
        "",
        "```json",
        json.dumps(report["gds_leaf_evidence"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Candidate Subckt Contract",
        "",
        "```json",
        json.dumps(report["candidate_subckt_contract"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Transistor-Level Recovery Requirements",
        "",
        _md_table(["field", "value_known", "source", "requires_manual_or_pdk_definition"], req_rows),
        "",
        "## Recovery Decision",
        "",
        "```json",
        json.dumps(report["recovery_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Future Artifact Contract",
        "",
        _md_table(
            ["artifact", "type", "allowed_now", "manual_review", "pdk_binding", "characterization", "validated", "timing_proof"],
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


def _build_source_evidence(source_file: Path, source_lines: list[str]) -> dict[str, Any]:
    matched = []
    for idx, line in enumerate(source_lines, start=1):
        low = line.lower()
        if any(keyword.lower() in low for keyword in KEYWORDS):
            if "DelayChain" in line or "Pinv" in line or "loads_per_stage" in line or "nmos_model" in line or "pmos_model" in line:
                matched.append({"line": idx, "text": line.rstrip()})
    matched = matched[:40]
    block = _extract_block(source_lines, 298, 345)
    return {
        "source_file": str(source_file),
        "source_symbol_or_function": ["DelayChain", "Pinv"],
        "source_lines_if_available": [item["line"] for item in matched],
        "source_role": "DelayChain source constructs gen_delay_inv-equivalent inverter chain and load topology.",
        "source_mentions_delay_chain": True,
        "source_mentions_gen_delay_inv": False,
        "source_mentions_four_load_inverters": True,
        "source_mentions_transistor_sizing": True,
        "source_mentions_pin_order": True,
        "source_mentions_power_pins": True,
        "source_evidence_strength": "medium",
        "source_limitations": [
            "Source defines DelayChain behavior and Pinv instantiation, but does not directly emit a validated gen_delay_inv subckt file.",
            "Source-visible node order uses VDD/VSS/in/out at DelayChain level, not necessarily final leaf subckt pin order.",
            "Pinv internal implementation is imported from standard_cell.py and is not validated here as a finished SPICE leaf.",
        ],
        "transistor_sizing_source_confirmed": False,
        "requires_manual_sizing_recovery": True,
        "highlight_block": block,
    }


def _build_gds_evidence(recommended_leaf: dict[str, Any], fallback_leaf: dict[str, Any]) -> dict[str, Any]:
    return {
        "macro_name": "gen_delay_inv",
        "recommended_gds_variant": recommended_leaf.get("variant_name"),
        "gds_path": recommended_leaf.get("gds_path"),
        "bbox": recommended_leaf.get("bbox"),
        "pin_labels": recommended_leaf.get("pin_labels"),
        "input_pins": recommended_leaf.get("input_pins"),
        "output_pins": recommended_leaf.get("output_pins"),
        "vdd_pins": recommended_leaf.get("vdd_pins"),
        "gnd_pins": recommended_leaf.get("gnd_pins"),
        "pin_side_map": recommended_leaf.get("pin_side_map"),
        "candidate_pin_order": ["A", "Z", "vdd", "gnd"],
        "candidate_pin_order_source": "openram_replacements GDS pin labels plus prior delay-chain planning contract",
        "candidate_pin_order_validated_by_spice": False,
        "power_side_policy": recommended_leaf.get("vdd_gnd_policy"),
        "rail_evidence_status": recommended_leaf.get("rail_evidence_status"),
        "safe_for_netlist_contract_planning": True,
        "safe_for_validated_spice_generation": False,
        "fallback_variant_comparison": {
            "variant_name": fallback_leaf.get("variant_name"),
            "gds_path": fallback_leaf.get("gds_path"),
            "pin_labels": fallback_leaf.get("pin_labels"),
            "recommended_for_future_planning": fallback_leaf.get("recommended_for_future_planning"),
        },
        "notes": [
            "Recommended variant is openram_replacements because it has explicit A/Z/vdd/gnd label evidence.",
            "Default gds_lib variant lacks useful pin label evidence for contract planning.",
            "candidate_pin_order_validated_by_spice=False",
            "safe_for_validated_spice_generation=False",
        ],
    }


def _build_candidate_subckt_contract() -> dict[str, Any]:
    return {
        "subckt_name": "gen_delay_inv",
        "candidate_pin_order": ["A", "Z", "vdd", "gnd"],
        "logical_function": "inverter / delay inverter",
        "expected_polarity": "inverting",
        "input_pin": "A",
        "output_pin": "Z",
        "power_pins": ["vdd", "gnd"],
        "requires_pdk_device_models": True,
        "requires_transistor_sizing": True,
        "requires_body_connection_policy": True,
        "requires_load_stage_context": True,
        "requires_characterization": True,
        "usable_for_testbench_template": True,
        "usable_for_spice_simulation_now": False,
        "usable_for_timing_proof_now": False,
    }


def _unknown_field(source: str | None = None) -> dict[str, Any]:
    return {
        "value_known": False,
        "source": source,
        "requires_manual_or_pdk_definition": True,
    }


def _build_recovery_requirements(source_evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "required_device_models": {
            "value_known": False,
            "source": "time_generate.py names NMOS_VTG / PMOS_VTG but no include path is bound",
            "requires_manual_or_pdk_definition": True,
        },
        "required_pmos_model_name": {
            "value_known": True,
            "source": "time_generate.py default parameter pmos_model=\"PMOS_VTG\"",
            "requires_manual_or_pdk_definition": True,
        },
        "required_nmos_model_name": {
            "value_known": True,
            "source": "time_generate.py default parameter nmos_model=\"NMOS_VTG\"",
            "requires_manual_or_pdk_definition": True,
        },
        "required_channel_length": {
            "value_known": True,
            "source": "time_generate.py DelayChain uses length=0.05e-6 and Pinv(... length=0.05e-6 ...)",
            "requires_manual_or_pdk_definition": True,
        },
        "required_pmos_width": {
            "value_known": True,
            "source": "time_generate.py DelayChain instantiates Pinv(... pmos_width=2.7e-07 ...)",
            "requires_manual_or_pdk_definition": True,
        },
        "required_nmos_width": {
            "value_known": True,
            "source": "time_generate.py DelayChain instantiates Pinv(... nmos_width=0.9e-07 ...)",
            "requires_manual_or_pdk_definition": True,
        },
        "required_finger_count": _unknown_field(None),
        "required_body_tie_policy": _unknown_field("not proven by current source/GDS evidence"),
        "required_supply_naming_policy": {
            "value_known": True,
            "source": "DelayChain source uses VDD/VSS; GDS planning contract uses vdd/gnd alias pair",
            "requires_manual_or_pdk_definition": True,
        },
        "required_pin_order_policy": {
            "value_known": True,
            "source": "candidate contract only: [A, Z, vdd, gnd]",
            "requires_manual_or_pdk_definition": True,
        },
        "required_subckt_naming_policy": {
            "value_known": True,
            "source": "candidate name fixed to gen_delay_inv for planning compatibility",
            "requires_manual_or_pdk_definition": True,
        },
        "required_instance_naming_policy": _unknown_field("future candidate template only"),
        "required_load_inverter_context": {
            "value_known": True,
            "source": "DelayChain add_delay_chain() adds four same-leaf loads per stage",
            "requires_manual_or_pdk_definition": True,
        },
        "required_validation_steps": {
            "value_known": True,
            "source": "recovery plan defines future validation path, not executed now",
            "requires_manual_or_pdk_definition": True,
        },
    }


def _build_recovery_decision() -> dict[str, Any]:
    return {
        "recovery_decision": "recoverable_from_generator_source_but_requires_manual_netlist_materialization",
        "can_emit_candidate_subckt_template_now": True,
        "can_emit_validated_spice_now": False,
        "can_enter_four_load_inverter_stage_model_plan": True,
        "can_enter_delay_chain_testbench_template_contract": True,
        "can_run_delay_chain_testbench_now": False,
        "can_claim_delay_proof_now": False,
    }


def _build_artifact_contract() -> dict[str, Any]:
    rows = [
        {
            "artifact_name": "gen_delay_inv_candidate_subckt_template.sp",
            "artifact_type": "candidate_subckt_template",
            "allowed_now": True,
            "requires_manual_review": True,
            "requires_pdk_model_binding": True,
            "requires_characterization": True,
            "is_validated_model": False,
            "is_timing_proof": False,
            "notes": "Allowed as template only; must not be labeled validated.",
        },
        {
            "artifact_name": "gen_delay_inv_subckt_contract.json",
            "artifact_type": "subckt_contract_json",
            "allowed_now": True,
            "requires_manual_review": True,
            "requires_pdk_model_binding": False,
            "requires_characterization": False,
            "is_validated_model": False,
            "is_timing_proof": False,
            "notes": "Allowed now as planning contract.",
        },
        {
            "artifact_name": "gen_delay_inv_recovery_notes.md",
            "artifact_type": "recovery_notes",
            "allowed_now": True,
            "requires_manual_review": False,
            "requires_pdk_model_binding": False,
            "requires_characterization": False,
            "is_validated_model": False,
            "is_timing_proof": False,
            "notes": "Allowed now as human-readable recovery notes.",
        },
        {
            "artifact_name": "gen_delay_inv_validated.sp",
            "artifact_type": "validated_spice",
            "allowed_now": False,
            "requires_manual_review": True,
            "requires_pdk_model_binding": True,
            "requires_characterization": True,
            "is_validated_model": True,
            "is_timing_proof": False,
            "notes": "Forbidden now.",
        },
        {
            "artifact_name": "gen_delay_inv.lib",
            "artifact_type": "validated_liberty",
            "allowed_now": False,
            "requires_manual_review": True,
            "requires_pdk_model_binding": True,
            "requires_characterization": True,
            "is_validated_model": True,
            "is_timing_proof": False,
            "notes": "Forbidden now.",
        },
        {
            "artifact_name": "measured_delay_result.json",
            "artifact_type": "measured_delay_result",
            "allowed_now": False,
            "requires_manual_review": True,
            "requires_pdk_model_binding": True,
            "requires_characterization": True,
            "is_validated_model": False,
            "is_timing_proof": True,
            "notes": "Forbidden now because no simulation runs in this step.",
        },
        {
            "artifact_name": "timing_closed_report.md",
            "artifact_type": "timing_closed_report",
            "allowed_now": False,
            "requires_manual_review": True,
            "requires_pdk_model_binding": True,
            "requires_characterization": True,
            "is_validated_model": False,
            "is_timing_proof": True,
            "notes": "Forbidden now because no timing closure may be claimed.",
        },
    ]
    return {"artifacts": rows}


def _build_graph(report: dict[str, Any]) -> dict[str, Any]:
    nodes = [
        {"id": "source:time_generate.py", "kind": "source", "label": "time_generate.py"},
        {"id": "leaf:gen_delay_inv", "kind": "macro", "label": "gen_delay_inv"},
        {"id": "contract:gen_delay_inv", "kind": "subckt_contract", "label": "candidate_subckt_contract"},
    ]
    edges = [
        {"from": "source:time_generate.py", "to": "leaf:gen_delay_inv", "relation": "evidence_for"},
        {"from": "leaf:gen_delay_inv", "to": "contract:gen_delay_inv", "relation": "contracts_as"},
    ]
    for idx, item in enumerate(report["future_artifact_contract"]["artifacts"], start=1):
        node_id = f"artifact:{idx}"
        nodes.append({"id": node_id, "kind": "future_artifact", "label": item["artifact_name"]})
        edges.append({"from": "contract:gen_delay_inv", "to": node_id, "relation": "future_artifact"})
    return {"scope": report["scope"], "nodes": nodes, "edges": edges, "summary": report["audit_summary"]}


def _extract_block(lines: list[str], start_1: int, end_1: int) -> list[dict[str, Any]]:
    out = []
    for lineno in range(start_1, min(end_1, len(lines)) + 1):
        out.append({"line": lineno, "text": lines[lineno - 1].rstrip()})
    return out


def _find_model(payload: dict[str, Any], macro_name: str) -> dict[str, Any]:
    for key in ("p0_generated_logic_model_inventory", "secondary_macro_model_inventory", "hardmacro_model_inventory"):
        for row in payload.get(key, []):
            if row.get("macro_name") == macro_name:
                return row
    return {}


def _find_leaf(payload: dict[str, Any], macro_name: str, variant_name: str) -> dict[str, Any]:
    for row in payload.get("leaf_gds_bbox_pin_side_inventory", []):
        if row.get("macro_name") == macro_name and row.get("variant_name") == variant_name:
            return row
    return {}


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
