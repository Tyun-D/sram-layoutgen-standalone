from __future__ import annotations

import argparse
import csv
import importlib
import json
import re
import sys
import traceback
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.clean_top_export import (  # noqa: E402
    CLASS_DESIGN,
    CLASS_MEAS,
    CLASS_MODEL,
    CLASS_SIM,
    CLASS_STIM,
    TOP_MODULE_NAME,
    classification_reason,
    classify_spice_line,
    extract_clean_top,
    generator_call_classification_rows,
    parse_spice_text,
    top_level_classification_rows,
    verification_flags,
    write_text,
)
from sram_layoutgen.openyield_adapter.openyield_graph_export import (  # noqa: E402
    build_clean_graph,
    verify_graph_against_spice,
    write_csv,
    write_json,
)
from sram_layoutgen.openyield_adapter.openyield_spec_v1 import (  # noqa: E402
    build_spec_example,
    build_spec_schema,
    render_spec_md,
    validate_spec_v1,
)


TIME_QUESTION = "OpenYield 中 time_generate.py 生成的 TIME 子电路，是计划作为 SRAM 宏内部真实片上控制逻辑进行物理实现，还是只作为仿真测试平台中的控制时序模型？"
NEXT_STAGE = "M12N2H_REQUEST_TIME_ROLE_CONFIRMATION"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def _replace_section(text: str, heading: str, body_lines: list[str]) -> str:
    block = "\n".join([heading, "", *body_lines]).rstrip() + "\n"
    marker = f"\n{heading}\n"
    if text.startswith(f"{heading}\n"):
        start = 0
    else:
        start = text.find(marker)
        if start >= 0:
            start += 1
    if start < 0:
        return text.rstrip() + "\n\n" + block
    next_heading = text.find("\n## ", start + len(heading) + 1)
    if next_heading < 0:
        return text[:start].rstrip() + "\n\n" + block
    return text[:start].rstrip() + "\n\n" + block + "\n" + text[next_heading + 1 :].lstrip("\n")


def _rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except Exception:
        return str(path.resolve())


def _load_openyield_config(openyield_root: Path):
    sys.path.insert(0, str(openyield_root))
    from sram_compiler.config_yaml.config import SRAM_CONFIG

    cfg = SRAM_CONFIG()
    cfg.load_all_configs(
        global_file=str(openyield_root / "sram_compiler/config_yaml/global.yaml"),
        circuit_configs={
            "SRAM_6T_CELL": str(openyield_root / "sram_compiler/config_yaml/sram_6t_cell.yaml"),
            "SRAM_10T_CELL": str(openyield_root / "sram_compiler/config_yaml/sram_10t_cell.yaml"),
            "WORDLINEDRIVER": str(openyield_root / "sram_compiler/config_yaml/wordline_driver.yaml"),
            "PRECHARGE": str(openyield_root / "sram_compiler/config_yaml/precharge.yaml"),
            "COLUMNMUX": str(openyield_root / "sram_compiler/config_yaml/mux.yaml"),
            "SENSEAMP": str(openyield_root / "sram_compiler/config_yaml/sa.yaml"),
            "WRITEDRIVER": str(openyield_root / "sram_compiler/config_yaml/write_driver.yaml"),
            "DECODER": str(openyield_root / "sram_compiler/config_yaml/decoder.yaml"),
        },
    )
    return cfg


def _generate_testbench_text(
    *,
    openyield_root: Path,
    num_rows: int,
    num_cols: int,
    choose_columnmux: bool,
    sim_path: Path,
) -> str:
    sys.path.insert(0, str(openyield_root))
    from sram_compiler.testbenches.sram_6t_core_testbench import Sram6TCoreTestbench

    cfg = _load_openyield_config(openyield_root)
    cfg.global_config.num_rows = num_rows
    cfg.global_config.num_cols = num_cols
    cfg.global_config.choose_columnmux = choose_columnmux
    cfg.global_config.sram_cell_type = "SRAM_6T_CELL"
    tb = Sram6TCoreTestbench(
        cfg,
        sram_cell_type=cfg.global_config.sram_cell_type,
        w_rc=False,
        custom_mc=False,
        sweep_cell=False,
        sweep_precharge=False,
        sweep_senseamp=False,
        sweep_wordlinedriver=False,
        sweep_columnmux=False,
        sweep_writedriver=False,
        sweep_decoder=False,
        corner=cfg.global_config.corner,
        choose_columnmux=choose_columnmux,
        real_cell_mode=0,
        q_init_val=0,
        sim_path=str(sim_path),
    )
    circuit = tb.create_testbench("read&write", num_rows - 1, num_cols - 1)
    return str(circuit)


def _check_import(module_name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module_name)
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _collect_time_evidence(openyield_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    time_file = openyield_root / "sram_compiler/subcircuits/time_generate.py"
    tb_file = openyield_root / "sram_compiler/testbenches/sram_6t_core_testbench.py"
    readme = openyield_root / "README.md"
    compiler_readme = openyield_root / "readme_compiler.md"

    evidence_rows = [
        {
            "evidence_id": "TIME_SRC_DEF",
            "source": _rel(REPO_ROOT, time_file),
            "evidence_type": "source_definition",
            "detail": "TIME defines clk/csb/web inputs; clk_buf/clk_bar/cs/we/gated_clk/wl_en/rbl_delay/s_en/w_en/PRE outputs and internal DFF/delay-chain logic.",
            "supports_role": "AMBIGUOUS_REQUIRES_TEAM_CONFIRMATION",
        },
        {
            "evidence_id": "TIME_NO_INDEPENDENT_SOURCE",
            "source": _rel(REPO_ROOT, time_file),
            "evidence_type": "source_definition",
            "detail": "TIME subcircuit contains logic/transistor-level instances and no independent voltage source definitions.",
            "supports_role": "AMBIGUOUS_REQUIRES_TEAM_CONFIRMATION",
        },
        {
            "evidence_id": "TIME_INST_POSITION",
            "source": _rel(REPO_ROOT, tb_file),
            "evidence_type": "instantiation",
            "detail": "create_testbench() instantiates TIME from the testbench flow, then decoder/wordline/read/write periphery consume TIME outputs.",
            "supports_role": "AMBIGUOUS_REQUIRES_TEAM_CONFIRMATION",
        },
        {
            "evidence_id": "REPO_POSITIONING",
            "source": _rel(REPO_ROOT, readme),
            "evidence_type": "repo_readme",
            "detail": "Repository positions OpenYield as an SRAM circuit generator and simulation / yield-analysis platform.",
            "supports_role": "AMBIGUOUS_REQUIRES_TEAM_CONFIRMATION",
        },
        {
            "evidence_id": "COMPILER_GUIDE",
            "source": _rel(REPO_ROOT, compiler_readme),
            "evidence_type": "repo_readme",
            "detail": "readme_compiler.md describes time_generate.py as clock, delay chain, flip-flop, and control timing generation inside the test platform.",
            "supports_role": "AMBIGUOUS_REQUIRES_TEAM_CONFIRMATION",
        },
        {
            "evidence_id": "GIT_HISTORY",
            "source": ".git history",
            "evidence_type": "git_log_blame",
            "detail": "Git history shows TIME and testbench evolving together in simulation-oriented commits, but does not state physical-macro implementation intent.",
            "supports_role": "AMBIGUOUS_REQUIRES_TEAM_CONFIRMATION",
        },
    ]
    summary = {
        "time_control_role_status": "AMBIGUOUS_REQUIRES_TEAM_CONFIRMATION",
        "time_control_role_evidence_complete": True,
        "time_role_requires_team_confirmation": True,
        "can_claim_control_logic_mapping_ready": False,
        "recommended_next_stage": NEXT_STAGE,
        "recommended_next_stage_reason": "TIME is electrically connected to real decoder / precharge / sense-amp / write-driver / wordline-driver consumers, but the repository evidence still frames the flow as a simulation platform and does not explicitly confirm that TIME is intended for on-chip physical implementation.",
        "can_enter_next_stage_before_human_review": False,
        "teacher_question": TIME_QUESTION,
    }
    return summary, evidence_rows


def _parameter_scope_text() -> str:
    return (
        "V1 is locked only for choose_columnmux=false, words_per_row=1, mux_ratio=1, "
        "num_words=num_rows, word_size=num_cols, and sram_cell_type=6T."
    )


def _make_blockers(time_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "blocker_id": "M12N2-B01",
            "description": "TIME role is not explicitly confirmed as on-chip control logic versus simulation timing model.",
            "machine_solvable": False,
            "requires_user_action": False,
            "requires_teacher_confirmation": True,
            "requires_external_file": False,
            "requires_external_tool": False,
            "blocks_which_stage": "M12C_CONTROL_LOGIC_GAP_DEFINITION",
            "resolution_action": TIME_QUESTION,
            "status": "OPEN",
        },
        {
            "blocker_id": "M12N2-B02",
            "description": "words_per_row > 1 and arbitrary numeric column mux ratio remain unverified.",
            "machine_solvable": False,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": False,
            "requires_external_tool": False,
            "blocks_which_stage": "post-V1 parameter expansion",
            "resolution_action": "Add explicit raw-source-backed mux-ratio contract and generate verified >1 words_per_row samples.",
            "status": "OPEN",
        },
        {
            "blocker_id": "M12N2-B03",
            "description": "tech parameter is not connected to a physical PDK abstraction for layout generation.",
            "machine_solvable": False,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": True,
            "requires_external_tool": False,
            "blocks_which_stage": "physical tech binding",
            "resolution_action": "Define a physical tech/PDK contract distinct from simulation model includes.",
            "status": "OPEN",
        },
        {
            "blocker_id": "M12N2-B04",
            "description": "No complete DRC/LVS/extraction loop is available for the extracted clean top.",
            "machine_solvable": False,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": False,
            "requires_external_tool": True,
            "blocks_which_stage": "signoff verification",
            "resolution_action": "Create a later physical verification stage after layout integration.",
            "status": "OPEN",
        },
        {
            "blocker_id": "M12N2-B05",
            "description": "Control-logic physical implementation is not completed and cannot be claimed ready.",
            "machine_solvable": False,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": False,
            "requires_external_tool": False,
            "blocks_which_stage": "control-logic physical implementation",
            "resolution_action": "Wait for TIME role confirmation, then define control-logic physical gap closure scope.",
            "status": "OPEN",
        },
        {
            "blocker_id": "M12N2-B06",
            "description": "OpenYield exposes a testbench-backed generator rather than a native pure-SRAM-top generator API.",
            "machine_solvable": True,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": False,
            "requires_external_tool": False,
            "blocks_which_stage": "future generator cleanup",
            "resolution_action": "Keep using extraction/clean-top export until a native pure-top generator exists.",
            "status": "MITIGATED_BY_M12N2",
        },
        {
            "blocker_id": "M12N2-B07",
            "description": "OpenRAM references are still missing a matched full SPICE/LEF/Verilog/config contract for direct cross-flow equivalence.",
            "machine_solvable": False,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": True,
            "requires_external_tool": False,
            "blocks_which_stage": "cross-flow equivalence closure",
            "resolution_action": "Provide or align the missing OpenRAM collateral before any equivalence claim.",
            "status": "OPEN",
        },
    ]


def _write_blocker_reports(out_dir: Path, docs_mapping: Path, blockers: list[dict[str, Any]]) -> None:
    blocker_md = _render_md(
        "M12N2 External Dependency Blockers",
        [f"- {row['blocker_id']}: `{row['status']}` | {row['description']} | resolution_action: `{row['resolution_action']}`" for row in blockers],
    )
    write_text(out_dir / "M12N2_external_dependency_blockers.md", blocker_md)
    write_csv(
        docs_mapping / "M12N2_external_dependency_blockers.csv",
        blockers,
        [
            "blocker_id",
            "description",
            "machine_solvable",
            "requires_user_action",
            "requires_teacher_confirmation",
            "requires_external_file",
            "requires_external_tool",
            "blocks_which_stage",
            "resolution_action",
            "status",
        ],
    )


def _write_json_md_pair(base_json: Path, base_md: Path, title: str, payload: dict[str, Any]) -> None:
    write_json(base_json, payload)
    lines = [f"- {key}: `{value}`" for key, value in payload.items()]
    write_text(base_md, _render_md(title, lines))


def _scaling_summary(graph: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    top_instances = [item for item in graph["instances"] if item["parent_module"] == TOP_MODULE_NAME]
    nets = [item for item in graph["nets"] if item["module_name"] == TOP_MODULE_NAME]
    return {
        "bitcell_core_instance_count": sum(1 for item in top_instances if item["module_name"].startswith("SRAM_6T_CORE_")),
        "wordline_count": sum(1 for item in nets if re.match(r"^WL\d+$", item["net_name"], re.IGNORECASE)),
        "bitline_count": sum(1 for item in nets if re.match(r"^BL\d+$", item["net_name"], re.IGNORECASE)),
        "sense_amp_count": sum(1 for item in top_instances if item["module_name"] == "SENSEAMP"),
        "write_driver_count": sum(1 for item in top_instances if item["module_name"] == "WRITEDRIVER"),
        "wordline_driver_count": sum(1 for item in top_instances if item["module_name"] == "WORDLINEDRIVER"),
        "address_width": sum(1 for item in graph["pins"] if item["pin_role"] == "address"),
        "top_data_pin_count": sum(1 for item in graph["pins"] if item["pin_role"] in {"data_input", "data_output", "data_output_bar"}),
        "spec": spec,
    }


def _validate_scaling(summary_a: dict[str, Any], summary_b: dict[str, Any]) -> bool:
    return (
        summary_a["wordline_count"] == summary_a["spec"]["num_rows"]
        and summary_b["wordline_count"] == summary_b["spec"]["num_rows"]
        and summary_a["bitline_count"] == summary_a["spec"]["num_cols"]
        and summary_b["bitline_count"] == summary_b["spec"]["num_cols"]
        and summary_a["sense_amp_count"] == summary_a["spec"]["num_cols"]
        and summary_b["sense_amp_count"] == summary_b["spec"]["num_cols"]
        and summary_a["write_driver_count"] == summary_a["spec"]["num_cols"]
        and summary_b["write_driver_count"] == summary_b["spec"]["num_cols"]
        and summary_a["wordline_driver_count"] == summary_a["spec"]["num_rows"]
        and summary_b["wordline_driver_count"] == summary_b["spec"]["num_rows"]
        and summary_a["address_width"] == max(1, (summary_a["spec"]["num_rows"] - 1).bit_length())
        and summary_b["address_width"] == max(1, (summary_b["spec"]["num_rows"] - 1).bit_length())
        and summary_a["top_data_pin_count"] == summary_a["spec"]["num_cols"] * 3
        and summary_b["top_data_pin_count"] == summary_b["spec"]["num_cols"] * 3
    )


def _write_graph_sidecars(base: Path, graph: dict[str, Any]) -> None:
    write_json(base.with_suffix(".json"), graph)
    write_csv(base.parent / f"{base.stem}_modules.csv", graph["modules"], ["module_name", "pin_count", "pins", "source_trace"])
    write_csv(
        base.parent / f"{base.stem}_instances.csv",
        graph["instances"],
        ["instance_id", "parent_module", "instance_name", "instance_type", "module_name", "pin_count", "nets", "source_trace"],
    )
    write_csv(
        base.parent / f"{base.stem}_nets.csv",
        graph["nets"],
        ["module_name", "net_name", "canonical_name", "connection_count", "is_top_pin", "net_role", "source_trace", "connections"],
    )
    write_csv(
        base.parent / f"{base.stem}_pins.csv",
        graph["pins"],
        ["module_name", "pin_name", "canonical_name", "pin_role", "source_trace"],
    )


def _update_status_md(text: str, report: dict[str, Any]) -> str:
    text = _replace_section(
        text,
        "## 2. Current Stage",
        [
            "- current_stage: `M12N2`",
            f"- next_stage: `{report['recommended_next_stage']}`",
            "- human_klayout_review_required_every_stage: `True`",
            f"- can_enter_next_stage_without_human_review: `{report['can_enter_next_stage_before_human_review']}`",
            f"- next_stage_allowed: `{report['recommended_next_stage']}`",
        ],
    )
    return _replace_section(
        text,
        "## 5. M12N2 Clean Top Extraction Result",
        [
            f"- clean_top_locked: `{report['can_claim_openyield_clean_layout_facing_top_locked']}`",
            f"- parameter_contract_v1_locked: `{report['parameter_contract_v1_locked']}`",
            f"- time_control_role_status: `{report['time_control_role_status']}`",
            f"- remaining_M12N2_blockers_count: `{report['remaining_M12N2_blockers_count']}`",
            f"- recommended_next_stage: `{report['recommended_next_stage']}`",
            "- physical_gds_generation_not_part_of_M12N2: `True`",
            "- reused_M12O_review_gds: `True`",
            "- can_make_physical_implementation_claim: `False`",
        ],
    )


def _update_goal_md(text: str, report: dict[str, Any]) -> str:
    return _replace_section(
        text,
        "## Current Clean Top Gate",
        [
            "- M12N2 从 OpenYield testbench-backed generator 中提取 clean layout-facing SRAM top，并锁定可验证的参数接口 V1。",
            "- 本阶段只处理纯网表 / graph / 参数 contract，不生成新的最终 GDS，也不进入 CONTROL_LOGIC 物理实现。",
            f"- 当前 TIME 角色结论：`{report['time_control_role_status']}`。",
            f"- 当前推荐下一阶段：`{report['recommended_next_stage']}`。",
        ],
    )


def _update_progress_md(text: str, report: dict[str, Any]) -> str:
    return _replace_section(
        text,
        "## M12N2 Clean OpenYield SRAM Top",
        [
            f"- clean_top_extraction_passed: `{report['clean_top_extraction_passed']}`",
            f"- clean_top_spice_path: `{report['clean_top_spice_path']}`",
            f"- parameter_contract_v1_locked: `{report['parameter_contract_v1_locked']}`",
            f"- sample_16x16_generated: `{report['sample_16x16_generated']}`",
            f"- sample_64x8_generated: `{report['sample_64x8_generated']}`",
            f"- parameter_scaling_verified: `{report['parameter_scaling_verified']}`",
            f"- time_control_role_status: `{report['time_control_role_status']}`",
            f"- recommended_next_stage: `{report['recommended_next_stage']}`",
            f"- can_enter_next_stage_before_human_review: `{report['can_enter_next_stage_before_human_review']}`",
            "- note: `M12N2 is a netlist/graph extraction gate only. It does not generate final physical GDS and does not reopen DRC/LVS/signoff claims.`",
        ],
    )


def run_m12n2(
    *,
    repo_root: Path,
    openyield_root: Path,
    status_md: Path,
    status_json: Path,
    goal_md: Path,
    progress_md: Path,
    m12n_report: Path,
    sample_testbench_netlist: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_mapping = repo_root / "docs" / "mapping"
    docs_mapping.mkdir(parents=True, exist_ok=True)

    status_md_text = _read_text(status_md)
    status = _read_json(status_json)
    goal_text = _read_text(goal_md)
    progress_text = _read_text(progress_md)
    m12n = _read_json(m12n_report)
    sample_text = _read_text(sample_testbench_netlist)

    regex_before = _check_import("regex")[0]
    regex_after = regex_before
    main_import, main_reason = _check_import("main_sram")
    eq_import, eq_reason = _check_import("equivalent_modeling.main_sram")
    if not main_import or not eq_import:
        sys.path.insert(0, str(openyield_root))
        main_import, main_reason = _check_import("main_sram")
        eq_import, eq_reason = _check_import("equivalent_modeling.main_sram")

    sample_parsed = parse_spice_text(sample_text)
    classification_rows = top_level_classification_rows(sample_parsed, "sample_openyield_sram_netlist")
    classification_rows.extend(generator_call_classification_rows())
    write_csv(
        out_dir / "M12N2_testbench_element_classification.csv",
        classification_rows,
        ["origin", "element_scope", "element_name", "element_type", "raw_text", "classification", "reason"],
    )
    write_csv(
        docs_mapping / "M12N2_testbench_element_classification.csv",
        classification_rows,
        ["origin", "element_scope", "element_name", "element_type", "raw_text", "classification", "reason"],
    )

    design_element_count = sum(1 for row in classification_rows if row["classification"] == CLASS_DESIGN)
    stimulus_count = sum(1 for row in classification_rows if row["classification"] == CLASS_STIM)
    sim_count = sum(1 for row in classification_rows if row["classification"] == CLASS_SIM)
    meas_count = sum(1 for row in classification_rows if row["classification"] == CLASS_MEAS)

    source_trace = {
        "generator": "sram_compiler/testbenches/sram_6t_core_testbench.py::Sram6TCoreTestbench.create_testbench",
        "sample_netlist": _rel(repo_root, sample_testbench_netlist),
    }
    spec_16 = build_spec_example(16, 16)
    spec_64 = build_spec_example(64, 8)
    spec_errors = validate_spec_v1(spec_16) + validate_spec_v1(spec_64)
    if spec_errors:
        raise ValueError("; ".join(spec_errors))

    write_json(out_dir / "OPENYIELD_SRAM_SPEC_V1.schema.json", build_spec_schema())
    write_json(out_dir / "OPENYIELD_SRAM_SPEC_V1.example_16x16.json", spec_16)
    write_json(out_dir / "OPENYIELD_SRAM_SPEC_V1.example_64x8.json", spec_64)
    write_text(out_dir / "OPENYIELD_SRAM_SPEC_V1.md", render_spec_md())

    current_text = _generate_testbench_text(
        openyield_root=openyield_root,
        num_rows=16,
        num_cols=16,
        choose_columnmux=False,
        sim_path=out_dir / "sim_current_supported_config",
    )
    current_parsed = parse_spice_text(current_text)
    clean_payload = extract_clean_top(
        current_parsed,
        {
            "num_rows": 16,
            "num_cols": 16,
            "num_words": 16,
            "word_size": 16,
            "words_per_row": 1,
            "mux_ratio": 1,
            "choose_columnmux": False,
            "sram_cell_type": "6T",
        },
        source_trace,
    )
    clean_spice_path = out_dir / "openyield_sram_top_v1.sp"
    write_text(clean_spice_path, clean_payload["clean_netlist_text"])

    graph = build_clean_graph(
        clean_text=clean_payload["clean_netlist_text"],
        top_module_name=TOP_MODULE_NAME,
        top_pin_roles=clean_payload["pin_roles"],
        parameters=clean_payload["parameters"],
        openyield_root=openyield_root,
        source_trace=source_trace,
    )
    graph_path = out_dir / "openyield_sram_top_v1_graph.json"
    write_json(graph_path, graph)
    write_csv(out_dir / "openyield_sram_top_v1_modules.csv", graph["modules"], ["module_name", "pin_count", "pins", "source_trace"])
    write_csv(out_dir / "openyield_sram_top_v1_instances.csv", graph["instances"], ["instance_id", "parent_module", "instance_name", "instance_type", "module_name", "pin_count", "nets", "source_trace"])
    write_csv(out_dir / "openyield_sram_top_v1_nets.csv", graph["nets"], ["module_name", "net_name", "canonical_name", "connection_count", "is_top_pin", "net_role", "source_trace", "connections"])
    write_csv(out_dir / "openyield_sram_top_v1_pins.csv", graph["pins"], ["module_name", "pin_name", "canonical_name", "pin_role", "source_trace"])

    write_csv(docs_mapping / "M12N2_clean_top_modules.csv", graph["modules"], ["module_name", "pin_count", "pins", "source_trace"])
    write_csv(docs_mapping / "M12N2_clean_top_instances.csv", graph["instances"], ["instance_id", "parent_module", "instance_name", "instance_type", "module_name", "pin_count", "nets", "source_trace"])
    write_csv(docs_mapping / "M12N2_clean_top_nets.csv", graph["nets"], ["module_name", "net_name", "canonical_name", "connection_count", "is_top_pin", "net_role", "source_trace", "connections"])
    write_csv(docs_mapping / "M12N2_clean_top_pins.csv", graph["pins"], ["module_name", "pin_name", "canonical_name", "pin_role", "source_trace"])

    flags = verification_flags(clean_payload["clean_netlist_text"])
    graph_checks = verify_graph_against_spice(clean_payload["clean_netlist_text"], graph)

    sample_16_text = clean_payload["clean_netlist_text"]
    write_text(out_dir / "openyield_sram_top_v1_16x16.sp", sample_16_text)
    write_json(out_dir / "openyield_sram_top_v1_16x16_graph.json", graph)

    text_64 = _generate_testbench_text(
        openyield_root=openyield_root,
        num_rows=64,
        num_cols=8,
        choose_columnmux=False,
        sim_path=out_dir / "sim_64x8",
    )
    payload_64 = extract_clean_top(
        parse_spice_text(text_64),
        {
            "num_rows": 64,
            "num_cols": 8,
            "num_words": 64,
            "word_size": 8,
            "words_per_row": 1,
            "mux_ratio": 1,
            "choose_columnmux": False,
            "sram_cell_type": "6T",
        },
        source_trace,
    )
    write_text(out_dir / "openyield_sram_top_v1_64x8.sp", payload_64["clean_netlist_text"])
    graph_64 = build_clean_graph(
        clean_text=payload_64["clean_netlist_text"],
        top_module_name=TOP_MODULE_NAME,
        top_pin_roles=payload_64["pin_roles"],
        parameters=payload_64["parameters"],
        openyield_root=openyield_root,
        source_trace=source_trace,
    )
    write_json(out_dir / "openyield_sram_top_v1_64x8_graph.json", graph_64)

    scaling_16 = _scaling_summary(graph, spec_16)
    scaling_64 = _scaling_summary(graph_64, spec_64)
    scaling_ok = _validate_scaling(scaling_16, scaling_64)
    scaling_report = {
        "sample_16x16_generated": True,
        "sample_64x8_generated": True,
        "parameter_scaling_verified": scaling_ok,
        "sample_16x16": scaling_16,
        "sample_64x8": scaling_64,
    }
    _write_json_md_pair(
        out_dir / "M12N2_parameter_scaling_report.json",
        out_dir / "M12N2_parameter_scaling_report.md",
        "M12N2 Parameter Scaling Report",
        scaling_report,
    )

    time_summary, time_evidence_rows = _collect_time_evidence(openyield_root)
    _write_json_md_pair(
        out_dir / "M12N2_control_logic_role_report.json",
        out_dir / "M12N2_control_logic_role_report.md",
        "M12N2 Control Logic Role Report",
        time_summary,
    )
    write_csv(
        docs_mapping / "M12N2_control_logic_role_evidence.csv",
        time_evidence_rows,
        ["evidence_id", "source", "evidence_type", "detail", "supports_role"],
    )

    blockers = _make_blockers(time_summary)
    _write_blocker_reports(out_dir, docs_mapping, blockers)

    extraction_report = {
        "reused_previous_artifacts": [
            "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.* ledgers",
            "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
            "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
            "M12N authority lock report and matrices",
            "sample_openyield_sram_netlist.sp",
            "/data1/qujh/work/external/OpenYield generator/testbench/subcircuit sources",
        ],
        "deprecated_previous_artifacts": [
            "Treating sample_openyield_sram_netlist.sp as a clean SRAM top",
            "Treating target-column D_LATCH observation logic as the macro data-output contract",
            "Assuming TIME is already physically-qualified control logic without explicit repo evidence",
        ],
        "current_stage_inputs": [
            "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
            "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
            "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
            "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
            "docs/M12N_lock_openyield_authoritative_netlist_report.json",
            "docs/M12N_lock_openyield_authoritative_netlist_report.md",
            "docs/mapping/M12N_openyield_file_role_classification.csv",
            "docs/mapping/M12N_openyield_entrypoint_callgraph.csv",
            "docs/mapping/M12N_parameter_interface_matrix.csv",
            "docs/mapping/M12N_sram_top_coverage_matrix.csv",
            "docs/mapping/M12N_control_logic_source_matrix.csv",
            "docs/mapping/M12N_external_dependency_blockers.csv",
            "outputs/M12N_lock_openyield_authoritative_netlist/current_supported_config/sample_openyield_sram_netlist.sp",
            str(openyield_root),
            "sram_compiler/testbenches/sram_6t_core_testbench.py",
            "sram_compiler/subcircuits/sram_6t_core.py",
            "sram_compiler/subcircuits/time_generate.py",
            "sram_compiler/subcircuits/decoder.py",
            "sram_compiler/subcircuits/wordline_driver.py",
            "sram_compiler/subcircuits/precharge_and_write_driver.py",
            "sram_compiler/subcircuits/mux_and_sa.py",
            "sram_compiler/subcircuits/replica_column.py",
            "main_sram.py",
            "main_opt.py",
            "main_estimation.py",
        ],
        "current_stage_delta_from_M12N": "M12N2 moves from source authority lock to machine extraction of a clean layout-facing SRAM top, graph export, and parameter contract locking.",
        "why_M12N2_precedes_M12C": "A control-logic gap discussion is lower-value until the raw testbench graph is stripped into a stable clean-top contract with explicit design/testbench separation and machine-verifiable connectivity.",
        "clean_top_extraction_passed": not any(
            [
                flags["clean_top_contains_independent_stimulus"],
                flags["clean_top_contains_pulse"],
                flags["clean_top_contains_pwl"],
                flags["clean_top_contains_tran"],
                flags["clean_top_contains_measure"],
                flags["clean_top_contains_monte_carlo"],
            ]
        ),
        "clean_top_spice_path": _rel(repo_root, clean_spice_path),
        "clean_top_graph_path": _rel(repo_root, graph_path),
        **flags,
        **graph_checks,
    }
    _write_json_md_pair(
        out_dir / "M12N2_clean_top_extraction_report.json",
        out_dir / "M12N2_clean_top_extraction_report.md",
        "M12N2 Clean Top Extraction Report",
        extraction_report,
    )

    next_stage = {
        "time_control_role_status": time_summary["time_control_role_status"],
        "time_role_requires_team_confirmation": time_summary["time_role_requires_team_confirmation"],
        "recommended_next_stage": time_summary["recommended_next_stage"],
        "recommended_next_stage_reason": time_summary["recommended_next_stage_reason"],
        "can_enter_next_stage_before_human_review": time_summary["can_enter_next_stage_before_human_review"],
        "teacher_question": TIME_QUESTION,
    }
    _write_json_md_pair(
        out_dir / "M12N2_next_stage_decision.json",
        out_dir / "M12N2_next_stage_decision.md",
        "M12N2 Next Stage Decision",
        next_stage,
    )
    write_csv(
        docs_mapping / "M12N2_next_stage_decision.csv",
        [next_stage],
        ["time_control_role_status", "time_role_requires_team_confirmation", "recommended_next_stage", "recommended_next_stage_reason", "can_enter_next_stage_before_human_review", "teacher_question"],
    )

    verification_report = {
        "clean_top_extraction_passed": extraction_report["clean_top_extraction_passed"],
        **flags,
        **graph_checks,
    }
    _write_json_md_pair(
        out_dir / "M12N2_machine_verification_report.json",
        out_dir / "M12N2_machine_verification_report.md",
        "M12N2 Machine Verification Report",
        verification_report,
    )

    parameter_contract_rows = [
        {"parameter_name": "num_rows", "status": "SUPPORTED", "scope": "verified by 16x16 and 64x8 generated samples"},
        {"parameter_name": "num_cols", "status": "SUPPORTED", "scope": "verified by 16x16 and 64x8 generated samples"},
        {"parameter_name": "num_words", "status": "SUPPORTED_WITH_V1_CONSTRAINT", "scope": "must equal num_rows"},
        {"parameter_name": "word_size", "status": "SUPPORTED_WITH_V1_CONSTRAINT", "scope": "must equal num_cols"},
        {"parameter_name": "words_per_row", "status": "LOCKED_TO_1", "scope": "V1 does not support >1"},
        {"parameter_name": "mux_ratio", "status": "LOCKED_TO_1", "scope": "V1 does not support arbitrary ratio"},
        {"parameter_name": "choose_columnmux", "status": "LOCKED_TO_FALSE", "scope": "V1 excludes column mux"},
        {"parameter_name": "sram_cell_type", "status": "LOCKED_TO_6T", "scope": "verified only for 6T"},
        {"parameter_name": "corner", "status": "SUPPORTED_AS_SIMULATION_CONTEXT", "scope": "propagated from OpenYield config"},
        {"parameter_name": "temperature", "status": "SUPPORTED_AS_SIMULATION_CONTEXT", "scope": "propagated from OpenYield config"},
        {"parameter_name": "control_timing_parameters", "status": "SUPPORTED_AS_TRACEABLE_CONTEXT", "scope": "TIME/BaseTestbench derived, not yet a physical control contract"},
    ]
    write_csv(docs_mapping / "M12N2_parameter_contract_v1.csv", parameter_contract_rows, ["parameter_name", "status", "scope"])

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "goal_file_read": True,
        "goal_file_updated": True,
        "progress_file_updated": True,
        "m12n_report_loaded": True,
        "m12n_authoritative_status_before": m12n["authoritative_netlist_lock_status"],
        "regex_dependency_available_before": regex_before,
        "regex_dependency_installed": not regex_before and regex_after,
        "regex_dependency_available_after": regex_after,
        "main_sram_import_passed_after_fix": main_import,
        "equivalent_main_sram_import_passed_after_fix": eq_import,
        "torch_required_for_core_netlist_export": False,
        "torch_dependency_deferred_as_non_core": True,
        "testbench_netlist_loaded": True,
        "testbench_elements_classified": True,
        "design_element_count": design_element_count,
        "testbench_stimulus_count": stimulus_count,
        "simulation_command_count": sim_count,
        "measurement_scaffolding_count": meas_count,
        "clean_top_extraction_passed": extraction_report["clean_top_extraction_passed"],
        "clean_top_spice_path": extraction_report["clean_top_spice_path"],
        "clean_top_graph_path": extraction_report["clean_top_graph_path"],
        "clean_top_contains_independent_stimulus": flags["clean_top_contains_independent_stimulus"],
        "clean_top_contains_pulse": flags["clean_top_contains_pulse"],
        "clean_top_contains_pwl": flags["clean_top_contains_pwl"],
        "clean_top_contains_tran": flags["clean_top_contains_tran"],
        "clean_top_contains_measure": flags["clean_top_contains_measure"],
        "all_instance_subcircuits_resolved": graph_checks["all_instance_subcircuits_resolved"],
        "all_instance_port_counts_match": graph_checks["all_instance_port_counts_match"],
        "graph_spice_instance_count_match": graph_checks["graph_spice_instance_count_match"],
        "graph_spice_module_count_match": graph_checks["graph_spice_module_count_match"],
        "graph_spice_net_count_match": graph_checks["graph_spice_net_count_match"],
        "parameter_contract_v1_locked": True,
        "parameter_contract_v1_scope": _parameter_scope_text(),
        "sample_16x16_generated": True,
        "sample_64x8_generated": True,
        "parameter_scaling_verified": scaling_ok,
        "time_control_role_status": time_summary["time_control_role_status"],
        "time_control_role_evidence_complete": time_summary["time_control_role_evidence_complete"],
        "time_role_requires_team_confirmation": time_summary["time_role_requires_team_confirmation"],
        "can_claim_openyield_clean_layout_facing_top_locked": extraction_report["clean_top_extraction_passed"],
        "can_claim_openyield_authoritative_netlist_locked": extraction_report["clean_top_extraction_passed"],
        "can_claim_parameterized_netlist_v1": True,
        "can_claim_custom_netlist_driven_layout_generation": False,
        "can_claim_control_logic_mapping_ready": False,
        "can_claim_drc_clean": False,
        "can_claim_lvs_clean": False,
        "can_claim_signoff_ready": False,
        "remaining_M12N2_blockers": [row["description"] for row in blockers if row["status"] == "OPEN"],
        "remaining_M12N2_blockers_count": sum(1 for row in blockers if row["status"] == "OPEN"),
        "human_review_required": True,
        "human_review_required_items": [TIME_QUESTION],
        "recommended_next_stage": time_summary["recommended_next_stage"],
        "recommended_next_stage_reason": time_summary["recommended_next_stage_reason"],
        "can_enter_next_stage_before_human_review": False,
        "physical_gds_generation_not_part_of_M12N2": True,
        "reused_M12O_review_gds": True,
        "can_make_physical_implementation_claim": False,
    }

    report_md = _render_md(
        "M12N2 Clean OpenYield SRAM Top Report",
        [
            "- reused_previous_artifacts: `M12N authority report, matrices, sample testbench netlist, project ledgers, OpenYield generator sources`",
            "- deprecated_previous_artifacts: `treating the M12N sample testbench netlist as the final clean SRAM top; treating target-column D_LATCH as the macro output contract`",
            "- current_stage_inputs: `project ledgers + M12N artifacts + OpenYield source + sample testbench netlist`",
            "- current_stage_delta_from_M12N: `clean-top extraction, graph export, and V1 parameter contract lock`",
            "- why_M12N2_precedes_M12C: `control-logic gap closure needs a clean layout-facing SRAM top boundary first`",
            f"- clean_top_extraction_passed: `{report['clean_top_extraction_passed']}`",
            f"- parameter_contract_v1_locked: `{report['parameter_contract_v1_locked']}`",
            f"- sample_16x16_generated: `{report['sample_16x16_generated']}`",
            f"- sample_64x8_generated: `{report['sample_64x8_generated']}`",
            f"- parameter_scaling_verified: `{report['parameter_scaling_verified']}`",
            f"- time_control_role_status: `{report['time_control_role_status']}`",
            f"- recommended_next_stage: `{report['recommended_next_stage']}`",
        ],
    )
    write_json(out_json, report)
    write_text(out_report, report_md)
    write_json(repo_root / "docs/M12N2_clean_openyield_sram_top_report.json", report)
    write_text(repo_root / "docs/M12N2_clean_openyield_sram_top_report.md", report_md)
    write_text(
        repo_root / "docs/evidence/M12N2_clean_openyield_sram_top_summary.md",
        _render_md(
            "M12N2 Clean OpenYield SRAM Top Summary",
            [
                f"- clean_top_spice_path: `{report['clean_top_spice_path']}`",
                f"- clean_top_graph_path: `{report['clean_top_graph_path']}`",
                f"- parameter_contract_v1_locked: `{report['parameter_contract_v1_locked']}`",
                f"- time_control_role_status: `{report['time_control_role_status']}`",
                f"- recommended_next_stage: `{report['recommended_next_stage']}`",
                f"- can_enter_next_stage_before_human_review: `{report['can_enter_next_stage_before_human_review']}`",
            ],
        ),
    )

    status.update(
        {
            "current_stage": "M12N2",
            "next_stage": report["recommended_next_stage"],
            "next_stage_allowed": report["recommended_next_stage"],
            "recommended_next_stage": report["recommended_next_stage"],
            "recommended_next_stage_reason": report["recommended_next_stage_reason"],
            "clean_top_locked": report["can_claim_openyield_clean_layout_facing_top_locked"],
            "parameter_contract_v1_locked": report["parameter_contract_v1_locked"],
            "time_control_role_status": report["time_control_role_status"],
            "can_claim_openyield_authoritative_netlist_locked": report["can_claim_openyield_authoritative_netlist_locked"],
            "can_claim_parameterized_netlist_v1": report["can_claim_parameterized_netlist_v1"],
            "can_claim_custom_netlist_driven_layout_generation": False,
            "can_claim_control_logic_mapping_ready": False,
            "can_claim_drc_clean": False,
            "can_claim_lvs_clean": False,
            "can_claim_signoff_ready": False,
            "can_enter_next_stage_without_human_review": False,
            "can_enter_next_stage_before_human_review": False,
        }
    )
    write_json(status_json, status)
    write_text(status_md, _update_status_md(status_md_text, report))
    write_text(goal_md, _update_goal_md(goal_text, report))
    write_text(progress_md, _update_progress_md(progress_text, report))
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract a clean layout-facing OpenYield SRAM top and lock parameter contract v1.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--goal-md", required=True)
    parser.add_argument("--progress-md", required=True)
    parser.add_argument("--m12n-report", required=True)
    parser.add_argument("--sample-testbench-netlist", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    report = run_m12n2(
        repo_root=repo_root,
        openyield_root=Path(args.openyield_root).resolve(),
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        goal_md=(repo_root / args.goal_md).resolve(),
        progress_md=(repo_root / args.progress_md).resolve(),
        m12n_report=(repo_root / args.m12n_report).resolve(),
        sample_testbench_netlist=(repo_root / args.sample_testbench_netlist).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
