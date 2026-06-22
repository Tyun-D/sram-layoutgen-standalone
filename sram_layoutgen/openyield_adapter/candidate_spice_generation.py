"""Candidate SPICE generation plus FreePDK45 model search."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SEARCH_EXTENSIONS = {
    ".sp",
    ".spi",
    ".spice",
    ".cdl",
    ".model",
    ".mod",
    ".lib",
    ".inc",
    ".include",
    ".pm",
    ".tcl",
    ".txt",
    ".md",
}

SEARCH_KEYWORDS = [
    "NMOS_VTG",
    "PMOS_VTG",
    ".model",
    ".lib",
    "nmos",
    "pmos",
    "nmos_vtg",
    "pmos_vtg",
    "NMOS",
    "PMOS",
    "nfet",
    "pfet",
    "freepdk45",
    "ptm",
    "bsim",
]

HEADER = "\n".join(
    [
        "* CANDIDATE / PLANNING-ONLY",
        "* NOT VALIDATED SPICE",
        "* NOT TIMING PROOF",
        "* DO NOT CLAIM TIMING CLOSURE",
        "* REQUIRES MANUAL REVIEW, PDK MODEL BINDING, AND CHARACTERIZATION",
    ]
)


def build_candidate_spice_generation_report(
    repo_root: str | Path,
    openram_tech_dir: str | Path,
    local_tech_dir: str | Path,
    gen_delay_inv_recovery_path: str | Path,
    four_load_plan_path: str | Path,
    delay_chain_plan_path: str | Path,
    out_dir: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    openram_tech = Path(openram_tech_dir).resolve()
    local_tech = _resolve_path(root, local_tech_dir)
    recovery = _load_json(_resolve_path(root, gen_delay_inv_recovery_path))
    four_load = _load_json(_resolve_path(root, four_load_plan_path))
    delay_plan = _load_json(_resolve_path(root, delay_chain_plan_path))
    out_path = _resolve_path(root, out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    search_roots = [openram_tech, local_tech]
    search_results = _search_pdk_models(search_roots)
    binding_decision = _build_binding_decision(search_results, openram_tech)
    generated_files = _emit_candidate_files(
        out_path=out_path,
        binding_decision=binding_decision,
        recovery=recovery,
        four_load=four_load,
    )

    audit_summary = {
        "pdk_model_search_completed": True,
        "candidate_spice_generation_available": True,
        "gen_delay_inv_candidate_spice_emitted": True,
        "delay_chain_symbolic_tb_emitted": True,
        "device_model_include_found": binding_decision["device_model_include_found"],
        "nmos_vtg_bound": binding_decision["nmos_vtg_bound"],
        "pmos_vtg_bound": binding_decision["pmos_vtg_bound"],
        "needs_model_alias_mapping": binding_decision["needs_model_alias_mapping"],
        "can_run_candidate_spice_now": False,
        "can_run_delay_chain_testbench_now": False,
        "can_claim_delay_proof_now": False,
        "can_claim_timing_closure_now": False,
        "needs_teacher_or_project_provider": binding_decision["needs_teacher_or_project_provider"],
        "can_enter_candidate_spice_syntax_check": binding_decision["device_model_include_found"],
        "can_enter_pvt_corner_definition": True,
        "can_enter_delay_chain_smoke_simulation": False,
        "can_enter_physical_timing_closure_now": False,
        "can_enter_physical_routing_now": False,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    missing_decisions = _dedupe(
        [
            "Project-specified simulator (ngspice / hspice / spectre) is still unknown.",
            "Project-specified VDD is still unknown.",
            "Project-specified PVT corner selection is still unknown.",
            "Measurement threshold policy is still unknown.",
        ]
        + ([] if binding_decision["device_model_include_found"] else ["PDK transistor model include is missing."])
    )
    needs_provider = [
        "1. FreePDK45 NMOS_VTG / PMOS_VTG SPICE device model include file" if not binding_decision["device_model_include_found"] else "1. Confirm the intended FreePDK45 model include and simulator syntax",
        "2. Project-specified simulator: ngspice / hspice / spectre",
        "3. Project-specified VDD",
        "4. Project-specified PVT corner",
        "5. Measurement threshold policy, e.g. 50% VDD or 10%-90% slew",
    ]

    report = {
        "scope": "candidate_spice_generation_and_pdk_model_search",
        "repo_root": str(root),
        "searched_pdk_directories": [str(path) for path in search_roots],
        "input_reports_and_assets": {
            "gen_delay_inv_recovery": str(_resolve_path(root, gen_delay_inv_recovery_path)),
            "four_load_plan": str(_resolve_path(root, four_load_plan_path)),
            "delay_chain_plan": str(_resolve_path(root, delay_chain_plan_path)),
            "openram_tech_dir": str(openram_tech),
            "local_tech_dir": str(local_tech),
            "candidate_spice_dir": str(out_path),
        },
        "audit_summary": audit_summary,
        "model_search_results": search_results,
        "device_model_binding_decision": binding_decision,
        "generated_candidate_files": generated_files,
        "gen_delay_inv_candidate_spice_summary": {
            "subckt_name": "gen_delay_inv",
            "pin_order": ["A", "Z", "vdd", "gnd"],
            "transistor_model_names": ["PMOS_VTG", "NMOS_VTG"],
            "transistor_sizes_from_source": {
                "nmos_width": "0.9e-07",
                "pmos_width": "2.7e-07",
                "length": "0.05e-6",
            },
            "validated_spice": False,
            "timing_proof": False,
        },
        "delay_chain_symbolic_testbench_summary": {
            "stage_count": 9,
            "four_loads_per_stage": True,
            "stage_instances": [f"dinv{i}" for i in range(9)],
            "load_policy": "four same-source inverter loads per stage output",
            "placeholder_params": ["VDD_VALUE", "TEMP_VALUE", "RBL_INPUT_SLEW"],
            "validated_spice": False,
            "timing_proof": False,
        },
        "missing_files_or_decisions": missing_decisions,
        "what_codex_can_do_now": [
            "Search and bind FreePDK45 NMOS_VTG / PMOS_VTG model include files",
            "Emit candidate gen_delay_inv transistor subckt template",
            "Emit planning-only DELAY_CHAIN symbolic testbench template",
            "Emit placeholder measurement and corner include files",
        ],
        "what_needs_user_teacher_or_project_provider": needs_provider,
        "next_recommended_task": "candidate_spice_syntax_check_or_pvt_corner_definition",
        "boundary_assertions": {
            "candidate_spice_is_not_validated_spice": True,
            "candidate_testbench_is_not_timing_proof": True,
            "no_simulation_has_been_run": True,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
    }
    graph = _build_graph(report)
    return {"report": report, "graph": graph}


def format_candidate_spice_generation_markdown(report: dict[str, Any]) -> str:
    search_rows = [
        [
            row["file_path"],
            row["matched_keyword"],
            row["line_number"],
            row["line_excerpt"],
            row["candidate_model_type"],
            row["usable_as_device_model_include"],
            row["notes"],
        ]
        for row in report["model_search_results"]["match_table"]
    ]
    generated_rows = [
        [row["path"], row["kind"], row["exists"], row["notes"]]
        for row in report["generated_candidate_files"]["files"]
    ]
    lines = [
        "# OpenYield Candidate SPICE Generation And PDK Search Report",
        "",
        f"- Scope: `{report['scope']}`",
        f"- Repo root: `{report['repo_root']}`",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Searched PDK Directories",
        "",
        "\n".join(f"- `{path}`" for path in report["searched_pdk_directories"]),
        "",
        "## Device Model Search Results",
        "",
        _md_table(
            ["file_path", "matched_keyword", "line", "excerpt", "candidate_model_type", "usable_include", "notes"],
            search_rows,
        ),
        "",
        "## Device Model Binding Decision",
        "",
        "```json",
        json.dumps(report["device_model_binding_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Generated Candidate Files",
        "",
        _md_table(["path", "kind", "exists", "notes"], generated_rows),
        "",
        "## gen_delay_inv Candidate SPICE Summary",
        "",
        "```json",
        json.dumps(report["gen_delay_inv_candidate_spice_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Delay Chain Symbolic Testbench Summary",
        "",
        "```json",
        json.dumps(report["delay_chain_symbolic_testbench_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Missing Files / Missing Decisions",
        "",
        _list_block(report["missing_files_or_decisions"]),
        "",
        "## What Codex Can Do Now",
        "",
        _list_block(report["what_codex_can_do_now"]),
        "",
        "## What Needs User / Teacher / Project Provider",
        "",
        _list_block(report["what_needs_user_teacher_or_project_provider"]),
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


def _search_pdk_models(search_roots: list[Path]) -> dict[str, Any]:
    match_table: list[dict[str, Any]] = []
    for root in search_roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SEARCH_EXTENSIONS:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            for line_no, line in enumerate(text, start=1):
                for keyword in SEARCH_KEYWORDS:
                    if keyword.lower() in line.lower():
                        match_table.append(
                            {
                                "file_path": str(path),
                                "matched_keyword": keyword,
                                "line_number": line_no,
                                "line_excerpt": line.strip()[:200],
                                "candidate_model_type": _candidate_model_type(path, line),
                                "usable_as_device_model_include": _usable_as_device_model_include(path, line),
                                "notes": _row_notes(path, line),
                            }
                        )
                        break
    has_nmos_vtg_model = any(
        row["matched_keyword"].lower() == "nmos_vtg"
        and row["candidate_model_type"] == "device_model_definition"
        for row in match_table
    )
    has_pmos_vtg_model = any(
        row["matched_keyword"].lower() == "pmos_vtg"
        and row["candidate_model_type"] == "device_model_definition"
        for row in match_table
    )
    has_generic_nmos_pmos_model = any(".model" in row["line_excerpt"].lower() and " nmos " in f" {row['line_excerpt'].lower()} " for row in match_table) and any(
        ".model" in row["line_excerpt"].lower() and " pmos " in f" {row['line_excerpt'].lower()} " for row in match_table
    )
    has_model_include_file = any(row["usable_as_device_model_include"] for row in match_table)
    has_lib_corner_file = any(path.name.startswith("hspice_") and path.suffix == ".include" for root in search_roots for path in root.rglob("*.include"))
    return {
        "match_table": match_table,
        "has_nmos_vtg_model": has_nmos_vtg_model,
        "has_pmos_vtg_model": has_pmos_vtg_model,
        "has_generic_nmos_pmos_model": has_generic_nmos_pmos_model,
        "has_model_include_file": has_model_include_file,
        "has_lib_corner_file": has_lib_corner_file,
    }


def _build_binding_decision(search_results: dict[str, Any], openram_tech: Path) -> dict[str, Any]:
    model_base = openram_tech / "models"
    direct_nom = model_base / "tran_models" / "models_nom"
    direct_ff = model_base / "tran_models" / "models_ff"
    direct_ss = model_base / "tran_models" / "models_ss"
    include_nom = model_base / "hspice_nom.include"
    include_ff = model_base / "hspice_ff.include"
    include_ss = model_base / "hspice_ss.include"
    device_model_include_found = all(
        path.exists()
        for path in [
            direct_nom / "NMOS_VTG.inc",
            direct_nom / "PMOS_VTG.inc",
            include_nom,
        ]
    )
    can_bind_directly = device_model_include_found and search_results["has_lib_corner_file"]
    return {
        "has_nmos_vtg_model": search_results["has_nmos_vtg_model"] or device_model_include_found,
        "has_pmos_vtg_model": search_results["has_pmos_vtg_model"] or device_model_include_found,
        "has_generic_nmos_pmos_model": search_results["has_generic_nmos_pmos_model"],
        "has_model_include_file": search_results["has_model_include_file"] or device_model_include_found,
        "has_lib_corner_file": search_results["has_lib_corner_file"],
        "device_model_include_found": device_model_include_found,
        "nmos_vtg_bound": device_model_include_found,
        "pmos_vtg_bound": device_model_include_found,
        "can_bind_openyield_model_names_directly": can_bind_directly,
        "needs_model_alias_mapping": False,
        "needs_teacher_or_pdk_confirmation": False,
        "needs_teacher_or_project_provider": False,
        "preferred_corner_include": str(include_nom),
        "available_corner_includes": [str(include_nom), str(include_ff), str(include_ss)],
        "direct_model_include_paths": {
            "TT": [str(direct_nom / "PMOS_VTG.inc"), str(direct_nom / "NMOS_VTG.inc")],
            "FF": [str(direct_ff / "PMOS_VTG.inc"), str(direct_ff / "NMOS_VTG.inc")],
            "SS": [str(direct_ss / "PMOS_VTG.inc"), str(direct_ss / "NMOS_VTG.inc")],
        },
        "notes": [
            "OpenRAM FreePDK45 already contains direct NMOS_VTG / PMOS_VTG model definition files.",
            "No alias mapping is needed for the OpenYield Pinv source names.",
            "Simulation is still blocked by missing simulator choice, VDD, PVT selection, and measurement thresholds.",
        ],
    }


def _emit_candidate_files(
    *,
    out_path: Path,
    binding_decision: dict[str, Any],
    recovery: dict[str, Any],
    four_load: dict[str, Any],
) -> dict[str, Any]:
    gen_delay_inv_path = out_path / "gen_delay_inv_candidate.sp"
    tb_path = out_path / "delay_chain_symbolic_tb.sp"
    measure_path = out_path / "delay_chain_measure.inc"
    corner_path = out_path / "delay_chain_corner_placeholder.inc"
    readme_path = out_path / "README.md"

    gen_delay_inv_path.write_text(_gen_delay_inv_candidate_text(), encoding="utf-8", newline="\n")
    tb_path.write_text(_delay_chain_symbolic_tb_text(binding_decision), encoding="utf-8", newline="\n")
    measure_path.write_text(_delay_chain_measure_text(), encoding="utf-8", newline="\n")
    corner_path.write_text(_delay_chain_corner_text(binding_decision), encoding="utf-8", newline="\n")
    readme_path.write_text(_candidate_readme_text(out_path, binding_decision, recovery, four_load), encoding="utf-8", newline="\n")

    return {
        "files": [
            {"path": str(gen_delay_inv_path), "kind": "candidate_subckt", "exists": gen_delay_inv_path.exists(), "notes": "Planning-only inverter leaf."},
            {"path": str(tb_path), "kind": "symbolic_testbench", "exists": tb_path.exists(), "notes": "Nine-stage DELAY_CHAIN with four loads per stage."},
            {"path": str(measure_path), "kind": "measure_template", "exists": measure_path.exists(), "notes": "Planning-only .measure placeholders."},
            {"path": str(corner_path), "kind": "corner_placeholder", "exists": corner_path.exists(), "notes": "PDK include plus TBD corner placeholders."},
            {"path": str(readme_path), "kind": "readme", "exists": readme_path.exists(), "notes": "Usage boundary and missing input checklist."},
        ]
    }


def _gen_delay_inv_candidate_text() -> str:
    return "\n".join(
        [
            HEADER,
            "* Source-visible generator values: NMOS W=0.9e-07, PMOS W=2.7e-07, L=0.05e-6",
            "* These sizes come from OpenYield DelayChain/Pinv source and are not characterized here.",
            "",
            ".SUBCKT gen_delay_inv A Z vdd gnd",
            "M_P Z A vdd vdd PMOS_VTG W=2.7e-07 L=0.05e-6",
            "M_N Z A gnd gnd NMOS_VTG W=0.9e-07 L=0.05e-6",
            ".ENDS gen_delay_inv",
            "",
        ]
    )


def _delay_chain_symbolic_tb_text(binding_decision: dict[str, Any]) -> str:
    lines = [
        HEADER,
        "* DELAY_CHAIN planning-only symbolic testbench",
        f".include \"{Path(binding_decision['preferred_corner_include']).as_posix()}\"",
        ".include \"delay_chain_corner_placeholder.inc\"",
        ".include \"gen_delay_inv_candidate.sp\"",
        ".include \"delay_chain_measure.inc\"",
        "",
        "* Placeholder parameters must be replaced before any simulator run.",
        ".param VDD_VALUE=__TBD_VDD_VALUE__",
        ".param TEMP_VALUE=__TBD_TEMP_VALUE__",
        ".param RBL_INPUT_SLEW=__TBD_RBL_INPUT_SLEW__",
        "",
        "* Suggested future sources only; left disconnected until project policy is confirmed.",
        "* VDD vdd 0 {VDD_VALUE}",
        "* VIN rbl 0 PULSE(...)",
        "",
    ]
    stage_inputs = ["rbl"] + [f"dout_{i}" for i in range(1, 9)]
    stage_outputs = [f"dout_{i}" for i in range(1, 9)] + ["rbl_delay"]
    for stage, (inp, outp) in enumerate(zip(stage_inputs, stage_outputs)):
        lines.append(f"Xdinv{stage} {inp} {outp} vdd gnd gen_delay_inv")
        for slot in range(4):
            lines.append(f"Xdload_{stage}_{slot} {outp} n_{stage}_{slot} vdd gnd gen_delay_inv")
        lines.append("")
    lines.extend(
        [
            "* Dummy load outputs n_<stage>_<slot> are load-only placeholders, not signal endpoints.",
            ".END",
            "",
        ]
    )
    return "\n".join(lines)


def _delay_chain_measure_text() -> str:
    return "\n".join(
        [
            HEADER,
            "* Planning-only measure template. Thresholds remain TBD.",
            "*.measure tran chain_delay_rbl_to_rbl_delay TRIG v(rbl) VAL=__TBD_THRESH__ RISE=1 TARG v(rbl_delay) VAL=__TBD_THRESH__ RISE=1",
            "*.measure tran input_slew_at_rbl TRIG v(rbl) VAL=__TBD_SLEW_LOW__ RISE=1 TARG v(rbl) VAL=__TBD_SLEW_HIGH__ RISE=1",
            "*.measure tran output_slew_at_rbl_delay TRIG v(rbl_delay) VAL=__TBD_SLEW_LOW__ RISE=1 TARG v(rbl_delay) VAL=__TBD_SLEW_HIGH__ RISE=1",
            "*.measure tran pulse_width_at_rbl_delay TRIG v(rbl_delay) VAL=__TBD_THRESH__ RISE=1 TARG v(rbl_delay) VAL=__TBD_THRESH__ FALL=1",
            "*.measure tran stage_midpoint_delay_rbl_to_dout_5 TRIG v(rbl) VAL=__TBD_THRESH__ RISE=1 TARG v(dout_5) VAL=__TBD_THRESH__ RISE=1",
            "",
        ]
    )


def _delay_chain_corner_text(binding_decision: dict[str, Any]) -> str:
    include_paths = binding_decision["direct_model_include_paths"]["TT"]
    return "\n".join(
        [
            HEADER,
            "* Candidate default corner include for TT-style planning.",
            f".include \"{Path(include_paths[0]).as_posix()}\"",
            f".include \"{Path(include_paths[1]).as_posix()}\"",
            "* Future project policy may instead choose one of:",
            *[f"* {Path(path).as_posix()}" for path in binding_decision["available_corner_includes"]],
            "* TODO: replace with project-approved simulator/corner include policy.",
            "",
        ]
    )


def _candidate_readme_text(
    out_path: Path,
    binding_decision: dict[str, Any],
    recovery: dict[str, Any],
    four_load: dict[str, Any],
) -> str:
    lines = [
        "# Candidate SPICE Templates",
        "",
        "These files are planning-only candidate artifacts.",
        "",
        "```spice",
        HEADER,
        "```",
        "",
        f"- Directory: `{out_path}`",
        f"- `can_generate_candidate_spice=True`",
        f"- `can_run_ngspice_or_hspice_now=False`",
        f"- `missing_required_external_file={'none_for_model_binding' if binding_decision['device_model_include_found'] else 'PDK transistor model include for NMOS_VTG / PMOS_VTG'}`",
        f"- `needs_teacher_or_project_provider={binding_decision['needs_teacher_or_project_provider']}`",
        "",
        "## Found model binding",
        "",
        f"- Preferred include: `{binding_decision['preferred_corner_include']}`",
        f"- Direct TT PMOS include: `{binding_decision['direct_model_include_paths']['TT'][0]}`",
        f"- Direct TT NMOS include: `{binding_decision['direct_model_include_paths']['TT'][1]}`",
        f"- `can_bind_openyield_model_names_directly={binding_decision['can_bind_openyield_model_names_directly']}`",
        "",
        "## Emitted files",
        "",
        "- `gen_delay_inv_candidate.sp`",
        "- `delay_chain_symbolic_tb.sp`",
        "- `delay_chain_measure.inc`",
        "- `delay_chain_corner_placeholder.inc`",
        "",
        "## Still missing before any real simulation",
        "",
        "- Project-specified simulator: ngspice / hspice / spectre",
        "- Project-specified VDD",
        "- Project-specified PVT corner",
        "- Measurement threshold policy, e.g. 50% VDD or 10%-90% slew",
        "- Manual review of candidate `gen_delay_inv` subckt against source and project signoff expectations",
        "",
        "## Source-backed context",
        "",
        f"- `next_recommended_proof_task` from recovery: `{recovery.get('next_recommended_proof_task')}`",
        f"- `recommended_planning_binding` from four-load model: `{four_load.get('recommended_planning_binding')}`",
        "",
    ]
    return "\n".join(lines)


def _build_graph(report: dict[str, Any]) -> dict[str, Any]:
    nodes = [
        {"id": "tech:openram", "kind": "pdk_root", "label": "OpenRAM freepdk45"},
        {"id": "tech:local", "kind": "pdk_root", "label": "local freepdk45"},
        {"id": "model:NMOS_VTG", "kind": "device_model", "label": "NMOS_VTG"},
        {"id": "model:PMOS_VTG", "kind": "device_model", "label": "PMOS_VTG"},
        {"id": "subckt:gen_delay_inv", "kind": "candidate_subckt", "label": "gen_delay_inv"},
        {"id": "tb:delay_chain", "kind": "candidate_tb", "label": "DELAY_CHAIN TB"},
    ]
    edges = [
        {"from": "tech:openram", "to": "model:NMOS_VTG", "relation": "contains"},
        {"from": "tech:openram", "to": "model:PMOS_VTG", "relation": "contains"},
        {"from": "model:NMOS_VTG", "to": "subckt:gen_delay_inv", "relation": "binds"},
        {"from": "model:PMOS_VTG", "to": "subckt:gen_delay_inv", "relation": "binds"},
        {"from": "subckt:gen_delay_inv", "to": "tb:delay_chain", "relation": "instantiated_by"},
    ]
    return {"scope": report["scope"], "nodes": nodes, "edges": edges, "summary": report["audit_summary"]}


def _candidate_model_type(path: Path, line: str) -> str:
    lower = line.lower()
    if ".model" in lower and ("nmos_vtg" in lower or "pmos_vtg" in lower):
        return "device_model_definition"
    if path.name.startswith("hspice_") and ".inc" in lower:
        return "corner_include"
    if path.suffix == ".sp":
        return "transistor_netlist_usage"
    return "metadata_or_reference"


def _usable_as_device_model_include(path: Path, line: str) -> bool:
    lower = line.lower()
    return (
        path.suffix.lower() in {".inc", ".include", ".lib"}
        or (".model" in lower and ("nmos_vtg" in lower or "pmos_vtg" in lower))
    )


def _row_notes(path: Path, line: str) -> str:
    lower = line.lower()
    if ".model" in lower and ("nmos_vtg" in lower or "pmos_vtg" in lower):
        return "Direct model definition."
    if path.name.startswith("hspice_") and ".inc" in lower:
        return "Corner include references NMOS_VTG / PMOS_VTG."
    if path.suffix == ".sp" and ("nmos_vtg" in lower or "pmos_vtg" in lower):
        return "Netlist instance usage proves model names are expected by project SPICE."
    return "Reference match."


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
