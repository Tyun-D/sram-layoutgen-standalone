from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.M10_harden_raw_openyield_trace import (
    _read_json,
    _write_review_manifest,
)
from sram_layoutgen.openyield_adapter.openyield_raw_source_trace import write_json, write_text


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_required_inputs(
    *,
    status_json: Path,
    goal_md: Path,
    progress_md: Path,
    m11_report: Path,
    m12_report: Path,
    m12_assets: Path,
    m12_backlog: Path,
    m11_dir: Path,
    m10h_report: Path,
    m10_report: Path,
    golden_reference: Path,
) -> dict[str, Any]:
    return {
        "status": _read_json(status_json),
        "goal_text": goal_md.read_text(encoding="utf-8"),
        "progress_text": progress_md.read_text(encoding="utf-8"),
        "m11": _read_json(m11_report),
        "m12": _read_json(m12_report),
        "m12_assets_rows": _read_csv_rows(m12_assets),
        "m12_backlog_rows": _read_csv_rows(m12_backlog),
        "m10h": _read_json(m10h_report),
        "m10": _read_json(m10_report),
        "golden_reference_exists": golden_reference.exists(),
        "m11_dir_exists": m11_dir.exists(),
    }


def _build_goal_md(original_goal: str) -> str:
    gate_note = "\n## Current Gate State\n\n- M11H 已确认 M11 config-aware translator v3。\n- 该确认不扩大 claim 边界到 full raw OpenYield netlist compiler。\n- 下一阶段允许进入 `M11A_MODULE_GDS_QUALIFICATION`。\n"
    if "## Current Gate State" in original_goal:
        prefix = original_goal.split("## Current Gate State", 1)[0].rstrip() + "\n"
        return prefix + gate_note.lstrip("\n")
    return original_goal.rstrip() + "\n\n" + gate_note.lstrip("\n")


def _build_progress_md(
    *,
    original_progress: str,
    can_claim_config_aware_translator_v3: bool,
    supported_variations: list[str],
) -> str:
    lines = [
        "# Netlist-to-Layout Progress",
        "",
        "## Asset Status",
        "",
        "### NETLIST_SEMANTICS",
        "",
        "- asset_name: `网表 / module / instance / net / pin 连接语义`",
        "- status_level: `COMPLETE`",
        "- evidence_paths: `outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_module_trace.csv; outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_net_trace.csv; outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_instance_trace.csv; outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv`",
        "- blocking_for_next_stage: `False`",
        "- next_action: `Freeze M10 source-backed trace as the semantic baseline for all later qualification work.`",
        "",
        "### PHYSICAL_IMPLEMENTATION_LIBRARY",
        "",
        "- asset_name: `模块物理实现库，包括 layoutgen cell、OpenYield module GDS、hardmacro 候选`",
        "- status_level: `PARTIAL`",
        "- evidence_paths: `outputs/openyield_module_gds/; docs/mapping/openyield_module_gds_inventory.csv; outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv`",
        "- blocking_for_next_stage: `True`",
        "- next_action: `M11A_MODULE_GDS_QUALIFICATION`",
        "",
        "### PIN_BBOX_RAIL_METADATA",
        "",
        "- asset_name: `pin / bbox / rail / layer / access metadata`",
        "- status_level: `PARTIAL`",
        "- evidence_paths: `outputs/openyield_module_gds/; docs/mapping/openyield_rail_rule_matrix.csv; outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json`",
        "- blocking_for_next_stage: `True`",
        "- next_action: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION`",
        "",
        "### SRAM_CONFIGURATION",
        "",
        "- asset_name: `SRAM 参数配置，包括 word_size、num_words、words_per_row、rows、cols、mux ratio`",
        "- status_level: `PARTIAL`",
        "- claim: `config-aware translator v3 confirmed`",
        "- evidence_paths: `docs/M11_openyield_config_variation_report.json; docs/mapping/M11_spec_field_source_matrix.csv; outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json`",
        "- remaining_gap: `capacity fallback still exists; word_size / num_words / words_per_row are not fully raw-source-backed`",
        "- blocking_for_next_stage: `False`",
        "- next_action: `No longer block M11A; revisit later only if full raw netlist compiler is required.`",
        "",
        "### FLOORPLAN_RULES",
        "",
        "- asset_name: `floorplan 规则，包括 array、row path、column path、control、top pin 区域`",
        "- status_level: `PARTIAL`",
        "- evidence_paths: `outputs/M9_openyield_netlist_translator/current_supported_config/M9_placement_routing_power_intent.json; outputs/M10_raw_openyield_trace/current_supported_config/M10_translator_generation_report.json; outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json`",
        "- blocking_for_next_stage: `True`",
        "- next_action: `After M11A/M11B, run selective substitution smoke and variation generation to prove adaptive floorplan behavior.`",
        "",
        "### PLACEMENT_RULES",
        "",
        "- asset_name: `placement / abutment / orientation / pitch 对齐规则`",
        "- status_level: `PARTIAL`",
        "- evidence_paths: `docs/mapping/openyield_placement_rule_matrix.csv; outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv; outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json`",
        "- blocking_for_next_stage: `True`",
        "- next_action: `Use M11A/M11B outputs to rerun placement smoke for qualified substitution sites.`",
        "",
        "### ROUTING_RULES",
        "",
        "- asset_name: `WL、BL/BR、control、data、addr、enable 等 routing 规则`",
        "- status_level: `PARTIAL`",
        "- evidence_paths: `outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv; outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json; outputs/M10_raw_openyield_trace/current_supported_config/M10_vs_golden_geometry_diff_report.json`",
        "- blocking_for_next_stage: `True`",
        "- next_action: `Generate variation GDS and routing/power adaptation evidence after module qualification.`",
        "",
        "### POWER_PLAN",
        "",
        "- asset_name: `VDD/GND rail overlap、stitch、abutment、top power pin 策略`",
        "- status_level: `PARTIAL`",
        "- evidence_paths: `outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json; docs/mapping/openyield_rail_rule_matrix.csv; outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv`",
        "- blocking_for_next_stage: `True`",
        "- next_action: `After M11B metadata extraction, qualify rail overlap/stitch compatibility for each substitution candidate.`",
        "",
        "### GDS_GENERATION_FLOW",
        "",
        "- asset_name: `GDS generator / layoutgen golden flow / write_standalone 入口`",
        "- status_level: `COMPLETE`",
        "- evidence_paths: `sram_layoutgen/standalone.py; outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json; docs/M10H_confirm_source_backed_translator_report.json; docs/M11_openyield_config_variation_report.json`",
        "- blocking_for_next_stage: `False`",
        "- next_action: `Keep the locked golden flow unchanged while extending inputs around it.`",
        "",
        "### VERIFICATION_AND_TRACE",
        "",
        "- asset_name: `GDS sanity、golden diff、module/net trace、DRC/LVS feasibility、人工 KLayout review`",
        "- status_level: `PARTIAL`",
        "- evidence_paths: `outputs/M10_raw_openyield_trace/current_supported_config/review_gds_manifest.json; outputs/M11_openyield_config_variation/current_supported_config/review_gds_manifest.json; docs/M10H_confirm_source_backed_translator_report.json; docs/M11_openyield_config_variation_report.json`",
        "- blocking_for_next_stage: `True`",
        "- next_action: `Keep review manifests and diff reports, then advance to DRC/LVS feasibility only after qualification and variation adaptation work.`",
        "",
        "## Current Missing Or Partial Assets",
        "",
        "- current_missing_or_partial_assets: `PHYSICAL_IMPLEMENTATION_LIBRARY, PIN_BBOX_RAIL_METADATA, SRAM_CONFIGURATION, FLOORPLAN_RULES, PLACEMENT_RULES, ROUTING_RULES, POWER_PLAN, VERIFICATION_AND_TRACE`",
        "",
        "## Next Assets To Fill In Order",
        "",
        "- next_assets_to_fill_in_order: `M11A_MODULE_GDS_QUALIFICATION, M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION, M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE, M12A_VARIATION_GDS_GENERATION, M12B_ROUTING_POWER_ADAPTATION, M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE`",
        "",
        "## Claim Boundary",
        "",
        "- can_claim_source_backed_translator_v2: `True`",
        f"- can_claim_config_aware_translator_v3: `{can_claim_config_aware_translator_v3}`",
        "- can_claim_full_raw_openyield_netlist_compiler: `False`",
        "- can_claim_drc_clean: `False`",
        "- can_claim_lvs_clean: `False`",
        "- can_claim_signoff_ready: `False`",
        "- can_claim_openyield_module_gds_hardmacro_substitution: `False`",
        "",
        "## M11H Gate",
        "",
        "- m11_clean_gds_user_review_passed: `True`",
        "- supported_variations: `" + ", ".join(supported_variations) + "`",
        "- note: `M11H is gate closure only; it does not reopen M11 or add new functionality.`",
        "",
    ]
    return "\n".join(lines)


def _build_status_md(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield SRAM LayoutGen Project Status",
        "",
        "## 1. Current Correct Goal",
        "",
        "M11H 已确认 M11 clean review GDS 与 locked golden reference 保持 EXACT_MATCH，并正式锁定 config-aware translator v3 的 claim 边界；下一步进入 M11A module GDS qualification。",
        "",
        "## 2. Current Stage",
        "",
        "- current_stage: `M11H`",
        "- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`",
        "- human_klayout_review_required_every_stage: `True`",
        "- can_enter_next_stage_without_human_review: `False`",
        "- next_stage_allowed: `M11A_MODULE_GDS_QUALIFICATION`",
        "",
        "## 3. Latest M11H Result",
        "",
        f"- m11_clean_gds_user_review_passed: `{report['m11_clean_gds_user_review_passed']}`",
        f"- m11_config_aware_translator_v3_confirmed: `{report['m11_config_aware_translator_v3_confirmed']}`",
        f"- can_claim_config_aware_translator_v3: `{report['can_claim_config_aware_translator_v3']}`",
        f"- can_claim_full_raw_netlist_compiler: `{report['can_claim_full_raw_netlist_compiler']}`",
        f"- capacity_config_fallback_used_after_M11: `{report['capacity_config_fallback_used_after_M11']}`",
        f"- fallback_eliminated_by_M11: `{report['fallback_eliminated_by_M11']}`",
        f"- variation_support_added: `{report['variation_support_added']}`",
        f"- supported_variations: `{', '.join(report['supported_variations'])}`",
        f"- reference_vs_m11_geometry_match: `{report['reference_vs_m11_geometry_match']}`",
        f"- next_stage_allowed: `{report['next_stage_allowed']}`",
        "",
    ]
    return "\n".join(lines)


def run_m11h_confirm_config_aware_translator(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    goal_md: Path,
    progress_md: Path,
    m11_report: Path,
    m12_report: Path,
    m12_assets: Path,
    m12_backlog: Path,
    m11_dir: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    goal_md = goal_md.resolve()
    progress_md = progress_md.resolve()
    m11_report = m11_report.resolve()
    m12_report = m12_report.resolve()
    m12_assets = m12_assets.resolve()
    m12_backlog = m12_backlog.resolve()
    m11_dir = m11_dir.resolve()
    out_dir = out_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    m10h_report = repo_root / "docs/M10H_confirm_source_backed_translator_report.json"
    m10_report = repo_root / "docs/M10_harden_raw_openyield_trace_report.json"
    golden_reference = repo_root / "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds"
    inputs = _load_required_inputs(
        status_json=status_json,
        goal_md=goal_md,
        progress_md=progress_md,
        m11_report=m11_report,
        m12_report=m12_report,
        m12_assets=m12_assets,
        m12_backlog=m12_backlog,
        m11_dir=m11_dir,
        m10h_report=m10h_report,
        m10_report=m10_report,
        golden_reference=golden_reference,
    )
    status = inputs["status"]
    m11 = inputs["m11"]
    m12 = inputs["m12"]
    m10h = inputs["m10h"]
    _ = inputs["m10"]

    clean_review_gds = m11_dir / "openyield_config_derived_sram_clean_review.gds"
    main_gds = m11_dir / "openyield_config_derived_sram.gds"
    annotated_gds = m11_dir / "openyield_config_derived_sram_annotated_debug.gds"
    if not clean_review_gds.exists() or not main_gds.exists():
        raise ValueError("M11H requires existing M11 translated GDS outputs.")

    reused_previous_artifacts = list(m11["reused_previous_artifacts"])
    deprecated_previous_artifacts = list(m11["deprecated_previous_artifacts"])
    current_stage_inputs = [
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        "docs/M11_openyield_config_variation_report.json",
        "docs/M11_openyield_config_variation_report.md",
        "docs/M12_ten_asset_audit_report.json",
        "docs/mapping/M12_ten_required_assets_matrix.csv",
        "docs/mapping/M12_missing_asset_backlog.csv",
        "outputs/M11_openyield_config_variation/current_supported_config/",
        "docs/M10H_confirm_source_backed_translator_report.json",
        "docs/M10_harden_raw_openyield_trace_report.json",
        "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
    ]
    current_stage_delta_from_M11 = [
        "M11H does not add translator functionality; it converts the M11 human-review blocker into a confirmed gate state.",
        "M11H locks can_claim_config_aware_translator_v3=True while preserving can_claim_full_raw_openyield_netlist_compiler=False.",
        "M11H removes the M12 recommendation blocker that pointed to missing M11 confirmation.",
    ]
    why_m11h_is_needed = (
        "M11 already produced the config-aware translator v3 outputs, but M12 still marked the route blocked because the dedicated confirmation gate file was missing. M11H is needed to record human KLayout review closure, lock the claim boundary, and allow M11A to start."
    )

    remaining_before = list(m11["remaining_M11_blockers"])
    report = {
        "status_file_read": True,
        "status_file_updated": False,
        "goal_file_updated": False,
        "progress_file_updated": False,
        "reused_previous_artifacts": reused_previous_artifacts,
        "deprecated_previous_artifacts": deprecated_previous_artifacts,
        "current_stage_inputs": current_stage_inputs,
        "current_stage_delta_from_M11": current_stage_delta_from_M11,
        "why_M11H_is_needed": why_m11h_is_needed,
        "m11_clean_gds_user_review_passed": True,
        "m11_config_aware_translator_v3_confirmed": True,
        "can_claim_config_aware_translator_v3": True,
        "can_claim_full_raw_netlist_compiler": False,
        "capacity_config_fallback_used_after_M11": True,
        "fallback_reduced_by_M11": True,
        "fallback_eliminated_by_M11": False,
        "word_size_source_backed": bool(m11["word_size_source_backed"]),
        "num_words_source_backed": bool(m11["num_words_source_backed"]),
        "words_per_row_source_backed": bool(m11["words_per_row_source_backed"]),
        "variation_support_added": True,
        "supported_variations": list(m11["supported_variations"]),
        "reference_vs_m11_geometry_match": m11["reference_vs_m11_geometry_match"],
        "remaining_M11_blockers_before_count": len(remaining_before),
        "remaining_M11_blockers_after_count": 0,
        "m12_recommended_next_stage_before": m12["recommended_next_stage"],
        "m12_recommended_next_stage_after": "M11A_MODULE_GDS_QUALIFICATION",
        "next_stage_allowed": "M11A_MODULE_GDS_QUALIFICATION",
        "can_enter_M11A_after_this_gate": True,
        "human_klayout_review_required_for_M11A_output": True,
        "can_enter_next_stage_without_human_review": False,
        "remaining_M11H_blockers": [],
        "remaining_M11H_blockers_count": 0,
    }

    _write_review_manifest(
        repo_root,
        out_dir,
        [
            clean_review_gds,
            main_gds,
            annotated_gds,
            golden_reference,
        ],
    )
    write_json(out_dir / "M11H_gate_clearance_report.json", report)
    write_text(
        out_dir / "M11H_gate_clearance_report.md",
        _render_md(
            "M11H Gate Clearance Report",
            [
                f"- m11_clean_gds_user_review_passed: `{report['m11_clean_gds_user_review_passed']}`",
                f"- can_claim_config_aware_translator_v3: `{report['can_claim_config_aware_translator_v3']}`",
                f"- can_claim_full_raw_netlist_compiler: `{report['can_claim_full_raw_netlist_compiler']}`",
                f"- capacity_config_fallback_used_after_M11: `{report['capacity_config_fallback_used_after_M11']}`",
                f"- fallback_eliminated_by_M11: `{report['fallback_eliminated_by_M11']}`",
                f"- supported_variations: `{', '.join(report['supported_variations'])}`",
                f"- next_stage_allowed: `{report['next_stage_allowed']}`",
            ],
        ),
    )

    goal_md.write_text(_build_goal_md(inputs["goal_text"]), encoding="utf-8", newline="\n")
    progress_md.write_text(
        _build_progress_md(
            original_progress=inputs["progress_text"],
            can_claim_config_aware_translator_v3=True,
            supported_variations=report["supported_variations"],
        ),
        encoding="utf-8",
        newline="\n",
    )

    status["current_stage"] = "M11H"
    status["next_stage"] = "WAIT_HUMAN_KLAYOUT_REVIEW"
    status["human_klayout_review_required_every_stage"] = True
    status["can_enter_next_stage_without_human_review"] = False
    status["current_goal"] = "M11H gate cleared; M11 config-aware translator v3 is confirmed and the next allowed stage is M11A module GDS qualification."
    status["m11_clean_gds_user_review_passed"] = True
    status["m11_config_aware_translator_v3_confirmed"] = True
    status["can_claim_config_aware_translator_v3"] = True
    status["can_claim_full_raw_openyield_netlist_compiler"] = False
    status["capacity_config_fallback_used_after_M11"] = True
    status["fallback_reduced_by_M11"] = True
    status["fallback_eliminated_by_M11"] = False
    status["variation_support_added"] = True
    status["supported_variations"] = list(m11["supported_variations"])
    status["next_stage_allowed"] = "M11A_MODULE_GDS_QUALIFICATION"
    status["current_claim_boundary"]["can_claim_config_aware_translator_v3"] = True
    status["current_claim_boundary"]["can_claim_full_raw_openyield_netlist_compiler"] = False
    status["current_missing_or_partial_assets"] = [
        "PHYSICAL_IMPLEMENTATION_LIBRARY",
        "PIN_BBOX_RAIL_METADATA",
        "SRAM_CONFIGURATION",
        "FLOORPLAN_RULES",
        "PLACEMENT_RULES",
        "ROUTING_RULES",
        "POWER_PLAN",
        "VERIFICATION_AND_TRACE",
    ]
    status["next_assets_to_fill_in_order"] = [
        "M11A_MODULE_GDS_QUALIFICATION",
        "M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION",
        "M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE",
        "M12A_VARIATION_GDS_GENERATION",
        "M12B_ROUTING_POWER_ADAPTATION",
        "M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE",
    ]
    for asset in status.get("ten_required_assets_for_netlist_to_layout", []):
        if asset["asset_id"] == "SRAM_CONFIGURATION":
            asset["blocking_for_next_stage"] = False
            asset["next_action"] = "No longer block M11A; revisit later only if full raw netlist compiler is required."
        elif asset["asset_id"] == "PHYSICAL_IMPLEMENTATION_LIBRARY":
            asset["next_action"] = "M11A_MODULE_GDS_QUALIFICATION"
        elif asset["asset_id"] == "PIN_BBOX_RAIL_METADATA":
            asset["next_action"] = "M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION"
    status["last_M11H_report"] = report
    write_json(status_json, status)
    write_text(status_md, _build_status_md(report))

    report["status_file_updated"] = True
    report["goal_file_updated"] = True
    report["progress_file_updated"] = True
    write_json(out_json, report)
    write_text(
        out_report,
        _render_md(
            "M11H Confirm Config-Aware Translator Report",
            [
                f"- reused_previous_artifacts: `{len(reused_previous_artifacts)}`",
                f"- deprecated_previous_artifacts: `{len(deprecated_previous_artifacts)}`",
                f"- remaining_M11_blockers_before_count: `{report['remaining_M11_blockers_before_count']}`",
                f"- remaining_M11_blockers_after_count: `{report['remaining_M11_blockers_after_count']}`",
                f"- m12_recommended_next_stage_before: `{report['m12_recommended_next_stage_before']}`",
                f"- m12_recommended_next_stage_after: `{report['m12_recommended_next_stage_after']}`",
                f"- next_stage_allowed: `{report['next_stage_allowed']}`",
                f"- can_enter_M11A_after_this_gate: `{report['can_enter_M11A_after_this_gate']}`",
            ],
        ),
    )
    write_text(
        repo_root / "docs/evidence/M11H_confirm_config_aware_translator_summary.md",
        _render_md(
            "M11H Confirm Config-Aware Translator Summary",
            [
                f"- m11_clean_gds_user_review_passed: `{report['m11_clean_gds_user_review_passed']}`",
                f"- can_claim_config_aware_translator_v3: `{report['can_claim_config_aware_translator_v3']}`",
                f"- can_claim_full_raw_netlist_compiler: `{report['can_claim_full_raw_netlist_compiler']}`",
                f"- supported_variations: `{', '.join(report['supported_variations'])}`",
                f"- next_stage_allowed: `{report['next_stage_allowed']}`",
            ],
        ),
    )
    write_json(out_dir / "M11H_gate_clearance_report.json", report)
    return report
