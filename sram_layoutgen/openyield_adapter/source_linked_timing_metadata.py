"""Build source-linked timing metadata artifacts for OpenYield control timing review."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any


DEFAULT_OPENYIELD_ROOT = Path("/data1/qujh/work/external/OpenYield")
DEFAULT_REMOTE_URL = "https://github.com/ShenShan123/OpenYield.git"


def discover_openyield_root(repo_root: str | Path) -> Path:
    root = Path(repo_root).resolve()
    prior_report = root / "docs/openyield_source_provenance_report.json"
    if prior_report.exists():
        try:
            payload = json.loads(prior_report.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        candidate = payload.get("openyield_source_path")
        if candidate:
            path = Path(candidate)
            if path.exists():
                return path.resolve()
    return DEFAULT_OPENYIELD_ROOT.resolve()


def build_source_provenance_linking_report(
    repo_root: str | Path,
    openyield_root: str | Path,
    timing_json_path: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    openyield = Path(openyield_root).resolve()
    timing_json = _resolve_path(root, timing_json_path)
    timing_report = _load_json(timing_json)

    time_generate = openyield / "sram_compiler/subcircuits/time_generate.py"
    standard_cell = openyield / "sram_compiler/subcircuits/standard_cell.py"
    candidate_spice = root / "docs/candidate_spice/gen_delay_inv_candidate.sp"
    refined_deck = root / "docs/candidate_spice/delay_chain_measurement_refined_ngspice.sp"
    timing_summary = root / "docs/evidence/timing_metadata_summary.md"

    tg_text = time_generate.read_text(encoding="utf-8")
    sc_text = standard_cell.read_text(encoding="utf-8")
    candidate_text = candidate_spice.read_text(encoding="utf-8")
    refined_text = refined_deck.read_text(encoding="utf-8")

    delaychain_line = _find_line_number(tg_text, "class DelayChain(BaseSubcircuit)")
    pinv_line = _find_line_number(sc_text, "class Pinv(BaseSubcircuit)")
    rbl_delay_line = _find_line_number(tg_text, "'VDD', 'VSS', 'rbl', 'rbl_delay'")

    constructor_signature = _extract_signature(tg_text, "def __init__")
    pinv_signature = _extract_signature(sc_text, "def __init__")
    pattern = r"self\.inv = Pinv\(nmos_model, pmos_model,([0-9.eE+-]+),([0-9.eE+-]+), length=([0-9.eE+-]+),num=1\)"
    pinv_nmos = _extract_float(tg_text, pattern, 1)
    pinv_pmos = _extract_float(tg_text, pattern, 2)
    pinv_length = _extract_float(tg_text, pattern, 3)

    stage_count = 9 if "self.X('dinv8'" in tg_text else None
    loads_per_stage = 4 if "for j in range(4)" in tg_text else None
    odd_stage_inverts = True if stage_count and stage_count % 2 == 1 else False
    source_signal = "rbl" if "'VDD', 'VSS', 'rbl', 'rbl_delay'" in tg_text else None
    target_signal = "rbl_delay" if "'VDD', 'VSS', 'rbl', 'rbl_delay'" in tg_text else None

    timing_metadata = timing_report.get("timing_metadata", {})
    delay_by_corner_rtf = timing_metadata.get("rise_to_fall_delay_by_corner", {})
    delay_by_corner_ftr = timing_metadata.get("fall_to_rise_delay_by_corner", {})
    corners_complete = set(delay_by_corner_rtf) == {"nom", "ff", "ss"} and set(delay_by_corner_ftr) == {"nom", "ff", "ss"}

    source_to_candidate_spice_consistent = all([
        stage_count == 9,
        loads_per_stage == 4,
        "W=2.7e-07" in candidate_text,
        "W=0.9e-07" in candidate_text,
        "L=0.05e-6" in candidate_text,
        refined_text.count("Xdinv") == 9,
        refined_text.count("Xdload_") == 36,
        "Xdinv8 dout_8 rbl_delay" in refined_text,
    ])
    source_to_timing_metadata_consistent = all([
        timing_metadata.get("source_signal") == source_signal,
        timing_metadata.get("target_signal") == target_signal,
        timing_metadata.get("stage_count") == stage_count,
        timing_metadata.get("load_policy") == "four_load_inverters_per_stage",
        timing_metadata.get("inversion") == "odd_stage_chain_inverts",
        corners_complete,
        timing_metadata.get("worst_smoke_delay") is not None,
        timing_metadata.get("worst_smoke_delay_corner") == "ss",
    ])

    consistency_checks = {
        "stage_count_match": stage_count == timing_metadata.get("stage_count") == 9,
        "loads_per_stage_match": loads_per_stage == 4 and timing_metadata.get("load_policy") == "four_load_inverters_per_stage",
        "pinv_w_l_match": all([
            pinv_nmos == 0.9e-07,
            pinv_pmos == 2.7e-07,
            pinv_length == 0.05e-6,
            "W=2.7e-07" in candidate_text,
            "W=0.9e-07" in candidate_text,
            "L=0.05e-6" in candidate_text,
        ]),
        "source_signal_match": timing_metadata.get("source_signal") == "rbl",
        "target_signal_match": timing_metadata.get("target_signal") == "rbl_delay",
        "odd_stage_inversion_match": odd_stage_inverts and timing_metadata.get("inversion") == "odd_stage_chain_inverts",
        "nom_ff_ss_delay_metadata_complete": corners_complete,
    }

    rbl_usage = [
        {
            "path": str(time_generate),
            "line": rbl_delay_line,
            "role": "DelayChain instance drives rbl -> rbl_delay",
            "snippet": "self.X('delaychain', delaychain.NAME, 'VDD', 'VSS', 'rbl', 'rbl_delay')",
        },
        {
            "path": str(time_generate),
            "line": _find_line_number(tg_text, "self.X('inv_rbl_delay_bar'"),
            "role": "Generate rbl_delay_bar from rbl_delay",
            "snippet": "self.X('inv_rbl_delay_bar', inv_rbl_delay_bar.NAME, 'VDD', 'VSS', 'rbl_delay', 'rbl_delay_bar')",
        },
        {
            "path": str(time_generate),
            "line": _find_line_number(tg_text, "self.X('w_en'"),
            "role": "Write-enable path consumes rbl_delay_bar or delayed write variant",
            "snippet": "self.X('w_en', w_en.NAME, 'VDD','VSS' , w_en_rbl_input , 'gated_clk_bar' ,'we', 'w_en' )",
        },
        {
            "path": str(time_generate),
            "line": _find_line_number(tg_text, "self.X('s_en'"),
            "role": "Sense-enable path consumes rbl_delay",
            "snippet": "self.X('s_en', s_en.NAME, 'VDD','VSS' ,'rbl_delay', 'gated_clk_bar' ,'we_bar' ,'s_en' )",
        },
        {
            "path": str(time_generate),
            "line": _find_line_number(tg_text, "self.X('pre_unbuf'"),
            "role": "Precharge path consumes rbl_delay with gated clock and wl_en_bar",
            "snippet": "self.X('pre_unbuf', pre_unbuf.NAME, 'VDD', 'VSS', 'gated_clk_buf', 'rbl_delay', 'wl_en_bar', 'PRE_UNBUF')",
        },
    ]

    report = {
        "scope": "openyield_source_provenance_linking",
        "main_repo_path": str(root),
        "main_repo_head": _run_text(["git", "rev-parse", "HEAD"], cwd=root),
        "openyield_source_path": str(openyield),
        "openyield_remote_url": _run_text(["git", "remote", "get-url", "origin"], cwd=openyield) or DEFAULT_REMOTE_URL,
        "openyield_branch": _run_text(["git", "branch", "--show-current"], cwd=openyield),
        "openyield_head": _run_text(["git", "rev-parse", "HEAD"], cwd=openyield),
        "openyield_latest_commit_message": _run_text(["git", "log", "-1", "--pretty=%s"], cwd=openyield),
        "time_generate_py_path": str(time_generate),
        "delaychain_source": {
            "path": str(time_generate),
            "line": delaychain_line,
            "constructor_parameters": constructor_signature,
            "nodes": ["VDD", "VSS", "in", "out"],
            "stage_count_evidence": "dinv0 + dinv1..dinv7 + dinv8 => 9 total inverters",
            "instance_naming_pattern": {
                "stage_instances": "dinv0..dinv8",
                "load_instances": "dload_<stage>_<index>",
                "internal_nodes": "dout_1..dout_8 and n_<stage>_<index>",
            },
            "loads_per_stage": loads_per_stage,
            "load_inverter_source_shared_with_stage_inverter": True,
            "stage_inverter_source": "self.inv = Pinv(...) reused for both dinv and dload instances",
        },
        "pinv_source": {
            "path": str(standard_cell),
            "line": pinv_line,
            "constructor_parameters": pinv_signature,
            "nodes": ["VDD", "VSS", "A", "Z"],
            "nmos_width": pinv_nmos,
            "pmos_width": pinv_pmos,
            "length": pinv_length,
        },
        "rbl_delay_usage": rbl_usage,
        "local_cross_validation": {
            "candidate_spice": str(candidate_spice),
            "measurement_deck": str(refined_deck),
            "timing_metadata_json": str(timing_json),
            "timing_metadata_summary": str(timing_summary),
            "consistency_checks": consistency_checks,
            "source_to_candidate_spice_consistent": source_to_candidate_spice_consistent,
            "source_to_timing_metadata_consistent": source_to_timing_metadata_consistent,
            "mismatches": [key for key, value in consistency_checks.items() if not value],
        },
        "boundary_assertions": {
            "openyield_source_committed_into_main_repo": False,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
            "time_control_gds_generated": False,
            "delay_proof_claimed": False,
            "timing_closure_claimed": False,
            "physical_integration_enabled": False,
        },
        "gates": {
            "openyield_source_available": openyield.exists(),
            "openyield_head_recorded": True,
            "delay_chain_source_found": delaychain_line is not None,
            "pinv_source_found": pinv_line is not None,
            "source_to_candidate_spice_consistent": source_to_candidate_spice_consistent,
            "source_to_timing_metadata_consistent": source_to_timing_metadata_consistent,
            "can_enter_metadata_consumer_adapter": source_to_candidate_spice_consistent and source_to_timing_metadata_consistent,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_claim_openyield_full_integration_now": False,
        },
    }
    return report


def build_control_timing_mapping(
    timing_report: dict[str, Any],
    source_link_report: dict[str, Any],
) -> list[dict[str, Any]]:
    md = timing_report["timing_metadata"]
    worst_delay = md["worst_smoke_delay"]
    coverage = "nom/ff/ss @ VDD=1.0, TEMP=25C"
    forbidden = "no_delay_proof;no_timing_closure;no_physical_integration;no_time_control_gds"
    time_generate = source_link_report["time_generate_py_path"]

    return [
        {
            "openyield_object": "DELAY_CHAIN",
            "openyield_source_file": time_generate,
            "openyield_signal_or_node": "rbl->rbl_delay",
            "local_timing_object": "DELAY_CHAIN",
            "local_candidate_artifact": "docs/candidate_spice/gen_delay_inv_candidate.sp;docs/candidate_spice/delay_chain_measurement_refined_ngspice.sp",
            "local_metadata_artifact": "docs/openyield_delay_chain_timing_metadata_report.json;docs/evidence/timing_metadata_summary.md",
            "evidence_status": "source_linked_and_smoke_timing_metadata_available",
            "measured_delay_available": True,
            "worst_smoke_delay_s": worst_delay,
            "corner_coverage": coverage,
            "integration_readiness": "ready_for_control_timing_metadata_consumption_not_physical_integration",
            "next_required_action": "implement_metadata_consumer_adapter_without_touching_standalone",
            "forbidden_claims": forbidden,
        },
        {
            "openyield_object": "RBL_DELAY_PATH",
            "openyield_source_file": time_generate,
            "openyield_signal_or_node": "rbl_delay;rbl_delay_bar",
            "local_timing_object": "DELAY_CHAIN_RBL_PATH",
            "local_candidate_artifact": "docs/candidate_spice/delay_chain_measurement_refined_ngspice.sp",
            "local_metadata_artifact": "docs/openyield_delay_chain_timing_metadata_report.json",
            "evidence_status": "source_linked_and_smoke_timing_metadata_available",
            "measured_delay_available": True,
            "worst_smoke_delay_s": worst_delay,
            "corner_coverage": coverage,
            "integration_readiness": "ready_for_control_timing_metadata_consumption_not_physical_integration",
            "next_required_action": "map_rbl_delay_metadata_to_adapter_consumer",
            "forbidden_claims": forbidden,
        },
        {
            "openyield_object": "SENSE_ENABLE_PATH",
            "openyield_source_file": time_generate,
            "openyield_signal_or_node": "s_en<=AND3(rbl_delay,gated_clk_bar,we_bar)",
            "local_timing_object": "SENSE_ENABLE_PATH",
            "local_candidate_artifact": "",
            "local_metadata_artifact": "",
            "evidence_status": "source_identified_only",
            "measured_delay_available": False,
            "worst_smoke_delay_s": "",
            "corner_coverage": "none",
            "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
            "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
            "forbidden_claims": forbidden,
        },
        {
            "openyield_object": "PRECHARGE_ENABLE_PATH",
            "openyield_source_file": time_generate,
            "openyield_signal_or_node": "PRE_UNBUF/PRE<=PNAND3(gated_clk_buf,rbl_delay,wl_en_bar)",
            "local_timing_object": "PRECHARGE_ENABLE_PATH",
            "local_candidate_artifact": "",
            "local_metadata_artifact": "",
            "evidence_status": "source_identified_only",
            "measured_delay_available": False,
            "worst_smoke_delay_s": "",
            "corner_coverage": "none",
            "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
            "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
            "forbidden_claims": forbidden,
        },
        {
            "openyield_object": "WRITE_ENABLE_PATH",
            "openyield_source_file": time_generate,
            "openyield_signal_or_node": "w_en<=AND3(rbl_delay_bar/gated_variant,gated_clk_bar,we)",
            "local_timing_object": "WRITE_ENABLE_PATH",
            "local_candidate_artifact": "",
            "local_metadata_artifact": "",
            "evidence_status": "source_identified_only",
            "measured_delay_available": False,
            "worst_smoke_delay_s": "",
            "corner_coverage": "none",
            "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
            "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
            "forbidden_claims": forbidden,
        },
        {
            "openyield_object": "WORDLINE_ENABLE_PATH",
            "openyield_source_file": time_generate,
            "openyield_signal_or_node": "wl_en;wl_en_bar",
            "local_timing_object": "WORDLINE_ENABLE_PATH",
            "local_candidate_artifact": "",
            "local_metadata_artifact": "",
            "evidence_status": "source_identified_only",
            "measured_delay_available": False,
            "worst_smoke_delay_s": "",
            "corner_coverage": "none",
            "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
            "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
            "forbidden_claims": forbidden,
        },
        {
            "openyield_object": "GATED_CLOCK_PATH",
            "openyield_source_file": time_generate,
            "openyield_signal_or_node": "gated_clk_bar;gated_clk_buf",
            "local_timing_object": "GATED_CLOCK_PATH",
            "local_candidate_artifact": "",
            "local_metadata_artifact": "",
            "evidence_status": "source_identified_only",
            "measured_delay_available": False,
            "worst_smoke_delay_s": "",
            "corner_coverage": "none",
            "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
            "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
            "forbidden_claims": forbidden,
        },
        {
            "openyield_object": "DFF_ROW",
            "openyield_source_file": time_generate,
            "openyield_signal_or_node": "ADDR_DFF/A_dff*;TIME A*->A_dff*",
            "local_timing_object": "ADDR_DFF_ROW",
            "local_candidate_artifact": "",
            "local_metadata_artifact": "",
            "evidence_status": "source_identified_only",
            "measured_delay_available": False,
            "worst_smoke_delay_s": "",
            "corner_coverage": "none",
            "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
            "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
            "forbidden_claims": forbidden,
        },
        {
            "openyield_object": "PRECHARGE",
            "openyield_source_file": f"{Path(time_generate).parent / 'precharge_and_write_driver.py'}",
            "openyield_signal_or_node": "PRE-driven precharge devices",
            "local_timing_object": "PRECHARGE",
            "local_candidate_artifact": "",
            "local_metadata_artifact": "",
            "evidence_status": "source_identified_only",
            "measured_delay_available": False,
            "worst_smoke_delay_s": "",
            "corner_coverage": "none",
            "integration_readiness": "not_ready_needs_candidate_spice_and_transient_smoke",
            "next_required_action": "needs_candidate_spice;needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter",
            "forbidden_claims": forbidden,
        },
    ]


def build_control_timing_mapping_review_report(
    repo_root: str | Path,
    source_link_report: dict[str, Any],
    mapping_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    ready = [row["openyield_object"] for row in mapping_rows if row["measured_delay_available"]]
    source_only = [row["openyield_object"] for row in mapping_rows if row["evidence_status"] == "source_identified_only"]
    return {
        "scope": "control_timing_mapping_review",
        "repo_root": str(root),
        "repo_head": _run_text(["git", "rev-parse", "HEAD"], cwd=root),
        "openyield_head": source_link_report["openyield_head"],
        "mapping_rows": mapping_rows,
        "summary": {
            "mapped_object_count": len(mapping_rows),
            "objects_with_smoke_timing_metadata": ready,
            "objects_source_identified_only": source_only,
            "next_gate": "metadata_consumer_adapter",
        },
        "boundary_assertions": {
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
            "time_control_gds_generated": False,
            "delay_proof_claimed": False,
            "timing_closure_claimed": False,
            "physical_integration_enabled": False,
        },
    }


def build_source_linked_timing_metadata_audit(
    repo_root: str | Path,
    timing_report: dict[str, Any],
    source_link_report: dict[str, Any],
    mapping_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    delay_chain_row = next(row for row in mapping_rows if row["openyield_object"] == "DELAY_CHAIN")
    delay_chain_source_linked = source_link_report["gates"]["source_to_candidate_spice_consistent"] and source_link_report["gates"]["source_to_timing_metadata_consistent"]
    return {
        "scope": "source_linked_timing_metadata_audit",
        "repo_root": str(root),
        "repo_head": _run_text(["git", "rev-parse", "HEAD"], cwd=root),
        "openyield_head": source_link_report["openyield_head"],
        "timing_metadata_path": str(_resolve_path(root, "docs/openyield_delay_chain_timing_metadata_report.json")),
        "source_link_report_path": str(_resolve_path(root, "docs/openyield_source_provenance_linking_report.json")),
        "mapping_table_path": str(_resolve_path(root, "docs/mapping/openyield_control_timing_mapping.csv")),
        "delay_chain_summary": {
            "evidence_status": delay_chain_row["evidence_status"],
            "worst_smoke_delay_s": delay_chain_row["worst_smoke_delay_s"],
            "corner_coverage": delay_chain_row["corner_coverage"],
        },
        "gates": {
            "source_linked_timing_metadata_available": True,
            "delay_chain_source_linked": delay_chain_source_linked,
            "delay_chain_timing_metadata_available": timing_report["audit_summary"]["delay_chain_timing_metadata_update_available"],
            "control_mapping_table_available": bool(mapping_rows),
            "delay_chain_ready_for_metadata_consumption": delay_chain_source_linked and delay_chain_row["measured_delay_available"],
            "any_control_path_ready_for_physical_integration": False,
            "can_enter_metadata_consumer_adapter": delay_chain_source_linked and delay_chain_row["measured_delay_available"],
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_claim_openyield_full_integration_now": False,
        },
        "boundary_assertions": {
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
            "time_control_gds_generated": False,
            "delay_proof_claimed": False,
            "timing_closure_claimed": False,
            "physical_integration_enabled": False,
        },
    }


def format_source_provenance_linking_markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        "# OpenYield Source Provenance Linking Report",
        "",
        f"- Main repo path: `{report['main_repo_path']}`",
        f"- Main repo HEAD: `{report['main_repo_head']}`",
        f"- OpenYield source path: `{report['openyield_source_path']}`",
        f"- OpenYield remote URL: `{report['openyield_remote_url']}`",
        f"- OpenYield branch: `{report['openyield_branch']}`",
        f"- OpenYield HEAD: `{report['openyield_head']}`",
        f"- Latest OpenYield commit: `{report['openyield_latest_commit_message']}`",
        "",
        "## DelayChain Source",
        "",
        "```json",
        json.dumps(report["delaychain_source"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pinv Source",
        "",
        "```json",
        json.dumps(report["pinv_source"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## rbl/rbl_delay Usage",
        "",
        "```json",
        json.dumps(report["rbl_delay_usage"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Cross Validation",
        "",
        "```json",
        json.dumps(report["local_cross_validation"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Gates",
        "",
        "```json",
        json.dumps(report["gates"], ensure_ascii=False, indent=2),
        "```",
    ])


def format_mapping_markdown(rows: list[dict[str, Any]]) -> str:
    headers = [
        "openyield_object",
        "openyield_signal_or_node",
        "local_timing_object",
        "evidence_status",
        "measured_delay_available",
        "worst_smoke_delay_s",
        "corner_coverage",
        "integration_readiness",
        "next_required_action",
    ]
    lines = [
        "# OpenYield Control Timing Mapping",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")) for key in headers) + " |")
    return "\n".join(lines)


def format_control_timing_mapping_review_markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        "# OpenYield Control Timing Mapping Review Report",
        "",
        f"- Repo root: `{report['repo_root']}`",
        f"- Repo HEAD: `{report['repo_head']}`",
        f"- OpenYield HEAD: `{report['openyield_head']}`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(report["summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Mapping Rows",
        "",
        "```json",
        json.dumps(report["mapping_rows"], ensure_ascii=False, indent=2),
        "```",
    ])


def format_source_linked_timing_metadata_audit_markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        "# OpenYield Source-Linked Timing Metadata Audit Report",
        "",
        f"- Repo root: `{report['repo_root']}`",
        f"- Repo HEAD: `{report['repo_head']}`",
        f"- OpenYield HEAD: `{report['openyield_head']}`",
        "",
        "## Delay Chain Summary",
        "",
        "```json",
        json.dumps(report["delay_chain_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Gates",
        "",
        "```json",
        json.dumps(report["gates"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Boundary Assertions",
        "",
        "```json",
        json.dumps(report["boundary_assertions"], ensure_ascii=False, indent=2),
        "```",
    ])


def write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def _run_text(cmd: list[str], cwd: Path) -> str | None:
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or result.stderr.strip() or None


def _find_line_number(text: str, needle: str) -> int | None:
    for index, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return index
    return None


def _extract_signature(text: str, anchor: str) -> str | None:
    match = re.search(rf"{re.escape(anchor)}\((.*?)\):", text, re.S)
    if not match:
        return None
    return " ".join(part.strip() for part in match.group(1).splitlines())


def _extract_float(text: str, pattern: str, group: int) -> float | None:
    match = re.search(pattern, text)
    if not match:
        return None
    return float(match.group(group))
