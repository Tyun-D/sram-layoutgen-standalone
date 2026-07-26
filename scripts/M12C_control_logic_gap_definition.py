from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.control_floorplan_gap import build_floorplan_interface_plan
from sram_layoutgen.openyield_adapter.control_gap_review_gds import build_control_gap_review_gds
from sram_layoutgen.openyield_adapter.control_physical_mapper import build_physical_mapping_matrix
from sram_layoutgen.openyield_adapter.operation_topology_compare import build_operation_payload, compare_operation_payloads
from sram_layoutgen.openyield_adapter.time_hierarchy_extractor import extract_time_hierarchy, generate_operation_graph


EXPECTED_SHA = "1c34428d8b913963c4971d093b1a7c2df97a2509"
ALLOWED_NEXT = {
    "M12C2_CONTROL_LOGIC_PHYSICAL_LIBRARY_QUALIFICATION",
    "M12C3_CONTROL_LOGIC_PRIMITIVE_LAYOUT_GENERATOR_PLAN",
    "M12C4_CANONICAL_OPERATION_TOPOLOGY_LOCK",
    "M12C5_REQUEST_CONTROL_LOGIC_REQUIREMENT_CONFIRMATION",
    "M12F_CONTROL_LOGIC_FLOORPLAN_PROTOTYPE_PLAN",
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(_read_text(path))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _write_json(path: Path, payload: Any) -> None:
    _write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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


def _run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True)
    return result.stdout.strip()


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _required_inputs(repo_root: Path) -> list[str]:
    return [
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        "docs/M12N2R_correct_time_role_report.json",
        "docs/M12N2R_correct_time_role_report.md",
        "docs/mapping/M12N2R_time_source_evidence.csv",
        "docs/mapping/M12N2R_time_call_chain.csv",
        "docs/mapping/M12N2R_corrected_external_dependency_blockers.csv",
        "docs/mapping/M12N2R_M12C_entry_gate.csv",
        "docs/M12N2_clean_openyield_sram_top_report.json",
        "outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1.sp",
        "outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_graph.json",
        "outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_16x16.sp",
        "outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_16x16_graph.json",
        "outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_64x8.sp",
        "outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_64x8_graph.json",
        "outputs/M12N2_clean_openyield_sram_top/current_supported_config/OPENYIELD_SRAM_SPEC_V1.schema.json",
        "docs/mapping/M12N2_clean_top_modules.csv",
        "docs/mapping/M12N2_clean_top_instances.csv",
        "docs/mapping/M12N2_clean_top_nets.csv",
        "docs/mapping/M12N2_clean_top_pins.csv",
        "docs/M12O_openram_openyield_gap_audit_report.json",
        "docs/mapping/M12O_three_way_module_gap_matrix.csv",
        "docs/mapping/M12O_configurable_sram_spec_plan.csv",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_openram_vs_layoutgen_gap_review.gds",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_openram_vs_layoutgen_gap_clean_review.gds",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_openram_vs_layoutgen_gap_annotated_debug.gds",
        "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds",
        "outputs/openyield_module_gds",
        "external_references/openram_full_reference",
    ]


def _build_blockers(
    *,
    topology: dict[str, Any],
    mapping: dict[str, Any],
    floorplan: dict[str, Any],
) -> list[dict[str, Any]]:
    blockers = [
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
            "description": "Control-logic physical implementation has been defined but is not implemented.",
            "machine_solvable": False,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": False,
            "requires_external_tool": False,
            "blocks_which_stage": "control-logic physical implementation",
            "resolution_action": "Advance to the next control-logic qualification/planning stage; do not claim physical-ready before implementation exists.",
            "status": "DEFINED_NOT_IMPLEMENTED",
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
        {
            "blocker_id": "M12C-B08",
            "description": "Existing OpenYield control-logic candidate GDS files are metadata-rich candidates, not qualified final implementations.",
            "machine_solvable": True,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": False,
            "requires_external_tool": False,
            "blocks_which_stage": "M12C2_CONTROL_LOGIC_PHYSICAL_LIBRARY_QUALIFICATION",
            "resolution_action": "Qualify bbox/pin/rail metadata and verify that each candidate is a real reusable physical unit rather than a debug-only composition.",
            "status": "OPEN",
        },
        {
            "blocker_id": "M12C-B09",
            "description": "Pin and rail metadata coverage is incomplete across the full TIME primitive hierarchy.",
            "machine_solvable": True,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": False,
            "requires_external_tool": False,
            "blocks_which_stage": "M12C2_CONTROL_LOGIC_PHYSICAL_LIBRARY_QUALIFICATION",
            "resolution_action": "Run targeted metadata qualification on candidate composites and primitive hardcells.",
            "status": "OPEN",
        },
        {
            "blocker_id": "M12C-B10",
            "description": "Candidate control region insertion is expected to affect or at least challenge the current top-level bbox contract.",
            "machine_solvable": False,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": False,
            "requires_external_tool": False,
            "blocks_which_stage": "M12F_CONTROL_LOGIC_FLOORPLAN_PROTOTYPE_PLAN",
            "resolution_action": "Prototype the control-region floorplan and determine whether bbox expansion can be avoided.",
            "status": "OPEN" if floorplan["top_bbox_change_expected"] else "CLOSED",
        },
        {
            "blocker_id": "M12C-B11",
            "description": "OpenRAM control logic remains reference-only and cannot be directly reused as final OpenYield implementation.",
            "machine_solvable": False,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": False,
            "requires_external_tool": False,
            "blocks_which_stage": "control-logic implementation proof",
            "resolution_action": "Use OpenRAM only as floorplan/interface reference and keep OpenYield/layoutgen implementation paths separate.",
            "status": "OPEN",
        },
        {
            "blocker_id": "M12C-B12",
            "description": "Several transistor-level primitives still lack a parameterized physical generator plan.",
            "machine_solvable": True,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": False,
            "requires_external_tool": False,
            "blocks_which_stage": "M12C3_CONTROL_LOGIC_PRIMITIVE_LAYOUT_GENERATOR_PLAN",
            "resolution_action": "Define a parameterized transistor-level primitive layout generator or a legal wrapper path for the missing primitives.",
            "status": "OPEN" if mapping["parameterized_transistor_layout_required_count"] > 0 else "CLOSED",
        },
        {
            "blocker_id": "M12C-B13",
            "description": "FreePDK45 physical tech rule binding is still not connected to the OpenYield control-logic parameter contract.",
            "machine_solvable": False,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": True,
            "requires_external_tool": False,
            "blocks_which_stage": "technology-aware control-logic implementation",
            "resolution_action": "Bind control-logic primitive generation and qualification to an explicit physical tech abstraction.",
            "status": "OPEN",
        },
        {
            "blocker_id": "M12C-B14",
            "description": "Legal provenance and qualification boundaries for direct standard-cell-style reuse remain incomplete.",
            "machine_solvable": False,
            "requires_user_action": False,
            "requires_teacher_confirmation": False,
            "requires_external_file": False,
            "requires_external_tool": False,
            "blocks_which_stage": "reuse qualification",
            "resolution_action": "Keep existing layoutgen/OpenYield hardcells in qualification-only scope until reuse boundaries are explicitly validated.",
            "status": "OPEN",
        },
    ]
    if topology["operation_topology_requires_team_confirmation"]:
        blockers.append(
            {
                "blocker_id": "M12C-B15",
                "description": "The machine evidence cannot lock one canonical control-logic topology across read/write/read&write.",
                "machine_solvable": False,
                "requires_user_action": True,
                "requires_teacher_confirmation": True,
                "requires_external_file": False,
                "requires_external_tool": False,
                "blocks_which_stage": "physical implementation start",
                "resolution_action": "Ask whether the final macro should implement a read&write superset or a different canonical control-logic contract.",
                "status": "OPEN",
            }
        )
    return blockers


def _next_stage(topology: dict[str, Any], mapping: dict[str, Any], floorplan: dict[str, Any]) -> tuple[str, str]:
    if topology["operation_topology_requires_team_confirmation"]:
        return (
            "M12C5_REQUEST_CONTROL_LOGIC_REQUIREMENT_CONFIRMATION",
            "Machine evidence is insufficient to lock the canonical control-logic hardware topology without external confirmation.",
        )
    if not topology["canonical_operation_topology_locked"]:
        return (
            "M12C4_CANONICAL_OPERATION_TOPOLOGY_LOCK",
            "Operation-dependent hardware views still need one more machine-first topology lock step before physical qualification can proceed.",
        )
    if mapping["physical_ready_for_qualification_count"] > 0:
        return (
            "M12C2_CONTROL_LOGIC_PHYSICAL_LIBRARY_QUALIFICATION",
            "The operation topology is locked and there are existing candidate primitives/composites with metadata, so the next step should qualify bbox/pin/rail realism and reuse boundaries.",
        )
    if mapping["parameterized_transistor_layout_required_count"] > 0:
        return (
            "M12C3_CONTROL_LOGIC_PRIMITIVE_LAYOUT_GENERATOR_PLAN",
            "The topology is locked but too many primitives still lack reusable GDS candidates, so a primitive-generator plan is needed first.",
        )
    if floorplan["candidate_control_region_defined"]:
        return (
            "M12F_CONTROL_LOGIC_FLOORPLAN_PROTOTYPE_PLAN",
            "The topology and interface region are defined well enough to plan a floorplan prototype without claiming implementation.",
        )
    return (
        "M12C4_CANONICAL_OPERATION_TOPOLOGY_LOCK",
        "The next step remains a topology/floorplan lock because the physical implementation boundary is not yet qualification-ready.",
    )


def _update_status_md(text: str, report: dict[str, Any]) -> str:
    text = _replace_section(
        text,
        "## 2. Current Stage",
        [
            "- current_stage: `M12C`",
            f"- next_stage: `{report['recommended_next_stage']}`",
            f"- human_klayout_review_required_every_stage: `{report['human_review_required']}`",
            f"- can_enter_next_stage_without_human_review: `{report['can_enter_next_stage_before_human_review']}`",
            f"- next_stage_allowed: `{report['recommended_next_stage']}`",
        ],
    )
    return _replace_section(
        text,
        "## 6. M12C Control Logic Gap Definition Result",
        [
            f"- m12n2r_gate_passed: `{report['m12n2r_gate_passed']}`",
            f"- openyield_sha: `{report['openyield_sha']}`",
            f"- operation_topology_status: `{report['operation_topology_status']}`",
            f"- canonical_physical_operation_topology: `{report['canonical_physical_operation_topology']}`",
            f"- canonical_operation_topology_locked: `{report['canonical_operation_topology_locked']}`",
            f"- physical_module_total_count: `{report['physical_module_total_count']}`",
            f"- physical_ready_for_qualification_count: `{report['physical_ready_for_qualification_count']}`",
            f"- physical_partial_count: `{report['physical_partial_count']}`",
            f"- physical_reference_only_count: `{report['physical_reference_only_count']}`",
            f"- physical_missing_count: `{report['physical_missing_count']}`",
            f"- bbox_metadata_coverage: `{report['bbox_metadata_coverage']}`",
            f"- pin_geometry_coverage: `{report['pin_geometry_coverage']}`",
            f"- power_rail_metadata_coverage: `{report['power_rail_metadata_coverage']}`",
            f"- top_bbox_change_expected: `{report['top_bbox_change_expected']}`",
            f"- recommended_next_stage: `{report['recommended_next_stage']}`",
            f"- human_review_required: `{report['human_review_required']}`",
        ],
    )


def _update_goal_md(text: str, report: dict[str, Any]) -> str:
    return _replace_section(
        text,
        "## Current Control Logic Gap Definition Stage",
        [
            "- M12C 只定义 OpenYield TIME / CONTROL_LOGIC 从网表到物理实现的缺口与映射计划，不实际完成新的 CONTROL_LOGIC 版图。",
            f"- M12N2R gate 已通过：`{report['m12n2r_gate_passed']}`；TIME 角色：`ON_CHIP_CONTROL_LOGIC`。",
            f"- operation 拓扑审计结果：`{report['operation_topology_status']}`；canonical topology：`{report['canonical_physical_operation_topology']}`。",
            f"- 现有 physical cells 已盘点：ready=`{report['physical_ready_for_qualification_count']}`，partial=`{report['physical_partial_count']}`，reference_only=`{report['physical_reference_only_count']}`，missing=`{report['physical_missing_count']}`。",
            f"- 当前不能 claim CONTROL_LOGIC physical ready：`{report['can_claim_control_logic_physical_ready']}`；custom netlist-driven layout generation：`{report['can_claim_custom_netlist_driven_layout_generation']}`。",
            f"- 当前推荐下一阶段：`{report['recommended_next_stage']}`。",
        ],
    )


def _update_progress_md(text: str, report: dict[str, Any]) -> str:
    return _replace_section(
        text,
        "## M12C Control Logic Gap Definition",
        [
            f"- m12n2r_gate_passed: `{report['m12n2r_gate_passed']}`",
            f"- openyield_version_verified: `{report['openyield_version_verified']}`",
            f"- openyield_sha: `{report['openyield_sha']}`",
            f"- time_hierarchy_extracted: `{report['time_hierarchy_extracted']}`",
            f"- time_module_count: `{report['time_module_count']}`",
            f"- time_primitive_count: `{report['time_primitive_count']}`",
            f"- time_instance_count_for_reference_config: `{report['time_instance_count_for_reference_config']}`",
            f"- operation_topology_status: `{report['operation_topology_status']}`",
            f"- canonical_physical_operation_topology: `{report['canonical_physical_operation_topology']}`",
            f"- canonical_operation_topology_locked: `{report['canonical_operation_topology_locked']}`",
            f"- physical_module_total_count: `{report['physical_module_total_count']}`",
            f"- physical_ready_for_qualification_count: `{report['physical_ready_for_qualification_count']}`",
            f"- physical_partial_count: `{report['physical_partial_count']}`",
            f"- physical_reference_only_count: `{report['physical_reference_only_count']}`",
            f"- physical_missing_count: `{report['physical_missing_count']}`",
            f"- parameterized_transistor_layout_required_count: `{report['parameterized_transistor_layout_required_count']}`",
            f"- bbox_metadata_coverage: `{report['bbox_metadata_coverage']}`",
            f"- pin_geometry_coverage: `{report['pin_geometry_coverage']}`",
            f"- power_rail_metadata_coverage: `{report['power_rail_metadata_coverage']}`",
            f"- floorplan_interface_plan_generated: `{report['floorplan_interface_plan_generated']}`",
            f"- candidate_control_region_defined: `{report['candidate_control_region_defined']}`",
            f"- top_bbox_change_expected: `{report['top_bbox_change_expected']}`",
            f"- review_gds_generated: `{report['review_gds_generated']}`",
            f"- review_gds_parsed: `{report['review_gds_parsed']}`",
            f"- recommended_next_stage: `{report['recommended_next_stage']}`",
            f"- remaining_M12C_blockers_count: `{report['remaining_M12C_blockers_count']}`",
            f"- human_review_required: `{report['human_review_required']}`",
            f"- can_enter_next_stage_before_human_review: `{report['can_enter_next_stage_before_human_review']}`",
            "- note: `M12C is definition-only. It does not complete control-logic layout, does not replace new SRAM modules, and does not reopen DRC/LVS/signoff claims.`",
        ],
    )


def run_m12c(
    *,
    repo_root: Path,
    openyield_root: Path,
    openram_root: Path,
    openram_reference_dir: Path,
    status_md: Path,
    status_json: Path,
    goal_md: Path,
    progress_md: Path,
    m12n2r_report: Path,
    m12n2_clean_report: Path,
    clean_top_graph: Path,
    layoutgen_golden: Path,
    openyield_module_gds_dir: Path,
    m12o_gap_matrix: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_mapping = repo_root / "docs" / "mapping"
    docs_evidence = repo_root / "docs" / "evidence"
    docs_mapping.mkdir(parents=True, exist_ok=True)
    docs_evidence.mkdir(parents=True, exist_ok=True)

    status_md_text = _read_text(status_md)
    status = _read_json(status_json)
    goal_text = _read_text(goal_md)
    progress_text = _read_text(progress_md)
    m12n2r = _read_json(m12n2r_report)
    _ = _read_json(m12n2_clean_report)
    reference_graph = _read_json(clean_top_graph)

    sha = _run_git(["git", "rev-parse", "HEAD"], openyield_root)
    openyield_version_verified = sha == EXPECTED_SHA
    m12n2r_gate_passed = bool(m12n2r["can_enter_M12C_after_this_gate"])

    operation_results = {
        op: generate_operation_graph(
            repo_root=repo_root,
            openyield_root=openyield_root,
            operation=op,
            num_rows=16,
            num_cols=16,
            choose_columnmux=False,
            sim_path=out_dir / f"sim_{op.replace('&', '_')}",
        )
        for op in ("read", "write", "read&write")
    }
    op_payloads = {op: build_operation_payload(result) for op, result in operation_results.items()}
    topology = compare_operation_payloads(op_payloads)

    hierarchy = extract_time_hierarchy(
        openyield_root=openyield_root,
        reference_graph=operation_results["read&write"]["graph"],
        operation_graphs=operation_results,
        num_rows=16,
        num_cols=16,
    )

    mapping = build_physical_mapping_matrix(
        hierarchy_rows=hierarchy["rows"],
        openyield_module_gds_dir=openyield_module_gds_dir,
        repo_root=repo_root,
        openram_gap_matrix=m12o_gap_matrix,
    )
    openram_reference_gds = next(openram_reference_dir.rglob("*.gds"))
    floorplan = build_floorplan_interface_plan(
        layoutgen_golden=layoutgen_golden,
        openram_reference_gds=openram_reference_gds,
        mapping_summary=mapping,
    )
    review = build_control_gap_review_gds(
        layoutgen_golden=layoutgen_golden,
        openram_reference_gds=openram_reference_gds,
        openyield_module_gds_dir=openyield_module_gds_dir,
        out_review_gds=out_dir / "M12C_control_logic_gap_review.gds",
        out_clean_gds=out_dir / "M12C_control_logic_gap_clean_review.gds",
        out_debug_gds=out_dir / "M12C_control_logic_gap_annotated_debug.gds",
        floorplan_plan=floorplan,
    )

    blockers = _build_blockers(topology=topology, mapping=mapping, floorplan=floorplan)
    human_items = list(topology["human_review_required_items"])
    next_stage, next_stage_reason = _next_stage(topology, mapping, floorplan)
    if next_stage not in ALLOWED_NEXT:
        raise ValueError(f"Unexpected next stage: {next_stage}")
    human_review_required = bool(human_items)
    can_enter_next = not human_review_required

    time_inventory_fields = [
        "module_name",
        "source_file",
        "source_class",
        "parent_module",
        "pin_order",
        "pin_roles",
        "instance_count",
        "instance_count_formula",
        "parameter_dependencies",
        "operation_dependencies",
        "row_dependencies",
        "column_dependencies",
        "drive_scale_dependencies",
        "child_modules",
        "consumer_modules",
        "control_signals_generated",
    ]
    _write_csv(out_dir / "M12C_time_hierarchy_inventory.csv", hierarchy["rows"], time_inventory_fields)
    _write_text(
        out_dir / "M12C_time_hierarchy_inventory.md",
        _render_md("M12C Time Hierarchy Inventory", [f"- {row['module_name']}: `{row['instance_count_formula']}` | child_modules=`{row['child_modules']}` | consumer_modules=`{row['consumer_modules']}`" for row in hierarchy["rows"]]),
    )
    _write_csv(docs_mapping / "M12C_time_hierarchy_inventory.csv", hierarchy["rows"], time_inventory_fields)

    for op, payload in op_payloads.items():
        target = out_dir / f"M12C_operation_topology_{op.replace('&', '_').replace('read_write', 'read_write')}.json"
        if op == "read&write":
            target = out_dir / "M12C_operation_topology_read_write.json"
        elif op == "read":
            target = out_dir / "M12C_operation_topology_read.json"
        elif op == "write":
            target = out_dir / "M12C_operation_topology_write.json"
        _write_json(target, payload)
    diff_fields = ["diff_category", "read_value", "write_value", "read_write_value", "read_equals_write", "read_equals_read_write", "write_equals_read_write"]
    _write_csv(out_dir / "M12C_operation_topology_diff.csv", topology["diff_rows"], diff_fields)
    _write_text(
        out_dir / "M12C_operation_topology_diff.md",
        _render_md("M12C Operation Topology Diff", [f"- {row['diff_category']}: read==write `{row['read_equals_write']}`, read==read&write `{row['read_equals_read_write']}`, write==read&write `{row['write_equals_read_write']}`" for row in topology["diff_rows"]]),
    )
    _write_csv(docs_mapping / "M12C_operation_topology_diff.csv", topology["diff_rows"], diff_fields)

    mapping_fields = [
        "logical_module",
        "source_file",
        "source_class",
        "parent_path",
        "logical_function",
        "pin_names",
        "pin_count",
        "instance_count_or_formula",
        "parameter_dependencies",
        "operation_dependencies",
        "existing_openyield_gds_found",
        "existing_openyield_gds_path",
        "existing_layoutgen_cell_found",
        "existing_layoutgen_cell_name",
        "existing_openram_reference_found",
        "existing_openram_cell_or_region",
        "bbox_metadata_available",
        "pin_geometry_available",
        "power_rail_metadata_available",
        "layer_metadata_available",
        "physical_strategy",
        "physical_readiness",
        "blocking_reason",
        "recommended_action",
        "requires_human_review",
    ]
    _write_csv(out_dir / "M12C_control_logic_physical_mapping_matrix.csv", mapping["rows"], mapping_fields)
    _write_text(
        out_dir / "M12C_control_logic_physical_mapping_matrix.md",
        _render_md("M12C Control Logic Physical Mapping Matrix", [f"- {row['logical_module']}: `{row['physical_strategy']}` | readiness=`{row['physical_readiness']}` | layoutgen=`{row['existing_layoutgen_cell_name']}` | openyield_gds=`{row['existing_openyield_gds_found']}`" for row in mapping["rows"]]),
    )
    _write_csv(docs_mapping / "M12C_control_logic_physical_mapping_matrix.csv", mapping["rows"], mapping_fields)

    parameter_rows = [
        {
            "parameter": "num_rows",
            "source_location": "time_generate.py::TIME/ADDR_DFF/pdrive2_for_pre",
            "logical_impact": "address width and precharge drive scaling",
            "instance_count_impact": "ADDR_DFF DFF count scales with ceil(log2(num_rows))",
            "pin_count_impact": "A[*]/A_dff[*] pin expansion",
            "bbox_impact": "likely yes",
            "transistor_size_impact": "precharge buffer scaling indirectly depends on rows",
            "routing_impact": "decoder/control adjacency width changes",
            "power_impact": "buffer sizing affects local dynamic power",
            "requires_regeneration": True,
            "can_use_fixed_hardmacro": False,
            "supported_in_v1": True,
            "blocking_level": "HIGH",
        },
        {
            "parameter": "num_cols",
            "source_location": "time_generate.py::TIME/DATA_DFF/AND3/pdrive/pdrive2_for_pre",
            "logical_impact": "DATA_DFF width and w_en/precharge scaling",
            "instance_count_impact": "DATA_DFF DFF count scales with num_cols",
            "pin_count_impact": "DIN[*]/DIN_dff[*] expansion",
            "bbox_impact": "likely yes",
            "transistor_size_impact": "w_en_scale and pre_drive_scale depend on num_cols",
            "routing_impact": "write and enable fanout width changes",
            "power_impact": "larger load and drive strength",
            "requires_regeneration": True,
            "can_use_fixed_hardmacro": False,
            "supported_in_v1": True,
            "blocking_level": "HIGH",
        },
        {
            "parameter": "operation",
            "source_location": "time_generate.py::TIME and sram_6t_core_testbench.py::create_testbench",
            "logical_impact": "controls DATA_DFF presence and read/write periphery inclusion",
            "instance_count_impact": "changes DATA_DFF, SENSEAMP, WRITEDRIVER presence",
            "pin_count_impact": "changes DIN[*] and SA_Q[*]/SA_QB[*] exposure in extracted clean top",
            "bbox_impact": "yes for extracted view",
            "transistor_size_impact": "clock buffering and write path scaling differ with data-path presence",
            "routing_impact": "changes write-data and sense-output channels",
            "power_impact": "changes enabled paths",
            "requires_regeneration": True,
            "can_use_fixed_hardmacro": False,
            "supported_in_v1": True,
            "blocking_level": "HIGH",
        },
        {
            "parameter": "drive_scale",
            "source_location": "time_generate.py::pdrive/pdrive2_for_pre",
            "logical_impact": "none",
            "instance_count_impact": "none",
            "pin_count_impact": "none",
            "bbox_impact": "yes",
            "transistor_size_impact": "yes",
            "routing_impact": "moderate",
            "power_impact": "moderate",
            "requires_regeneration": True,
            "can_use_fixed_hardmacro": False,
            "supported_in_v1": False,
            "blocking_level": "MEDIUM",
        },
        {
            "parameter": "delay_chain_stages",
            "source_location": "time_generate.py::WenDelayChain",
            "logical_impact": "special write-delay topology only",
            "instance_count_impact": "yes",
            "pin_count_impact": "no",
            "bbox_impact": "yes",
            "transistor_size_impact": "indirect",
            "routing_impact": "moderate",
            "power_impact": "moderate",
            "requires_regeneration": True,
            "can_use_fixed_hardmacro": False,
            "supported_in_v1": False,
            "blocking_level": "MEDIUM",
        },
        {
            "parameter": "transistor_width",
            "source_location": "time_generate.py + standard_cell.py primitives",
            "logical_impact": "none",
            "instance_count_impact": "none",
            "pin_count_impact": "none",
            "bbox_impact": "yes",
            "transistor_size_impact": "yes",
            "routing_impact": "yes",
            "power_impact": "yes",
            "requires_regeneration": True,
            "can_use_fixed_hardmacro": False,
            "supported_in_v1": False,
            "blocking_level": "HIGH",
        },
        {
            "parameter": "corner_tech",
            "source_location": "global.yaml + physical tech binding gap",
            "logical_impact": "simulation-only today",
            "instance_count_impact": "none",
            "pin_count_impact": "none",
            "bbox_impact": "potentially yes once physically bound",
            "transistor_size_impact": "potentially yes",
            "routing_impact": "potentially yes",
            "power_impact": "potentially yes",
            "requires_regeneration": True,
            "can_use_fixed_hardmacro": False,
            "supported_in_v1": False,
            "blocking_level": "HIGH",
        },
    ]
    param_fields = [
        "parameter",
        "source_location",
        "logical_impact",
        "instance_count_impact",
        "pin_count_impact",
        "bbox_impact",
        "transistor_size_impact",
        "routing_impact",
        "power_impact",
        "requires_regeneration",
        "can_use_fixed_hardmacro",
        "supported_in_v1",
        "blocking_level",
    ]
    _write_csv(out_dir / "M12C_control_logic_parameter_physical_impact.csv", parameter_rows, param_fields)
    _write_text(
        out_dir / "M12C_control_logic_parameter_physical_impact.md",
        _render_md("M12C Control Logic Parameter Physical Impact", [f"- {row['parameter']}: requires_regeneration=`{row['requires_regeneration']}` | fixed_hardmacro=`{row['can_use_fixed_hardmacro']}` | blocking=`{row['blocking_level']}`" for row in parameter_rows]),
    )
    _write_csv(docs_mapping / "M12C_control_logic_parameter_physical_impact.csv", parameter_rows, param_fields)

    _write_json(out_dir / "M12C_control_logic_floorplan_interface_plan.json", floorplan)
    _write_text(
        out_dir / "M12C_control_logic_floorplan_interface_plan.md",
        _render_md("M12C Control Logic Floorplan Interface Plan", [f"- placement_strategy: `{floorplan['candidate_region']['placement_strategy']}`", f"- top_bbox_change_expected: `{floorplan['top_bbox_change_expected']}`", f"- decoder_adjacency: `{floorplan['decoder_adjacency']}`", f"- wordline_driver_adjacency: `{floorplan['wordline_driver_adjacency']}`"]),
    )
    _write_csv(out_dir / "M12C_control_logic_interface_nets.csv", floorplan["interface_nets"], ["net_name", "role", "direction", "consumer_or_producer", "adjacent_module"])
    _write_csv(docs_mapping / "M12C_control_logic_interface_nets.csv", floorplan["interface_nets"], ["net_name", "role", "direction", "consumer_or_producer", "adjacent_module"])

    blocker_fields = [
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
    ]
    _write_csv(out_dir / "M12C_external_dependency_blockers.csv", blockers, blocker_fields)
    _write_text(
        out_dir / "M12C_external_dependency_blockers.md",
        _render_md("M12C External Dependency Blockers", [f"- {row['blocker_id']}: `{row['status']}` | {row['description']}" for row in blockers]),
    )
    _write_csv(docs_mapping / "M12C_external_dependency_blockers.csv", blockers, blocker_fields)

    machine_verification = {
        "openyield_version_verified": openyield_version_verified,
        "time_hierarchy_extracted": True,
        "read_topology_generated": True,
        "write_topology_generated": True,
        "read_write_topology_generated": True,
        "operation_topology_diff_generated": True,
        "review_gds_generated": review["review_gds_generated"],
        "review_gds_parsed": review["review_gds_parsed"],
    }
    _write_json(out_dir / "M12C_machine_verification_report.json", machine_verification)
    _write_text(
        out_dir / "M12C_machine_verification_report.md",
        _render_md("M12C Machine Verification Report", [f"- {key}: `{value}`" for key, value in machine_verification.items()]),
    )
    _write_text(
        out_dir / "M12C_human_review_required_items.md",
        _render_md("M12C Human Review Required Items", ["- none"] if not human_items else [f"- {item}" for item in human_items]),
    )

    next_stage_payload = {
        "recommended_next_stage": next_stage,
        "recommended_next_stage_reason": next_stage_reason,
        "operation_topology_status": topology["operation_topology_status"],
        "canonical_physical_operation_topology": topology["canonical_physical_operation_topology"],
        "canonical_operation_topology_locked": topology["canonical_operation_topology_locked"],
        "human_review_required": human_review_required,
        "can_enter_next_stage_before_human_review": can_enter_next,
    }
    _write_json(out_dir / "M12C_next_stage_decision.json", next_stage_payload)
    _write_text(
        out_dir / "M12C_next_stage_decision.md",
        _render_md("M12C Next Stage Decision", [f"- {key}: `{value}`" for key, value in next_stage_payload.items()]),
    )
    _write_csv(docs_mapping / "M12C_next_stage_decision.csv", [next_stage_payload], list(next_stage_payload.keys()))

    remaining_blockers = [row["description"] for row in blockers if row["status"] in {"OPEN", "DEFINED_NOT_IMPLEMENTED"}]
    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "goal_file_read": True,
        "goal_file_updated": True,
        "progress_file_updated": True,
        "m12n2r_report_loaded": True,
        "m12n2r_gate_passed": m12n2r_gate_passed,
        "can_enter_M12C_from_M12N2R": bool(m12n2r["can_enter_M12C_after_this_gate"]),
        "reused_previous_artifacts": _required_inputs(repo_root),
        "deprecated_previous_artifacts": [
            "Treating OpenYield control-logic candidate GDS as final implementation-ready cells",
            "Treating OpenRAM control-logic geometry as directly reusable OpenYield implementation",
            "Starting control-logic physical implementation before operation topology and mapping are locked",
        ],
        "current_stage_inputs": _required_inputs(repo_root) + [str(openyield_root), str(openram_root)],
        "current_stage_delta_from_M12N2R": "M12C moves from role correction to explicit control-logic hierarchy extraction, operation-topology comparison, physical mapping, floorplan interface definition, and review-GDS generation.",
        "why_M12C_is_definition_only": "The current evidence can lock source hierarchy and candidate physical strategies, but it cannot yet prove qualified reusable control-logic layout or safe top-level assembly.",
        "why_physical_implementation_cannot_start_before_M12C_gate": "Operation-dependent topology, primitive reuse boundaries, bbox/pin/rail coverage, and floorplan interface constraints must be locked first to avoid implementing the wrong control block.",
        "openyield_version_verified": openyield_version_verified,
        "openyield_sha": sha,
        "time_hierarchy_extracted": True,
        "time_module_count": hierarchy["module_count"],
        "time_primitive_count": hierarchy["primitive_count"],
        "time_instance_count_for_reference_config": hierarchy["instance_count_for_reference_config"],
        "read_topology_generated": True,
        "write_topology_generated": True,
        "read_write_topology_generated": True,
        "operation_topology_diff_generated": True,
        "operation_topology_status": topology["operation_topology_status"],
        "canonical_physical_operation_topology": topology["canonical_physical_operation_topology"],
        "canonical_operation_topology_locked": topology["canonical_operation_topology_locked"],
        "operation_topology_requires_team_confirmation": topology["operation_topology_requires_team_confirmation"],
        "physical_mapping_matrix_generated": True,
        **{k: mapping[k] for k in [
            "physical_module_total_count",
            "physical_ready_for_qualification_count",
            "physical_partial_count",
            "physical_reference_only_count",
            "physical_missing_count",
            "parameterized_transistor_layout_required_count",
            "existing_openyield_control_primitive_gds_count",
            "existing_layoutgen_control_cell_count",
            "openram_control_reference_region_found",
            "bbox_metadata_coverage",
            "pin_geometry_coverage",
            "power_rail_metadata_coverage",
            "layer_metadata_coverage",
        ]},
        "floorplan_interface_plan_generated": True,
        "candidate_control_region_defined": floorplan["candidate_control_region_defined"],
        "top_bbox_change_expected": floorplan["top_bbox_change_expected"],
        "routing_channel_requirement_defined": floorplan["routing_channel_requirement_defined"],
        "power_interface_requirement_defined": floorplan["power_interface_requirement_defined"],
        "review_gds_generated": review["review_gds_generated"],
        "review_gds_parsed": review["review_gds_parsed"],
        "clean_review_gds_path": review["clean_review_gds_path"],
        "annotated_debug_gds_path": review["annotated_debug_gds_path"],
        "external_dependency_blockers_count": len(blockers),
        "human_review_required_item_count": len(human_items),
        "human_review_required_items": human_items,
        "can_claim_control_logic_source_locked": True,
        "can_claim_control_logic_mapping_ready": False,
        "can_claim_control_logic_physical_ready": False,
        "can_claim_custom_netlist_driven_layout_generation": False,
        "can_claim_routing_clean": False,
        "can_claim_power_clean": False,
        "can_claim_drc_clean": False,
        "can_claim_lvs_clean": False,
        "can_claim_signoff_ready": False,
        "recommended_next_stage": next_stage,
        "recommended_next_stage_reason": next_stage_reason,
        "remaining_M12C_blockers": remaining_blockers,
        "remaining_M12C_blockers_count": len(remaining_blockers),
        "human_review_required": human_review_required,
        "can_enter_next_stage_before_human_review": can_enter_next,
    }

    _write_json(out_json, report)
    _write_text(
        out_report,
        _render_md(
            "M12C Control Logic Gap Definition Report",
            [
                f"- current_stage_delta_from_M12N2R: `{report['current_stage_delta_from_M12N2R']}`",
                f"- why_M12C_is_definition_only: `{report['why_M12C_is_definition_only']}`",
                f"- why_physical_implementation_cannot_start_before_M12C_gate: `{report['why_physical_implementation_cannot_start_before_M12C_gate']}`",
                f"- operation_topology_status: `{report['operation_topology_status']}`",
                f"- canonical_physical_operation_topology: `{report['canonical_physical_operation_topology']}`",
                f"- physical_ready_for_qualification_count: `{report['physical_ready_for_qualification_count']}`",
                f"- physical_partial_count: `{report['physical_partial_count']}`",
                f"- physical_reference_only_count: `{report['physical_reference_only_count']}`",
                f"- physical_missing_count: `{report['physical_missing_count']}`",
                f"- top_bbox_change_expected: `{report['top_bbox_change_expected']}`",
                f"- recommended_next_stage: `{report['recommended_next_stage']}`",
                f"- can_enter_next_stage_before_human_review: `{report['can_enter_next_stage_before_human_review']}`",
            ],
        ),
    )
    _write_json(repo_root / "docs/M12C_control_logic_gap_definition_report.json", report)
    _write_text(repo_root / "docs/M12C_control_logic_gap_definition_report.md", _read_text(out_report))
    _write_text(
        repo_root / "docs/evidence/M12C_control_logic_gap_definition_summary.md",
        _render_md(
            "M12C Control Logic Gap Definition Summary",
            [
                f"- openyield_sha: `{sha}`",
                f"- operation_topology_status: `{report['operation_topology_status']}`",
                f"- canonical_physical_operation_topology: `{report['canonical_physical_operation_topology']}`",
                f"- physical_module_total_count: `{report['physical_module_total_count']}`",
                f"- physical_ready_for_qualification_count: `{report['physical_ready_for_qualification_count']}`",
                f"- top_bbox_change_expected: `{report['top_bbox_change_expected']}`",
                f"- recommended_next_stage: `{report['recommended_next_stage']}`",
            ],
        ),
    )

    status.update(
        {
            "current_stage": "M12C",
            "next_stage": next_stage,
            "next_stage_allowed": next_stage,
            "recommended_next_stage": next_stage,
            "recommended_next_stage_reason": next_stage_reason,
            "m12n2r_gate_passed": m12n2r_gate_passed,
            "time_control_role_status": "ON_CHIP_CONTROL_LOGIC",
            "operation_topology_status": topology["operation_topology_status"],
            "canonical_physical_operation_topology": topology["canonical_physical_operation_topology"],
            "canonical_operation_topology_locked": topology["canonical_operation_topology_locked"],
            "physical_module_total_count": mapping["physical_module_total_count"],
            "physical_ready_for_qualification_count": mapping["physical_ready_for_qualification_count"],
            "physical_partial_count": mapping["physical_partial_count"],
            "physical_reference_only_count": mapping["physical_reference_only_count"],
            "physical_missing_count": mapping["physical_missing_count"],
            "bbox_metadata_coverage": mapping["bbox_metadata_coverage"],
            "pin_geometry_coverage": mapping["pin_geometry_coverage"],
            "power_rail_metadata_coverage": mapping["power_rail_metadata_coverage"],
            "candidate_control_region_defined": floorplan["candidate_control_region_defined"],
            "top_bbox_change_expected": floorplan["top_bbox_change_expected"],
            "openyield_control_logic_physical_implementation_ready": False,
            "can_claim_control_logic_source_locked": True,
            "can_claim_control_logic_mapping_ready": False,
            "can_claim_control_logic_physical_ready": False,
            "can_claim_custom_netlist_driven_layout_generation": False,
            "can_claim_drc_clean": False,
            "can_claim_lvs_clean": False,
            "can_claim_signoff_ready": False,
            "human_klayout_review_required_every_stage": human_review_required,
            "can_enter_next_stage_without_human_review": can_enter_next,
            "can_enter_next_stage_before_human_review": can_enter_next,
        }
    )
    _write_json(status_json, status)
    _write_text(status_md, _update_status_md(status_md_text, report))
    _write_text(goal_md, _update_goal_md(goal_text, report))
    _write_text(progress_md, _update_progress_md(progress_text, report))
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Define the OpenYield TIME/control-logic physical implementation gap and mapping plan.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--openram-root", required=True)
    parser.add_argument("--openram-reference-dir", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--goal-md", required=True)
    parser.add_argument("--progress-md", required=True)
    parser.add_argument("--m12n2r-report", required=True)
    parser.add_argument("--m12n2-clean-report", required=True)
    parser.add_argument("--clean-top-graph", required=True)
    parser.add_argument("--layoutgen-golden", required=True)
    parser.add_argument("--openyield-module-gds-dir", required=True)
    parser.add_argument("--m12o-gap-matrix", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    report = run_m12c(
        repo_root=repo_root,
        openyield_root=Path(args.openyield_root).resolve(),
        openram_root=Path(args.openram_root).resolve(),
        openram_reference_dir=(repo_root / args.openram_reference_dir).resolve(),
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        goal_md=(repo_root / args.goal_md).resolve(),
        progress_md=(repo_root / args.progress_md).resolve(),
        m12n2r_report=(repo_root / args.m12n2r_report).resolve(),
        m12n2_clean_report=(repo_root / args.m12n2_clean_report).resolve(),
        clean_top_graph=(repo_root / args.clean_top_graph).resolve(),
        layoutgen_golden=(repo_root / args.layoutgen_golden).resolve(),
        openyield_module_gds_dir=(repo_root / args.openyield_module_gds_dir).resolve(),
        m12o_gap_matrix=(repo_root / args.m12o_gap_matrix).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
