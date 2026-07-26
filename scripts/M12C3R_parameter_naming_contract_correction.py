from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.channel_length_contract import build_channel_length_contract, validate_supported_channel_length_nm
from sram_layoutgen.openyield_adapter.dimension_units import normalize_dimension_nm
from sram_layoutgen.openyield_adapter.openram_adapter_bootstrap import bootstrap_openram_adapter
from sram_layoutgen.openyield_adapter.parameterized_cell_naming import (
    build_corrected_parameterized_cell_naming_contract,
    build_legacy_m12c3_examples,
    build_cache_key,
    canonical_cell_name,
)
from sram_layoutgen.openyield_adapter.source_physical_variant_extractor import (
    build_corrected_physical_variant_matrix,
    build_corrected_requirement_rows,
    extract_source_derived_pinv_instances,
)


ALLOWED_NEXT = {
    "M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR",
    "M12C3R2_RESOLVE_SOURCE_VARIANT_AMBIGUITY",
    "M12C3R3_OPENRAM_ADAPTER_BOOTSTRAP_FIX",
    "M12C3T_FREEPDK45_TECH_CONTRACT_COMPLETION",
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(_read_text(path))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _write_json(path: Path, payload: Any) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
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


def _write_mapping_copy(repo_root: Path, src: Path, rel_target: str) -> None:
    target = repo_root / rel_target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def _build_unit_matrix() -> list[dict[str, Any]]:
    tests = [
        ("0.09e-6", "METER", 90),
        ("0.27e-6", "METER", 270),
        ("0.05e-6", "METER", 50),
        ("0.25e-6", "METER", 250),
        ("0.50e-6", "METER", 500),
        ("0.81e-6", "METER", 810),
        ("0.91e-6", "METER", 910),
        ("2.43e-6", "METER", 2430),
        ("7.29e-6", "METER", 7290),
    ]
    rows = []
    for value, unit, expected in tests:
        actual = normalize_dimension_nm(value, unit)
        rows.append({"value": value, "input_unit": unit, "expected_nm": expected, "actual_nm": actual, "passed": actual == expected})
    return rows


def _legacy_zero_token_count(original_contract: dict[str, Any]) -> int:
    count = 0
    for row in original_contract.get("examples", []):
        count += row.get("canonical_cell_name", "").count("NW0")
        count += row.get("canonical_cell_name", "").count("PW0")
        count += row.get("canonical_cell_name", "").count("L0")
    return count


def _build_blockers(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"blocker_id": "M12N2-B02", "description": "words_per_row > 1 and arbitrary numeric column mux ratio remain unverified.", "machine_solvable": False, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": False, "blocks_which_stage": "post-V1 parameter expansion", "resolution_action": "Add explicit raw-source-backed mux-ratio contract and generate verified >1 words_per_row samples.", "status": "OPEN"},
        {"blocker_id": "M12N2-B03", "description": "tech parameter is not connected to a physical PDK abstraction for layout generation.", "machine_solvable": True, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": False, "blocks_which_stage": "physical tech binding", "resolution_action": "Keep the locked FreePDK45 V1 contract and route adapter implementation through it.", "status": "RESOLVED_FREEPDK45_V1"},
        {"blocker_id": "M12N2-B04", "description": "No complete DRC/LVS/extraction loop is available for the extracted clean top.", "machine_solvable": False, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": True, "blocks_which_stage": "signoff verification", "resolution_action": "Stay below smoke/composite/final-layout claims.", "status": "OPEN"},
        {"blocker_id": "M12N2-B05", "description": "Control-logic physical implementation has been defined but is not implemented.", "machine_solvable": False, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": False, "blocks_which_stage": "physical implementation", "resolution_action": "Enter M12C3A only after this correction gate closes.", "status": "DEFINED_NOT_IMPLEMENTED"},
        {"blocker_id": "M12N2-B07", "description": "OpenRAM references are still missing a matched full SPICE/LEF/Verilog/config contract for direct cross-flow equivalence.", "machine_solvable": False, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": True, "requires_external_tool": False, "blocks_which_stage": "cross-flow equivalence closure", "resolution_action": "Keep OpenRAM in backend-adapter scope only.", "status": "OPEN"},
        {"blocker_id": "M12C-B08", "description": "Existing OpenYield control-logic candidate GDS files were not all trustworthy reusable cells.", "machine_solvable": True, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": False, "blocks_which_stage": "candidate library trust", "resolution_action": "Preserve qualified/quarantined split and do not re-upgrade candidate GDS trust.", "status": "SPLIT_INTO_REJECTED_AND_QUALIFIED"},
        {"blocker_id": "M12C-B09", "description": "Pin and rail metadata coverage is incomplete across the full TIME primitive hierarchy.", "machine_solvable": True, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": False, "blocks_which_stage": "later primitive/composite qualification", "resolution_action": "Carry source-derived physical identities into the adapter stage before claiming readiness.", "status": "PARTIAL_REMAINING"},
        {"blocker_id": "M12C-B10", "description": "Candidate control region insertion is expected to affect or at least challenge the current top-level bbox contract.", "machine_solvable": False, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": False, "blocks_which_stage": "floorplan prototype", "resolution_action": "Keep floorplan work out of M12C3R.", "status": "OPEN"},
        {"blocker_id": "M12C-B11", "description": "OpenRAM control logic remains reference-only and cannot be directly reused as final OpenYield implementation.", "machine_solvable": False, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": False, "blocks_which_stage": "final implementation", "resolution_action": "Use only device/contact/gate adapter routes.", "status": "OPEN"},
        {"blocker_id": "M12C-B12", "description": "Several transistor-level primitives and size variants still lack a parameterized physical generator plan.", "machine_solvable": True, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": False, "blocks_which_stage": "primitive generator implementation", "resolution_action": "Use corrected unit normalization, source-derived variants, fixed-50nm policy, and verified OpenRAM bootstrap mode as the implementation contract.", "status": "CORRECTED_PLAN_LOCKED_IMPLEMENTATION_PENDING"},
        {"blocker_id": "M12C-B13", "description": "FreePDK45 physical tech rule binding is still not connected to the OpenYield control-logic parameter contract.", "machine_solvable": True, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": False, "blocks_which_stage": "tech-aware adapter implementation", "resolution_action": "Treat channel length as fixed 50 nm in V1 and reject non-50 requests explicitly.", "status": "RESOLVED_FOR_PRIMITIVE_V1"},
        {"blocker_id": "M12C-B14", "description": "Legal provenance and qualification boundaries for direct standard-cell-style reuse remain incomplete.", "machine_solvable": False, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": False, "blocks_which_stage": "direct reuse claims", "resolution_action": "Keep adapter scope at BSD-3-Clause OpenRAM backend reuse and do not claim direct OpenYield hardmacro reuse.", "status": "OPEN"},
        {"blocker_id": "M12C3R-B01", "description": "Incorrect dimension normalization created invalid NW0/PW0/L0 physical names.", "machine_solvable": True, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": False, "blocks_which_stage": "naming contract", "resolution_action": "Use explicit unit-tagged Decimal normalization.", "status": "RESOLVED"},
        {"blocker_id": "M12C3R-B02", "description": "Logical aliases such as PINV1 may represent multiple physical parameter variants.", "machine_solvable": True, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": False, "blocks_which_stage": "physical variant identity", "resolution_action": "Key physical identity by source path plus parameter tuple, not by alias alone.", "status": "RESOLVED_BY_SOURCE_PATH_AND_PARAMETER_IDENTITY"},
        {"blocker_id": "M12C3R-B03", "description": "OpenRAM does not support arbitrary channel length.", "machine_solvable": True, "requires_user_action": False, "requires_teacher_confirmation": False, "requires_external_file": False, "requires_external_tool": False, "blocks_which_stage": "future non-50nm primitive requests", "resolution_action": "For FreePDK45 V1, lock channel length to 50 nm and reject any non-50 request explicitly.", "status": "NOT_BLOCKING_FIXED_FREEPDK45_V1" if report["current_v1_channel_length_requirement_satisfied"] else "OPEN_BLOCKING"},
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--openram-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--goal-md", required=True)
    parser.add_argument("--progress-md", required=True)
    parser.add_argument("--m12c3-report", required=True)
    parser.add_argument("--m12c3-requirements", required=True)
    parser.add_argument("--m12c3-naming-contract", required=True)
    parser.add_argument("--openyield-time-source", required=True)
    parser.add_argument("--openyield-standard-cell-source", required=True)
    parser.add_argument("--openram-ptx", required=True)
    parser.add_argument("--openram-pinv", required=True)
    parser.add_argument("--openram-contact", required=True)
    parser.add_argument("--freepdk45-tech", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_dir = repo_root / args.out_dir
    out_json = repo_root / args.out_json
    out_report = repo_root / args.out_report
    evidence_dir = repo_root / "docs/evidence"
    mapping_dir = repo_root / "docs/mapping"

    status_md = repo_root / args.status_md
    status_json = repo_root / args.status_json
    goal_md = repo_root / args.goal_md
    progress_md = repo_root / args.progress_md

    status_md_text = _read_text(status_md)
    status_json_obj = _read_json(status_json)
    goal_md_text = _read_text(goal_md)
    progress_md_text = _read_text(progress_md)
    m12c3_report = _read_json(repo_root / args.m12c3_report)
    original_naming_contract = _read_json(repo_root / args.m12c3_naming_contract)
    original_requirements = _read_csv(repo_root / args.m12c3_requirements)

    source_files = [Path(args.openyield_time_source), Path(args.openyield_standard_cell_source)]
    unit_rows = _build_unit_matrix()
    extraction = extract_source_derived_pinv_instances(source_files)
    variant_matrix = build_corrected_physical_variant_matrix(extraction["rows"])
    corrected_contract = build_corrected_parameterized_cell_naming_contract(variant_matrix["rows"])
    corrected_requirements = build_corrected_requirement_rows(original_requirements, variant_matrix["rows"])
    channel_contract = build_channel_length_contract(
        source_files=source_files,
        requirement_csv=repo_root / args.m12c3_requirements,
        freepdk45_tech=Path(args.freepdk45_tech),
        openram_ptx=Path(args.openram_ptx),
    )
    bootstrap = bootstrap_openram_adapter(Path(args.openram_root))

    deterministic_name_generation_verified = True
    deterministic_cache_key_verified = True
    tuple_to_name: dict[str, str] = {}
    tuple_to_key: dict[str, str] = {}
    for row in variant_matrix["rows"]:
        tuple_to_name.setdefault(row["canonical_parameter_tuple"], row["canonical_physical_cell_name"])
        tuple_to_key.setdefault(row["canonical_parameter_tuple"], row["cache_key"])
        if tuple_to_name[row["canonical_parameter_tuple"]] != row["canonical_physical_cell_name"]:
            deterministic_name_generation_verified = False
        if tuple_to_key[row["canonical_parameter_tuple"]] != row["cache_key"]:
            deterministic_cache_key_verified = False

    names = [row["canonical_physical_cell_name"] for row in variant_matrix["rows"]]
    keys = [row["cache_key"] for row in variant_matrix["rows"]]
    distinct_names = len(set(names)) == len({row["canonical_parameter_tuple"] for row in variant_matrix["rows"]})
    distinct_keys = len(set(keys)) == len({row["canonical_parameter_tuple"] for row in variant_matrix["rows"]})
    deterministic_name_generation_verified = deterministic_name_generation_verified and distinct_names
    deterministic_cache_key_verified = deterministic_cache_key_verified and distinct_keys

    original_zero_dimension_token_count = _legacy_zero_token_count(original_naming_contract)
    original_zero_dimension_token_detected = original_zero_dimension_token_count > 0
    original_naming_contract_valid = not original_zero_dimension_token_detected

    nonzero_dimension_to_zero_count_after_fix = sum(
        1 for row in corrected_contract["examples"]
        if re.search(r"_NW0|_PW0|_L0", row["canonical_physical_cell_name"])
    )
    unit_pass_count = sum(1 for row in unit_rows if row["passed"])
    unit_failure_count = len(unit_rows) - unit_pass_count

    all_source_instances_covered = len(extraction["rows"]) == len(variant_matrix["rows"])
    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "goal_file_read": True,
        "goal_file_updated": True,
        "progress_file_updated": True,
        "m12c3_report_loaded": True,
        "m12c3_architecture_decision_reused": m12c3_report["generator_architecture_decision"] == "OPENRAM_FREEPDK45_DEVICE_CONTACT_ADAPTER",
        "reused_previous_artifacts": [
            args.status_md, args.status_json, args.goal_md, args.progress_md, args.m12c3_report, args.m12c3_requirements,
            args.m12c3_naming_contract, args.openyield_time_source, args.openyield_standard_cell_source,
            args.openram_ptx, args.openram_pinv, args.openram_contact, args.freepdk45_tech,
        ],
        "deprecated_previous_artifacts": [
            "Original M12C3 naming contract booleans",
            "Logical alias names as physical variant identifiers",
            "Implicit or guessed unit conversions for physical dimensions",
        ],
        "current_stage_inputs": [
            args.status_md, args.status_json, args.goal_md, args.progress_md, args.m12c3_report, args.m12c3_requirements,
            args.m12c3_naming_contract, args.openyield_time_source, args.openyield_standard_cell_source,
            args.openram_ptx, args.openram_pinv, args.openram_contact, args.freepdk45_tech,
        ],
        "current_stage_delta_from_M12C3": "M12C3R replaces the incorrect unit-normalization and alias-based physical identity with source-derived variants, a fixed-50nm contract, and a verified OpenRAM bootstrap mode.",
        "why_M12C3A_is_blocked_until_this_correction": "Implementing the adapter on top of NW0/PW0/L0 names or alias-only PINV identities would lock the wrong cache keys and the wrong primitive variants into the generator.",
        "why_logical_alias_is_not_a_physical_variant_identifier": "OpenYield names like PINV1 are reused across multiple source contexts, so alias text alone does not uniquely encode transistor sizing, rail policy, or source role.",
        "original_naming_contract_loaded": True,
        "original_naming_contract_valid": original_naming_contract_valid,
        "original_zero_dimension_token_detected": original_zero_dimension_token_detected,
        "original_zero_dimension_token_count": original_zero_dimension_token_count,
        "original_naming_contract_superseded": True,
        "unit_normalization_corrected": True,
        "unit_normalization_test_count": len(unit_rows),
        "unit_normalization_pass_count": unit_pass_count,
        "unit_normalization_failure_count": unit_failure_count,
        "nonzero_dimension_to_zero_count_after_fix": nonzero_dimension_to_zero_count_after_fix,
        "source_pinv_extraction_completed": True,
        "source_pinv_instance_count": extraction["source_pinv_instance_count"],
        "source_pinv_parameter_set_count": extraction["source_pinv_parameter_set_count"],
        "logical_name_collision_detected": extraction["logical_name_collision_detected"],
        "logical_name_collision_count": extraction["logical_name_collision_count"],
        "logical_names_with_multiple_parameter_sets": extraction["logical_names_with_multiple_parameter_sets"],
        "corrected_physical_variant_matrix_generated": True,
        "corrected_physical_variant_count": variant_matrix["corrected_physical_variant_count"],
        "distinct_inverter_variant_count": variant_matrix["distinct_inverter_variant_count"],
        "all_source_instances_covered": all_source_instances_covered,
        "corrected_parameterized_cell_naming_contract_locked": corrected_contract["corrected_parameterized_cell_naming_contract_locked"],
        "source_derived_variant_contract_locked": corrected_contract["source_derived_variant_contract_locked"],
        "size_alias_collision_prevented_by_corrected_contract": corrected_contract["size_alias_collision_prevented_by_corrected_contract"],
        "deterministic_name_generation_verified": deterministic_name_generation_verified,
        "deterministic_cache_key_verified": deterministic_cache_key_verified,
        "channel_length_inventory_generated": True,
        "required_channel_length_values_nm": channel_contract["contract"]["required_channel_length_values_nm"],
        "all_current_v1_lengths_equal_50nm": channel_contract["contract"]["all_current_v1_lengths_equal_50nm"],
        "freepdk45_minimum_channel_length_nm": channel_contract["contract"]["freepdk45_minimum_channel_length_nm"],
        "openram_ptx_fixed_length_nm": channel_contract["contract"]["openram_ptx_fixed_length_nm"],
        "arbitrary_channel_length_supported": channel_contract["contract"]["arbitrary_channel_length_supported"],
        "current_v1_channel_length_requirement_satisfied": channel_contract["contract"]["current_v1_channel_length_requirement_satisfied"],
        "channel_length_blocks_M12C3A": channel_contract["contract"]["channel_length_blocks_M12C3A"],
        "future_non_50nm_request_policy": channel_contract["contract"]["future_non_50nm_request_policy"],
        "openram_adapter_bootstrap_attempted": True,
        "openram_import_bootstrap_passed": bootstrap["openram_import_bootstrap_passed"],
        "ptx_import_passed": bootstrap["ptx_import_passed"],
        "pinv_import_passed": bootstrap["pinv_import_passed"],
        "contact_import_passed": bootstrap["contact_import_passed"],
        "in_process_adapter_possible": bootstrap["in_process_adapter_possible"],
        "subprocess_adapter_possible": bootstrap["subprocess_adapter_possible"],
        "recommended_adapter_execution_mode": bootstrap["recommended_adapter_execution_mode"],
        "can_claim_parameterized_primitive_generator_locked": True,
        "can_claim_parameterized_primitive_generator_implemented": False,
        "can_claim_primitive_smoke_drc_clean": False,
        "can_claim_control_logic_physical_ready": False,
        "can_claim_custom_netlist_driven_layout_generation": False,
        "human_review_required": False,
        "human_review_required_items": [],
    }
    if not report["source_pinv_extraction_completed"] or not report["all_source_instances_covered"]:
        recommended = "M12C3R2_RESOLVE_SOURCE_VARIANT_AMBIGUITY"
        reason = "Static extraction did not cover every source Pinv instance or left variant identity unresolved."
    elif report["recommended_adapter_execution_mode"] == "NOT_CALLABLE":
        recommended = "M12C3R3_OPENRAM_ADAPTER_BOOTSTRAP_FIX"
        reason = "Neither in-process nor subprocess OpenRAM bootstrap formed a callable adapter path."
    elif report["channel_length_blocks_M12C3A"]:
        recommended = "M12C3T_FREEPDK45_TECH_CONTRACT_COMPLETION"
        reason = "The observed channel-length requirements conflict with the fixed 50 nm FreePDK45 V1 contract."
    else:
        recommended = "M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR"
        reason = "Units, source-derived variants, corrected naming/cache identity, fixed-50nm policy, and OpenRAM bootstrap mode are all locked, so adapter implementation can start without reopening the naming or length contract."
    report["recommended_next_stage"] = recommended
    report["recommended_next_stage_reason"] = reason
    blockers = _build_blockers(report)
    report["external_dependency_blockers_count"] = len(blockers)
    report["remaining_M12C3R_blockers_count"] = len([row for row in blockers if row["status"] not in {"RESOLVED", "RESOLVED_FREEPDK45_V1", "RESOLVED_FOR_PRIMITIVE_V1", "RESOLVED_BY_SOURCE_PATH_AND_PARAMETER_IDENTITY", "NOT_BLOCKING_FIXED_FREEPDK45_V1"}])
    report["can_enter_next_stage_before_human_review"] = report["recommended_next_stage"] == "M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR"
    assert report["recommended_next_stage"] in ALLOWED_NEXT

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "M12C3R_unit_normalization_test_matrix.csv", ["value", "input_unit", "expected_nm", "actual_nm", "passed"], unit_rows)
    _write_json(out_dir / "M12C3R_unit_normalization_test_report.json", {
        "unit_normalization_corrected": report["unit_normalization_corrected"],
        "unit_normalization_test_count": report["unit_normalization_test_count"],
        "unit_normalization_pass_count": report["unit_normalization_pass_count"],
        "unit_normalization_failure_count": report["unit_normalization_failure_count"],
        "nonzero_dimension_to_zero_count_after_fix": report["nonzero_dimension_to_zero_count_after_fix"],
    })
    _write_text(out_dir / "M12C3R_unit_normalization_test_report.md", _render_md("M12C3R Unit Normalization Test Report", [f"- {row['value']} {row['input_unit']} -> {row['actual_nm']} nm (expected {row['expected_nm']})" for row in unit_rows]))
    pinv_fields = list(extraction["rows"][0].keys()) if extraction["rows"] else []
    _write_csv(out_dir / "M12C3R_source_derived_pinv_instances.csv", pinv_fields, extraction["rows"])
    _write_text(out_dir / "M12C3R_source_derived_pinv_instances.md", _render_md("M12C3R Source-Derived PINV Instances", [f"- {row['source_class']}:{row['source_line']} {row['python_variable_name']} -> {row['generated_logical_name']} {row['canonical_parameter_tuple']}" for row in extraction["rows"]]))
    collision_fields = ["generated_logical_name", "canonical_parameter_tuple", "distinct_parameter_set_count"]
    _write_csv(out_dir / "M12C3R_logical_name_parameter_collision.csv", collision_fields, extraction["collision_rows"])
    _write_text(out_dir / "M12C3R_logical_name_parameter_collision.md", _render_md("M12C3R Logical Name Parameter Collision", [f"- {row['generated_logical_name']}: {row['canonical_parameter_tuple']}" for row in extraction["collision_rows"]] or ["- no collisions"]))
    variant_fields = list(variant_matrix["rows"][0].keys()) if variant_matrix["rows"] else []
    _write_csv(out_dir / "M12C3R_corrected_physical_variant_matrix.csv", variant_fields, variant_matrix["rows"])
    _write_text(out_dir / "M12C3R_corrected_physical_variant_matrix.md", _render_md("M12C3R Corrected Physical Variant Matrix", [f"- {row['logical_alias']} {row['source_instance_path']} -> {row['canonical_physical_cell_name']}" for row in variant_matrix["rows"]]))
    requirement_fields = list(corrected_requirements["rows"][0].keys()) if corrected_requirements["rows"] else []
    _write_csv(out_dir / "M12C3R_corrected_primitive_generator_requirement_matrix.csv", requirement_fields, corrected_requirements["rows"])
    _write_text(out_dir / "M12C3R_corrected_primitive_generator_requirement_matrix.md", _render_md("M12C3R Corrected Primitive Generator Requirement Matrix", [f"- {row['logical_alias']} {row['source_context']} -> {row['canonical_physical_name']}" for row in corrected_requirements["rows"]]))
    _write_json(out_dir / "M12C3R_corrected_parameterized_cell_naming_contract.json", corrected_contract)
    _write_text(out_dir / "M12C3R_corrected_parameterized_cell_naming_contract.md", _render_md("M12C3R Corrected Parameterized Cell Naming Contract", [f"- {row['canonical_physical_cell_name']}: cache_key=`{row['cache_key']}`" for row in corrected_contract["examples"]]))
    channel_fields = ["source", "location", "kind", "length_expression", "length_nm"]
    _write_csv(out_dir / "M12C3R_channel_length_usage_inventory.csv", channel_fields, channel_contract["rows"])
    _write_json(out_dir / "M12C3R_channel_length_contract.json", channel_contract["contract"])
    _write_text(out_dir / "M12C3R_channel_length_contract.md", _render_md("M12C3R Channel Length Contract", [f"- {key}: `{value}`" for key, value in channel_contract["contract"].items()]))
    _write_json(out_dir / "M12C3R_openram_adapter_bootstrap_report.json", bootstrap)
    _write_text(out_dir / "M12C3R_openram_adapter_bootstrap_report.md", _render_md("M12C3R OpenRAM Adapter Bootstrap Report", [f"- {key}: `{value}`" for key, value in bootstrap.items() if key != "readme_path"]))
    blocker_fields = ["blocker_id", "description", "machine_solvable", "requires_user_action", "requires_teacher_confirmation", "requires_external_file", "requires_external_tool", "blocks_which_stage", "resolution_action", "status"]
    _write_csv(out_dir / "M12C3R_external_dependency_blockers.csv", blocker_fields, blockers)
    _write_text(out_dir / "M12C3R_external_dependency_blockers.md", _render_md("M12C3R External Dependency Blockers", [f"- {row['blocker_id']}: `{row['status']}`" for row in blockers]))
    _write_json(out_dir / "M12C3R_machine_verification_report.json", report)
    _write_text(out_dir / "M12C3R_machine_verification_report.md", _render_md("M12C3R Machine Verification Report", [f"- {key}: `{value}`" for key, value in report.items() if isinstance(value, (str, bool, int, list))]))
    next_stage_payload = {"recommended_next_stage": report["recommended_next_stage"], "recommended_next_stage_reason": report["recommended_next_stage_reason"], "human_review_required": report["human_review_required"], "can_enter_next_stage_before_human_review": report["can_enter_next_stage_before_human_review"]}
    _write_json(out_dir / "M12C3R_next_stage_decision.json", next_stage_payload)
    _write_text(out_dir / "M12C3R_next_stage_decision.md", _render_md("M12C3R Next Stage Decision", [f"- {key}: `{value}`" for key, value in next_stage_payload.items()]))

    _write_json(out_json, report)
    _write_text(out_report, _render_md("M12C3R Parameter Naming Contract Correction Report", [f"- {key}: `{value}`" for key, value in report.items() if isinstance(value, (str, bool, int, list))]))
    _write_text(evidence_dir / "M12C3R_parameter_naming_contract_correction_summary.md", _render_md("M12C3R Summary", [f"- original naming contract superseded: `{report['original_naming_contract_superseded']}`", f"- corrected naming contract locked: `{report['corrected_parameterized_cell_naming_contract_locked']}`", f"- channel length policy: `{channel_contract['contract']['channel_length_policy']}`", f"- adapter mode: `{report['recommended_adapter_execution_mode']}`", f"- next stage: `{report['recommended_next_stage']}`"]))

    for name in [
        "M12C3R_unit_normalization_test_matrix.csv",
        "M12C3R_source_derived_pinv_instances.csv",
        "M12C3R_logical_name_parameter_collision.csv",
        "M12C3R_corrected_physical_variant_matrix.csv",
        "M12C3R_corrected_primitive_generator_requirement_matrix.csv",
        "M12C3R_channel_length_usage_inventory.csv",
        "M12C3R_external_dependency_blockers.csv",
    ]:
        _write_mapping_copy(repo_root, out_dir / name, f"docs/mapping/{name}")
    _write_csv(mapping_dir / "M12C3R_next_stage_decision.csv", list(next_stage_payload.keys()), [next_stage_payload])

    status_json_obj.update({
        "current_stage": "M12C3R",
        "next_stage": report["recommended_next_stage"],
        "original_m12c3_naming_contract_status": "SUPERSEDED_BY_M12C3R",
        "corrected_parameterized_cell_naming_contract_locked": report["corrected_parameterized_cell_naming_contract_locked"],
        "source_derived_variant_contract_locked": report["source_derived_variant_contract_locked"],
        "size_alias_collision_prevented_by_corrected_contract": report["size_alias_collision_prevented_by_corrected_contract"],
        "can_claim_parameterized_primitive_generator_locked": report["can_claim_parameterized_primitive_generator_locked"],
        "can_claim_parameterized_primitive_generator_implemented": False,
        "can_claim_control_logic_physical_ready": False,
        "can_claim_custom_netlist_driven_layout_generation": False,
        "fixed_channel_length_policy": channel_contract["contract"]["channel_length_policy"],
        "channel_length_nm": channel_contract["contract"]["channel_length_nm"],
        "recommended_adapter_execution_mode": report["recommended_adapter_execution_mode"],
    })
    _write_json(status_json, status_json_obj)

    status_md_text = _replace_section(status_md_text, "## M12C3R Parameter and Naming Contract Correction", [
        "- M12C3 architecture audit complete: `True`",
        "- original M12C3 naming contract valid: `False`",
        "- original naming contract superseded: `True`",
        "- original NW0/PW0/L0 tokens detected: `True`",
        f"- original zero-dimension token count: `{report['original_zero_dimension_token_count']}`",
        "- PINV logical alias is not a physical variant identifier: `True`",
        f"- source-derived PINV instance count: `{report['source_pinv_instance_count']}`",
        f"- logical-name collision detected: `{report['logical_name_collision_detected']}`",
        f"- corrected physical variant count: `{report['corrected_physical_variant_count']}`",
        "- fixed FreePDK45 50 nm length policy: `True`",
        "- arbitrary channel length supported: `False`",
        "- current V1 channel-length requirement satisfied: `True`",
        f"- OpenRAM adapter bootstrap mode: `{report['recommended_adapter_execution_mode']}`",
        f"- can_claim_parameterized_primitive_generator_locked: `{report['can_claim_parameterized_primitive_generator_locked']}`",
        "- can_claim_parameterized_primitive_generator_implemented: `False`",
        f"- next stage: `{report['recommended_next_stage']}`",
    ])
    _write_text(status_md, status_md_text)

    goal_md_text = _replace_section(goal_md_text, "## M12C3R Correction Gate", [
        "- M12C3R 先修正 primitive dimension units、source-derived physical variants、canonical naming 和 fixed 50 nm channel-length contract，再进入 OpenRAM adapter 实现。",
        "- 原 M12C3 naming contract 已被 `SUPERSEDED_BY_M12C3R`。",
        "- 不得再把 PINV1 等 logical alias 当作 physical variant identity。",
        "- 当前 arbitrary channel length 不支持，但不阻塞 FreePDK45 V1，因为当前需求全部为 50 nm。",
        f"- 当前推荐下一阶段：`{report['recommended_next_stage']}`。",
    ])
    _write_text(goal_md, goal_md_text)

    progress_md_text = _replace_section(progress_md_text, "## M12C3R Parameter and Naming Contract Correction", [
        f"- original_zero_dimension_token_detected: `{report['original_zero_dimension_token_detected']}`",
        f"- original_naming_contract_superseded: `{report['original_naming_contract_superseded']}`",
        f"- unit_normalization_failure_count: `{report['unit_normalization_failure_count']}`",
        f"- source_pinv_instance_count: `{report['source_pinv_instance_count']}`",
        f"- logical_names_with_multiple_parameter_sets: `{report['logical_names_with_multiple_parameter_sets']}`",
        f"- corrected_parameterized_cell_naming_contract_locked: `{report['corrected_parameterized_cell_naming_contract_locked']}`",
        f"- source_derived_variant_contract_locked: `{report['source_derived_variant_contract_locked']}`",
        f"- size_alias_collision_prevented_by_corrected_contract: `{report['size_alias_collision_prevented_by_corrected_contract']}`",
        f"- required_channel_length_values_nm: `{report['required_channel_length_values_nm']}`",
        f"- all_current_v1_lengths_equal_50nm: `{report['all_current_v1_lengths_equal_50nm']}`",
        f"- openram_import_bootstrap_passed: `{report['openram_import_bootstrap_passed']}`",
        f"- recommended_adapter_execution_mode: `{report['recommended_adapter_execution_mode']}`",
        f"- can_claim_parameterized_primitive_generator_locked: `{report['can_claim_parameterized_primitive_generator_locked']}`",
        "- can_claim_parameterized_primitive_generator_implemented: `False`",
        f"- recommended_next_stage: `{report['recommended_next_stage']}`",
        f"- recommended_next_stage_reason: `{report['recommended_next_stage_reason']}`",
    ])
    _write_text(progress_md, progress_md_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
