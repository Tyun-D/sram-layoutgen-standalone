"""Candidate SPICE static syntax checks and simulator binding audit."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


HEADER_LINES = [
    "* CANDIDATE / PLANNING-ONLY",
    "* NOT VALIDATED SPICE",
    "* NOT TIMING PROOF",
    "* DO NOT CLAIM TIMING CLOSURE",
    "* REQUIRES MANUAL REVIEW, PDK MODEL BINDING, AND CHARACTERIZATION",
]


def build_candidate_spice_syntax_check_report(
    repo_root: str | Path,
    candidate_dir: str | Path,
    openram_tech_dir: str | Path,
    pdk_model_dir: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    candidate = _resolve_path(root, candidate_dir)
    openram_tech = Path(openram_tech_dir).resolve()
    pdk_models = Path(pdk_model_dir).resolve()

    simulator_detection = _detect_simulators()
    selected = _select_simulator(simulator_detection)
    pdk_binding = _build_pdk_binding(openram_tech, pdk_models, candidate)
    local_include = _emit_local_model_include(candidate, pdk_binding)
    static_check = _static_spice_checks(candidate, pdk_binding, local_include)
    syntax_smoke = _attempt_syntax_smoke(candidate, selected, local_include)

    audit_summary = {
        "candidate_spice_syntax_check_available": True,
        "simulator_found": selected["found"],
        "selected_simulator": selected["simulator_name"],
        "pdk_include_binding_available": pdk_binding["hspice_include_resolves"] and pdk_binding["direct_model_includes_resolve"],
        "local_model_include_emitted": local_include.exists(),
        "static_spice_check_pass": static_check["static_spice_check_pass"],
        "syntax_smoke_attempted": syntax_smoke["syntax_smoke_attempted"],
        "syntax_smoke_pass": syntax_smoke["syntax_smoke_pass"],
        "can_run_candidate_spice_now": selected["found"] and (syntax_smoke["syntax_smoke_pass"] or not syntax_smoke["syntax_smoke_attempted"]),
        "can_run_delay_chain_testbench_now": False,
        "can_claim_delay_proof_now": False,
        "can_claim_timing_closure_now": False,
        "needs_user_simulator_install": not selected["found"],
        "needs_user_vdd_corner_threshold": True,
        "needs_teacher_or_project_provider": False,
        "can_enter_pvt_corner_definition_plan": True,
        "can_enter_delay_chain_smoke_simulation": selected["found"] and (syntax_smoke["syntax_smoke_pass"] or not syntax_smoke["syntax_smoke_attempted"]),
        "can_enter_physical_timing_closure_now": False,
        "can_enter_physical_routing_now": False,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    report = {
        "scope": "candidate_spice_syntax_check_and_simulator_binding",
        "repo_root": str(root),
        "candidate_dir": str(candidate),
        "openram_tech_dir": str(openram_tech),
        "pdk_model_dir": str(pdk_models),
        "audit_summary": audit_summary,
        "simulator_detection": simulator_detection,
        "selected_simulator": selected,
        "pdk_include_binding": pdk_binding,
        "local_model_include": {
            "path": str(local_include),
            "exists": local_include.exists(),
        },
        "static_spice_check": static_check,
        "syntax_smoke_result": syntax_smoke,
        "what_codex_can_fix": [
            "Emit a local direct-model include file for TT/nominal binding",
            "Check candidate SPICE structure, pin order, stage count, load count, and placeholder policy",
            "Prepare a simulator-specific syntax smoke deck when a simulator becomes available",
        ],
        "what_needs_user_or_teacher": [
            "Install or provide a simulator in PATH if smoke parse is required now",
            "Confirm project simulator choice",
            "Provide formal VDD, PVT corner, and threshold policy before any real simulation",
        ],
        "next_recommended_task": "install_or_bind_simulator_then_define_vdd_corner_threshold",
        "boundary_assertions": {
            "static_check_is_not_timing_proof": True,
            "syntax_smoke_is_not_delay_proof": True,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
    }
    graph = _build_graph(report)
    return {"report": report, "graph": graph}


def format_candidate_spice_syntax_check_markdown(report: dict[str, Any]) -> str:
    sim_rows = [
        [
            row["simulator_name"],
            row["found"],
            row["version_if_available"],
            row["path"],
            row["usable_for_hspice_include_syntax"],
            row["usable_for_basic_spice_parse"],
            row["license_or_runtime_issue_if_any"],
            row["recommended_for_next_step"],
        ]
        for row in report["simulator_detection"]
    ]
    issues = report["static_spice_check"]["issues"] + report["syntax_smoke_result"].get("issues", [])
    lines = [
        "# OpenYield Candidate SPICE Syntax Check Report",
        "",
        f"- Scope: `{report['scope']}`",
        f"- Candidate dir: `{report['candidate_dir']}`",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Simulator Detection",
        "",
        _md_table(
            ["simulator", "found", "version", "path", "hspice include syntax", "basic parse", "issue", "recommended"],
            sim_rows,
        ),
        "",
        "## PDK Include Binding",
        "",
        "```json",
        json.dumps(report["pdk_include_binding"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Static SPICE Check",
        "",
        "```json",
        json.dumps(report["static_spice_check"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Optional Syntax Smoke",
        "",
        "```json",
        json.dumps(report["syntax_smoke_result"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Issues",
        "",
        _list_block(issues),
        "",
        "## What Codex Can Fix",
        "",
        _list_block(report["what_codex_can_fix"]),
        "",
        "## What Needs User / Teacher",
        "",
        _list_block(report["what_needs_user_or_teacher"]),
        "",
        "## Boundary Assertions",
        "",
        "```json",
        json.dumps(report["boundary_assertions"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Next Recommended Task",
        "",
        f"- `{report['next_recommended_task']}`",
    ]
    return "\n".join(lines)


def _detect_simulators() -> list[dict[str, Any]]:
    rows = []
    specs = [
        ("hspice", ["hspice", "-v"], True, True),
        ("ngspice", ["ngspice", "-v"], False, True),
        ("spectre", ["spectre", "-W"], False, True),
    ]
    for name, version_cmd, hspice_ok, parse_ok in specs:
        path = shutil.which(name)
        found = path is not None
        version = None
        issue = None
        if found:
            try:
                result = subprocess.run(version_cmd, capture_output=True, text=True, timeout=10, check=False)
                version = (result.stdout or result.stderr).strip().splitlines()[0] if (result.stdout or result.stderr).strip() else "available"
                if result.returncode not in (0, 1):
                    issue = f"unexpected_returncode_{result.returncode}"
            except Exception as exc:  # noqa: BLE001
                issue = str(exc)
        else:
            issue = "not_found_in_PATH"
        rows.append(
            {
                "simulator_name": name,
                "found": found,
                "version_if_available": version,
                "path": path,
                "usable_for_hspice_include_syntax": found and hspice_ok,
                "usable_for_basic_spice_parse": found and parse_ok,
                "license_or_runtime_issue_if_any": issue,
                "recommended_for_next_step": found and (name == "hspice"),
            }
        )
    return rows


def _select_simulator(rows: list[dict[str, Any]]) -> dict[str, Any]:
    for preferred in ("hspice", "ngspice", "spectre"):
        for row in rows:
            if row["simulator_name"] == preferred and row["found"]:
                return row
    return {
        "simulator_name": None,
        "found": False,
        "version_if_available": None,
        "path": None,
        "usable_for_hspice_include_syntax": False,
        "usable_for_basic_spice_parse": False,
        "license_or_runtime_issue_if_any": "no_supported_simulator_found",
        "recommended_for_next_step": False,
    }


def _build_pdk_binding(openram_tech: Path, pdk_models: Path, candidate: Path) -> dict[str, Any]:
    pdk_dir_required = str(pdk_models)
    pdk_dir_candidate = str(pdk_models)
    pdk_env = os.environ.get("PDK_DIR")
    hspice_nom = pdk_models / "hspice_nom.include"
    direct_pmos = pdk_models / "tran_models" / "models_nom" / "PMOS_VTG.inc"
    direct_nmos = pdk_models / "tran_models" / "models_nom" / "NMOS_VTG.inc"
    return {
        "pdk_dir_required": pdk_dir_required,
        "pdk_dir_candidate": pdk_dir_candidate,
        "pdk_dir_env_already_set": pdk_env,
        "pdk_dir_env_needed": pdk_env != pdk_dir_candidate,
        "hspice_include_resolves": hspice_nom.exists(),
        "direct_model_includes_resolve": direct_pmos.exists() and direct_nmos.exists(),
        "hspice_nom_include": str(hspice_nom),
        "direct_nominal_model_includes": [str(direct_pmos), str(direct_nmos)],
        "candidate_local_include_target": str(candidate / "local_model_include_nom.inc"),
        "notes": [
            "The HSPICE include file uses $PDK_DIR/ncsu_basekit/... syntax and may require a tool-specific environment mapping.",
            "Direct .inc binding to nominal PMOS_VTG/NMOS_VTG is available and is safer for a local candidate smoke include.",
        ],
    }


def _emit_local_model_include(candidate: Path, pdk_binding: dict[str, Any]) -> Path:
    out = candidate / "local_model_include_nom.inc"
    lines = [
        "* CANDIDATE LOCAL INCLUDE / NOT A MODEL",
        f'.inc "{Path(pdk_binding["direct_nominal_model_includes"][0]).as_posix()}"',
        f'.inc "{Path(pdk_binding["direct_nominal_model_includes"][1]).as_posix()}"',
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return out


def _static_spice_checks(candidate: Path, pdk_binding: dict[str, Any], local_include: Path) -> dict[str, Any]:
    issues: list[str] = []
    gen_delay = (candidate / "gen_delay_inv_candidate.sp").read_text(encoding="utf-8")
    tb = (candidate / "delay_chain_symbolic_tb.sp").read_text(encoding="utf-8")
    measure = (candidate / "delay_chain_measure.inc").read_text(encoding="utf-8")
    corner = (candidate / "delay_chain_corner_placeholder.inc").read_text(encoding="utf-8")
    readme = (candidate / "README.md").read_text(encoding="utf-8")

    subckt_check = ".SUBCKT gen_delay_inv A Z vdd gnd" in gen_delay and ".ENDS gen_delay_inv" in gen_delay
    if not subckt_check:
        issues.append("gen_delay_inv_candidate.sp missing expected .SUBCKT/.ENDS pair")

    model_name_check = all(token in gen_delay for token in ["PMOS_VTG", "NMOS_VTG", "M_P Z A vdd vdd", "M_N Z A gnd gnd"])
    if not model_name_check:
        issues.append("gen_delay_inv_candidate.sp missing expected transistor model names or body/source wiring")

    include_paths = re.findall(r'^\.include "([^"]+)"', tb, flags=re.MULTILINE) + re.findall(r'^\.include "([^"]+)"', corner, flags=re.MULTILINE)
    include_path_check = True
    for include in include_paths:
        if include.endswith(".sp") or include.endswith(".inc") or include.endswith(".include"):
            include_file = Path(include)
            if not include_file.is_absolute():
                include_file = candidate / include
            if not include_file.exists():
                include_path_check = False
                issues.append(f"include path does not exist: {include}")
    stage_count = len(re.findall(r"^Xdinv\d+", tb, flags=re.MULTILINE))
    stage_count_check = stage_count == 9
    if not stage_count_check:
        issues.append(f"expected 9 delay stages, found {stage_count}")

    four_load_instances = re.findall(r"^Xdload_(\d+)_(\d+)\b", tb, flags=re.MULTILINE)
    four_load_check = len(four_load_instances) == 36 and all(sum(1 for s, _ in four_load_instances if int(s) == stage) == 4 for stage in range(9))
    if not four_load_check:
        issues.append("expected four load inverters per stage")

    dummy_nodes = re.findall(r"Xdload_\d+_\d+\s+\S+\s+(n_\d+_\d+)\s+vdd gnd gen_delay_inv", tb)
    dummy_node_check = len(dummy_nodes) == len(set(dummy_nodes)) == 36
    if not dummy_node_check:
        issues.append("dummy load output nodes are not unique")

    measure_placeholder_check = "__TBD_" in measure and "planning-only" in measure.lower() and "__TBD_" in tb
    if not measure_placeholder_check:
        issues.append("measure/template placeholders are incomplete")

    boundary_text_check = all(line in gen_delay for line in HEADER_LINES) and all(line in tb for line in HEADER_LINES) and all(
        phrase.lower() not in (gen_delay + tb + measure + corner + readme).lower()
        for phrase in ["validated timing proof", "timing closure achieved"]
    )
    if not boundary_text_check:
        issues.append("boundary warning text missing or misleading claim found")

    static_pass = all(
        [
            subckt_check,
            model_name_check,
            include_path_check,
            stage_count_check,
            four_load_check,
            dummy_node_check,
            measure_placeholder_check,
            boundary_text_check,
        ]
    )
    return {
        "static_spice_check_pass": static_pass,
        "subckt_check_pass": subckt_check,
        "model_name_check_pass": model_name_check,
        "include_path_check_pass": include_path_check,
        "stage_count_check_pass": stage_count_check,
        "four_load_check_pass": four_load_check,
        "dummy_node_check_pass": dummy_node_check,
        "measure_placeholder_check_pass": measure_placeholder_check,
        "boundary_text_check_pass": boundary_text_check,
        "issues": issues,
        "local_model_include_path": str(local_include),
        "candidate_files_checked": [
            str(candidate / "gen_delay_inv_candidate.sp"),
            str(candidate / "delay_chain_symbolic_tb.sp"),
            str(candidate / "delay_chain_measure.inc"),
            str(candidate / "delay_chain_corner_placeholder.inc"),
            str(candidate / "README.md"),
        ],
    }


def _attempt_syntax_smoke(candidate: Path, selected: dict[str, Any], local_include: Path) -> dict[str, Any]:
    smoke_file = candidate / "delay_chain_syntax_smoke.sp"
    log_path = None
    if not selected["found"]:
        smoke_file.write_text(_smoke_text(local_include), encoding="utf-8", newline="\n")
        return {
            "syntax_smoke_attempted": False,
            "syntax_smoke_pass": False,
            "simulator_used": None,
            "smoke_file": str(smoke_file),
            "log_path": None,
            "issues": ["No simulator found in PATH; syntax smoke not attempted."],
        }

    smoke_file.write_text(_smoke_text(local_include), encoding="utf-8", newline="\n")
    sim = selected["simulator_name"]
    if sim == "hspice":
        log_path = candidate / "delay_chain_syntax_smoke.hspice.log"
        cmd = [selected["path"], str(smoke_file)]
    elif sim == "ngspice":
        log_path = candidate / "delay_chain_syntax_smoke.ngspice.log"
        cmd = [selected["path"], "-b", str(smoke_file), "-o", str(log_path)]
    elif sim == "spectre":
        log_path = candidate / "delay_chain_syntax_smoke.spectre.log"
        cmd = [selected["path"], str(smoke_file)]
    else:
        return {
            "syntax_smoke_attempted": False,
            "syntax_smoke_pass": False,
            "simulator_used": None,
            "smoke_file": str(smoke_file),
            "log_path": None,
            "issues": ["No supported simulator selected."],
        }
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
        combined = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
        if log_path and sim != "ngspice":
            log_path.write_text(combined, encoding="utf-8", newline="\n")
        syntax_pass = result.returncode == 0
        issues = []
        if not syntax_pass:
            issues.append((combined.strip().splitlines() or [f"{sim} returned {result.returncode}"])[0])
        return {
            "syntax_smoke_attempted": True,
            "syntax_smoke_pass": syntax_pass,
            "simulator_used": sim,
            "smoke_file": str(smoke_file),
            "log_path": str(log_path) if log_path else None,
            "returncode": result.returncode,
            "issues": issues,
        }
    except Exception as exc:  # noqa: BLE001
        if log_path:
            log_path.write_text(str(exc), encoding="utf-8", newline="\n")
        return {
            "syntax_smoke_attempted": True,
            "syntax_smoke_pass": False,
            "simulator_used": sim,
            "smoke_file": str(smoke_file),
            "log_path": str(log_path) if log_path else None,
            "issues": [str(exc)],
        }


def _smoke_text(local_include: Path) -> str:
    return "\n".join(
        HEADER_LINES
        + [
            "* Syntax smoke only. Temporary VDD/TEMP are for parse/elaboration checks, not project signoff.",
            f'.include "{local_include.as_posix()}"',
            '.include "gen_delay_inv_candidate.sp"',
            '.include "delay_chain_measure.inc"',
            ".param VDD_VALUE=1.0",
            ".param TEMP_VALUE=25",
            ".param RBL_INPUT_SLEW=1n",
            ".temp 25",
            "VDD_SRC vdd 0 1.0",
            "VIN rbl 0 PULSE(0 1.0 0 10p 10p 200p 400p)",
            "Xdinv0 rbl dout_1 vdd 0 gen_delay_inv",
            "Xdload_0_0 dout_1 n_0_0 vdd 0 gen_delay_inv",
            ".tran 1p 2n",
            ".end",
            "",
        ]
    )


def _build_graph(report: dict[str, Any]) -> dict[str, Any]:
    nodes = [
        {"id": "candidate:gen_delay_inv", "kind": "candidate_spice", "label": "gen_delay_inv_candidate.sp"},
        {"id": "candidate:tb", "kind": "candidate_tb", "label": "delay_chain_symbolic_tb.sp"},
        {"id": "include:local_nom", "kind": "include", "label": "local_model_include_nom.inc"},
        {"id": "sim:selected", "kind": "simulator", "label": str(report["audit_summary"]["selected_simulator"])},
    ]
    edges = [
        {"from": "include:local_nom", "to": "candidate:gen_delay_inv", "relation": "binds_models"},
        {"from": "candidate:gen_delay_inv", "to": "candidate:tb", "relation": "instantiated_by"},
        {"from": "sim:selected", "to": "candidate:tb", "relation": "syntax_checks"},
    ]
    return {"scope": report["scope"], "nodes": nodes, "edges": edges, "summary": report["audit_summary"]}


def _resolve_path(root: Path, path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return (root / p).resolve()


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def _list_block(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)
