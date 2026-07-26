from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.M10_harden_raw_openyield_trace import _read_json, _rel
from sram_layoutgen.openyield_adapter.openyield_raw_source_trace import write_csv, write_json, write_text


ASSET_FIELDNAMES = [
    "asset_id",
    "asset_name",
    "required_for_netlist_to_layout",
    "current_status",
    "status_level",
    "evidence_paths",
    "evidence_summary",
    "source_stage",
    "is_complete",
    "is_partial",
    "is_missing",
    "blocking_for_next_stage",
    "blocking_reason",
    "must_reuse_artifacts",
    "deprecated_artifacts_not_to_use",
    "next_action",
    "next_stage_to_fill",
    "priority",
]

WORKDIR_INVENTORY_FIELDNAMES = [
    "scan_root",
    "relative_path",
    "exists",
    "path_kind",
    "asset_hits",
    "stage_tags",
    "is_required_input",
    "evidence_strength",
    "summary",
]

BACKLOG_FIELDNAMES = [
    "asset_id",
    "asset_name",
    "status_level",
    "blocking_for_next_stage",
    "blocking_reason",
    "next_action",
    "next_stage_to_fill",
    "priority",
]

NEXT_PLAN_FIELDNAMES = [
    "sequence",
    "stage_id",
    "why_now",
    "depends_on",
    "blocks_assets",
    "entry_condition",
]


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def _optional_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return _read_json(path)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _bool_text(value: bool) -> str:
    return "True" if value else "False"


def _csv_list(items: list[str]) -> str:
    return ";".join(items)


def _asset_row(
    *,
    asset_id: str,
    asset_name: str,
    status_level: str,
    evidence_paths: list[str],
    evidence_summary: str,
    source_stage: str,
    blocking_reason: str,
    must_reuse_artifacts: list[str],
    deprecated_artifacts_not_to_use: list[str],
    next_action: str,
    next_stage_to_fill: str,
    priority: str,
) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "asset_name": asset_name,
        "required_for_netlist_to_layout": True,
        "current_status": status_level,
        "status_level": status_level,
        "evidence_paths": evidence_paths,
        "evidence_summary": evidence_summary,
        "source_stage": source_stage,
        "is_complete": status_level == "COMPLETE",
        "is_partial": status_level == "PARTIAL",
        "is_missing": status_level == "MISSING",
        "blocking_for_next_stage": status_level != "COMPLETE",
        "blocking_reason": blocking_reason,
        "must_reuse_artifacts": must_reuse_artifacts,
        "deprecated_artifacts_not_to_use": deprecated_artifacts_not_to_use,
        "next_action": next_action,
        "next_stage_to_fill": next_stage_to_fill,
        "priority": priority,
    }


def _render_asset_matrix_md(rows: list[dict[str, Any]]) -> str:
    lines = ["| asset_id | status_level | next_stage_to_fill | evidence_summary |", "| --- | --- | --- | --- |"]
    for row in rows:
        lines.append(
            f"| {row['asset_id']} | {row['status_level']} | {row['next_stage_to_fill']} | {row['evidence_summary']} |"
        )
    return _render_md("M12 Ten Required Assets Matrix", lines)


def _render_inventory_md(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| scan_root | relative_path | asset_hits | evidence_strength |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows[:200]:
        lines.append(
            f"| {row['scan_root']} | {row['relative_path']} | {row['asset_hits'] or '-'} | {row['evidence_strength']} |"
        )
    if len(rows) > 200:
        lines.append(f"| ... | truncated_after_200_rows | total={len(rows)} | ... |")
    return _render_md("M12 Workdir Asset Evidence Inventory", lines)


def _render_backlog_md(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| asset_id | status_level | next_stage_to_fill | next_action |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['asset_id']} | {row['status_level']} | {row['next_stage_to_fill']} | {row['next_action']} |"
        )
    return _render_md("M12 Missing Asset Backlog", lines)


def _render_next_plan_md(rows: list[dict[str, Any]], recommended_next_stage: str) -> str:
    lines = [f"- recommended_next_stage: `{recommended_next_stage}`", ""]
    for row in rows:
        lines.extend(
            [
                f"## {row['sequence']}. {row['stage_id']}",
                "",
                f"- why_now: `{row['why_now']}`",
                f"- depends_on: `{row['depends_on']}`",
                f"- blocks_assets: `{row['blocks_assets']}`",
                f"- entry_condition: `{row['entry_condition']}`",
                "",
            ]
        )
    return "\n".join(["# M12 Next Fill Plan", "", *lines]).rstrip() + "\n"


def _discover_goal_progress_files(repo_root: Path) -> tuple[list[str], list[str]]:
    goal_candidates = [
        "PROJECT_GOAL.md",
        "docs/project_goal.md",
        "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
    ]
    progress_candidates = [
        "PROJECT_PROGRESS.md",
        "PROJECT_PLAN.md",
        "docs/project_progress.md",
        "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
    ]
    found_goals = [path for path in goal_candidates if (repo_root / path).exists()]
    found_progress = [path for path in progress_candidates if (repo_root / path).exists()]
    if not found_goals:
        found_goals = ["PROJECT_NETLIST_TO_LAYOUT_GOAL.md"]
    if not found_progress:
        found_progress = ["PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md"]
    return found_goals, found_progress


def _scan_workdir(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    scan_roots = [
        "sram_layoutgen",
        "scripts",
        "tests",
        "docs",
        "outputs",
        "external_references",
    ]
    rows: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for root_name in scan_roots:
        root = repo_root / root_name
        if not root.exists():
            continue
        count = 0
        for path in sorted(root.rglob("*")):
            if "__pycache__" in path.parts or path.is_dir():
                continue
            rel = _rel(repo_root, path)
            rel_lower = rel.lower()
            asset_hits: list[str] = []
            if any(token in rel_lower for token in ["module_binding", "net_binding", "source_backed", "layout_intent", "semantic"]):
                asset_hits.append("NETLIST_SEMANTICS")
            if any(token in rel_lower for token in ["openyield_module_gds", "module_gds", "generator_manifest"]):
                asset_hits.append("PHYSICAL_IMPLEMENTATION_LIBRARY")
            if any(token in rel_lower for token in ["pins.json", "bbox.json", "rail_report", "pin_access", "rail_rule"]):
                asset_hits.append("PIN_BBOX_RAIL_METADATA")
            if any(token in rel_lower for token in ["config", "variation", "sram_spec", "global.yaml"]):
                asset_hits.append("SRAM_CONFIGURATION")
            if any(token in rel_lower for token in ["floorplan", "layout_intent", "region", "connection_matrix"]):
                asset_hits.append("FLOORPLAN_RULES")
            if any(token in rel_lower for token in ["placement", "abutment", "orientation", "module_usage", "pitch"]):
                asset_hits.append("PLACEMENT_RULES")
            if any(token in rel_lower for token in ["routing", "net_binding", "shape", "wordline", "bitline"]):
                asset_hits.append("ROUTING_RULES")
            if any(token in rel_lower for token in ["power", "rail", "vdd", "gnd", "stitch"]):
                asset_hits.append("POWER_PLAN")
            if any(token in rel_lower for token in ["standalone", "translated_sram", "reproduced_fixed", "golden_reference"]):
                asset_hits.append("GDS_GENERATION_FLOW")
            if any(token in rel_lower for token in ["review", "diff_report", "remaining_gap", "sanity", "trace"]):
                asset_hits.append("VERIFICATION_AND_TRACE")
            stage_tags = []
            for part in path.parts:
                if part.startswith("M") and len(part) >= 2 and part[1].isdigit():
                    stage_tags.append(part)
            rows.append(
                {
                    "scan_root": root_name,
                    "relative_path": rel,
                    "exists": True,
                    "path_kind": "file",
                    "asset_hits": _csv_list(sorted(set(asset_hits))),
                    "stage_tags": _csv_list(stage_tags),
                    "is_required_input": rel
                    in {
                        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
                        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
                        "docs/M10H_confirm_source_backed_translator_report.json",
                        "docs/M11_openyield_config_variation_report.json",
                    },
                    "evidence_strength": "DIRECT" if asset_hits else "CONTEXT",
                    "summary": f"Scanned file under {root_name}.",
                }
            )
            count += 1
        counts[root_name] = count
    return rows, counts


def _build_asset_rows(
    *,
    repo_root: Path,
    status: dict[str, Any],
    m10h: dict[str, Any],
    m11: dict[str, Any],
    m11h: dict[str, Any] | None,
    module_inventory_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    deprecated_common = [
        "outputs/layout_prototype/hybrid_openyield_rail_overlap/hybrid_openyield_rail_overlap.complete.gds",
        "*_access_module",
        "floorplan_proxy*",
        "outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds",
    ]
    openyield_module_count = len([row for row in module_inventory_rows if row.get("gds_generated") == "True"])
    can_claim_config_aware = m11h is not None and bool(m11.get("can_claim_config_aware_translator_v3"))
    return [
        _asset_row(
            asset_id="NETLIST_SEMANTICS",
            asset_name="网表 / module / instance / net / pin 连接语义",
            status_level="COMPLETE",
            evidence_paths=[
                "outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_module_trace.csv",
                "outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_net_trace.csv",
                "outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_instance_trace.csv",
                "outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv",
            ],
            evidence_summary="M10 source-backed module/net/instance trace and M9 net binding matrix cover the current supported translator semantics, but this does not expand into a full raw compiler claim.",
            source_stage="M9/M10/M10H",
            blocking_reason="Semantic trace is reusable for the locked supported config; remaining blocker is claim scope, not missing semantics evidence.",
            must_reuse_artifacts=[
                "outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_module_trace.csv",
                "outputs/M10_raw_openyield_trace/current_supported_config/M10_source_backed_net_trace.csv",
                "docs/M10H_confirm_source_backed_translator_report.json",
            ],
            deprecated_artifacts_not_to_use=deprecated_common,
            next_action="Freeze M10 source-backed trace as the semantic baseline for all later qualification work.",
            next_stage_to_fill="REUSE_IN_M11A_AND_LATER",
            priority="P1",
        ),
        _asset_row(
            asset_id="PHYSICAL_IMPLEMENTATION_LIBRARY",
            asset_name="模块物理实现库，包括 layoutgen cell、OpenYield module GDS、hardmacro 候选",
            status_level="PARTIAL",
            evidence_paths=[
                "outputs/openyield_module_gds/",
                "docs/mapping/openyield_module_gds_inventory.csv",
                "outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv",
            ],
            evidence_summary=f"OpenYield module GDS inventory exists for {openyield_module_count} modules and M9 binds them semantically, but the library is not yet qualified for hardmacro substitution.",
            source_stage="L3/M1/M9",
            blocking_reason="Existing module GDS are candidates, not qualified replacements for final SRAM assembly or selective substitution.",
            must_reuse_artifacts=[
                "outputs/openyield_module_gds/",
                "docs/mapping/openyield_module_gds_inventory.csv",
                "outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv",
            ],
            deprecated_artifacts_not_to_use=deprecated_common,
            next_action="Run M11A to qualify which OpenYield module GDS can be treated as reusable hardmacros versus fallback-only candidates.",
            next_stage_to_fill="M11A",
            priority="P0",
        ),
        _asset_row(
            asset_id="PIN_BBOX_RAIL_METADATA",
            asset_name="pin / bbox / rail / layer / access metadata",
            status_level="PARTIAL",
            evidence_paths=[
                "outputs/openyield_module_gds/",
                "docs/mapping/openyield_rail_rule_matrix.csv",
                "outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json",
            ],
            evidence_summary="Per-module pins/bbox/rail artifacts exist and M8R proves top-level rail overlap recovery, but qualified module-by-module extraction and access validation are incomplete.",
            source_stage="L3/M8R/M9",
            blocking_reason="Metadata exists, but not every OpenYield module GDS pin/bbox/rail record has been qualification-checked for substitution use.",
            must_reuse_artifacts=[
                "outputs/openyield_module_gds/*/pins.json",
                "outputs/openyield_module_gds/*/bbox.json",
                "outputs/openyield_module_gds/*/rail_report.json",
            ],
            deprecated_artifacts_not_to_use=deprecated_common,
            next_action="Run M11B on top of M11A results to extract and verify pin/bbox/rail metadata only from qualified module GDS.",
            next_stage_to_fill="M11B",
            priority="P0",
        ),
        _asset_row(
            asset_id="SRAM_CONFIGURATION",
            asset_name="SRAM 参数配置，包括 word_size、num_words、words_per_row、rows、cols、mux ratio",
            status_level="PARTIAL",
            evidence_paths=[
                "docs/M11_openyield_config_variation_report.json",
                "docs/mapping/M11_spec_field_source_matrix.csv",
                "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json",
            ],
            evidence_summary=f"M11 adds variation support and can derive 8x64_wpr4, 4x32_wpr2, 16x16_wpr1, but word_size/num_words/words_per_row still rely on fallback and M11H gate is missing={_bool_text(m11h is None)}.",
            source_stage="M11",
            blocking_reason="Raw-backed capacity/config coverage is incomplete and M11H confirmation file does not exist.",
            must_reuse_artifacts=[
                "docs/M11_openyield_config_variation_report.json",
                "docs/mapping/M11_spec_field_source_matrix.csv",
                "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json",
            ],
            deprecated_artifacts_not_to_use=deprecated_common,
            next_action="First clear M11H gate status, then keep narrowing fallback fields before claiming config-aware translator v3.",
            next_stage_to_fill="M11H",
            priority="P0",
        ),
        _asset_row(
            asset_id="FLOORPLAN_RULES",
            asset_name="floorplan 规则，包括 array、row path、column path、control、top pin 区域",
            status_level="PARTIAL",
            evidence_paths=[
                "outputs/M9_openyield_netlist_translator/current_supported_config/M9_placement_routing_power_intent.json",
                "outputs/M10_raw_openyield_trace/current_supported_config/M10_translator_generation_report.json",
                "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json",
            ],
            evidence_summary="Locked golden flow reproduces the supported config exactly, but adaptive floorplan rules for variation output and selective hardmacro replacement are not yet proven.",
            source_stage="M8R/M9/M10/M11",
            blocking_reason="Current floorplan evidence is strong for the locked golden path only; generalized variation and substitution rules are not yet closed.",
            must_reuse_artifacts=[
                "outputs/M9_openyield_netlist_translator/current_supported_config/M9_placement_routing_power_intent.json",
                "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds",
            ],
            deprecated_artifacts_not_to_use=deprecated_common,
            next_action="After M11A/M11B, run selective substitution smoke and variation generation to prove adaptive floorplan behavior.",
            next_stage_to_fill="M11C",
            priority="P1",
        ),
        _asset_row(
            asset_id="PLACEMENT_RULES",
            asset_name="placement / abutment / orientation / pitch 对齐规则",
            status_level="PARTIAL",
            evidence_paths=[
                "docs/mapping/openyield_placement_rule_matrix.csv",
                "outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv",
                "outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json",
            ],
            evidence_summary="Placement, abutment, orientation, and pitch rules are documented and reused by the locked translator path, but they are not proven under qualified OpenYield module substitution.",
            source_stage="L2/L3/M8R/M9",
            blocking_reason="Rulebooks exist, yet no qualified placement proof exists for selective OpenYield hardmacro insertion.",
            must_reuse_artifacts=[
                "docs/mapping/openyield_placement_rule_matrix.csv",
                "outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv",
            ],
            deprecated_artifacts_not_to_use=deprecated_common,
            next_action="Use M11A/M11B outputs to rerun placement smoke for qualified substitution sites.",
            next_stage_to_fill="M11C",
            priority="P1",
        ),
        _asset_row(
            asset_id="ROUTING_RULES",
            asset_name="WL、BL/BR、control、data、addr、enable 等 routing 规则",
            status_level="PARTIAL",
            evidence_paths=[
                "outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv",
                "outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json",
                "outputs/M10_raw_openyield_trace/current_supported_config/M10_vs_golden_geometry_diff_report.json",
            ],
            evidence_summary="Routing semantics and exact-match locked flow are proven, but variable routing adaptation for non-locked variations and qualified module substitution is not yet demonstrated.",
            source_stage="M8R/M9/M10/M11",
            blocking_reason="Current routing proof is locked-flow exact match, not variation-aware or substitution-aware routing closure.",
            must_reuse_artifacts=[
                "outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv",
                "outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json",
            ],
            deprecated_artifacts_not_to_use=deprecated_common,
            next_action="Generate variation GDS and routing/power adaptation evidence after module qualification.",
            next_stage_to_fill="M12B",
            priority="P1",
        ),
        _asset_row(
            asset_id="POWER_PLAN",
            asset_name="VDD/GND rail overlap、stitch、abutment、top power pin 策略",
            status_level="PARTIAL",
            evidence_paths=[
                "outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json",
                "docs/mapping/openyield_rail_rule_matrix.csv",
                "outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv",
            ],
            evidence_summary="M8R recovered the locked power rail overlap and top-level stitch geometry, but qualified module-boundary rail compatibility and substitution-era stitch policy remain open.",
            source_stage="M8R/L2/L3/M9",
            blocking_reason="Power evidence is exact for the locked baseline only; module boundary compatibility with OpenYield GDS candidates is not qualified.",
            must_reuse_artifacts=[
                "outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json",
                "docs/mapping/openyield_rail_rule_matrix.csv",
            ],
            deprecated_artifacts_not_to_use=deprecated_common,
            next_action="After M11B metadata extraction, qualify rail overlap/stitch compatibility for each substitution candidate.",
            next_stage_to_fill="M12B",
            priority="P1",
        ),
        _asset_row(
            asset_id="GDS_GENERATION_FLOW",
            asset_name="GDS generator / layoutgen golden flow / write_standalone 入口",
            status_level="COMPLETE",
            evidence_paths=[
                "sram_layoutgen/standalone.py",
                "outputs/M8R_fix_golden_geometry_delta/current_supported_config/M8R_fixed_reproduction_report.json",
                "docs/M10H_confirm_source_backed_translator_report.json",
                "docs/M11_openyield_config_variation_report.json",
            ],
            evidence_summary="The locked layoutgen golden flow and write_standalone entry are proven and reused across M8R, M10, and M11 for current supported delivery.",
            source_stage="M8R/M10/M11",
            blocking_reason="Generation entry itself is not blocked; extension work is needed in other assets, not in the existence of the flow.",
            must_reuse_artifacts=[
                "sram_layoutgen/standalone.py",
                "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds",
            ],
            deprecated_artifacts_not_to_use=deprecated_common,
            next_action="Keep the locked golden flow unchanged while extending inputs around it.",
            next_stage_to_fill="REUSE_AS_BASELINE",
            priority="P1",
        ),
        _asset_row(
            asset_id="VERIFICATION_AND_TRACE",
            asset_name="GDS sanity、golden diff、module/net trace、DRC/LVS feasibility、人工 KLayout review",
            status_level="PARTIAL",
            evidence_paths=[
                "outputs/M10_raw_openyield_trace/current_supported_config/review_gds_manifest.json",
                "outputs/M11_openyield_config_variation/current_supported_config/review_gds_manifest.json",
                "docs/M10H_confirm_source_backed_translator_report.json",
                "docs/M11_openyield_config_variation_report.json",
            ],
            evidence_summary=f"GDS sanity, exact-match diff, and source-backed trace exist, but DRC/LVS/signoff claims remain false and M11H confirmation present={_bool_text(can_claim_config_aware)}.",
            source_stage="M8R/M10/M10H/M11",
            blocking_reason="Human KLayout review is required and DRC/LVS/netlist-to-layout equivalence are not yet closed.",
            must_reuse_artifacts=[
                "outputs/M10_raw_openyield_trace/current_supported_config/review_gds_manifest.json",
                "outputs/M11_openyield_config_variation/current_supported_config/review_gds_manifest.json",
            ],
            deprecated_artifacts_not_to_use=deprecated_common,
            next_action="Keep review manifests and diff reports, then advance to DRC/LVS feasibility only after qualification and variation adaptation work.",
            next_stage_to_fill="M13",
            priority="P0",
        ),
    ]


def _build_goal_md(asset_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Netlist-to-Layout Goal",
        "",
        "## Goal",
        "",
        "在已锁定的 layoutgen golden flow 上，把 OpenYield 网表语义、模块候选、配置、floorplan、placement、routing、power 和验证证据收敛成可追溯的 netlist-to-layout 资产闭环。",
        "",
        "## Ten Required Assets",
        "",
    ]
    for row in asset_rows:
        lines.append(f"- `{row['asset_id']}`: {row['asset_name']} [{row['status_level']}]")
    lines.extend(
        [
            "",
            "## Reuse Boundary",
            "",
            "- 必须复用 M7 golden reference、M8R exact-match flow、M9 binding matrices、M10 source-backed trace、M11 config variation evidence、T1 inventory。",
            "- 不能把 access_module、floorplan_proxy、historical hybrid reference、access-view complete SRAM prototype 当作最终物理实现依据。",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _build_progress_md(
    *,
    asset_rows: list[dict[str, Any]],
    current_missing_or_partial_assets: list[str],
    next_assets_to_fill_in_order: list[str],
    current_claim_boundary: dict[str, Any],
) -> str:
    lines = [
        "# Netlist-to-Layout Progress",
        "",
        "## Asset Status",
        "",
    ]
    for row in asset_rows:
        lines.extend(
            [
                f"### {row['asset_id']}",
                "",
                f"- asset_name: `{row['asset_name']}`",
                f"- status_level: `{row['status_level']}`",
                f"- evidence_paths: `{'; '.join(row['evidence_paths'])}`",
                f"- blocking_for_next_stage: `{row['blocking_for_next_stage']}`",
                f"- next_action: `{row['next_action']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Current Missing Or Partial Assets",
            "",
            f"- current_missing_or_partial_assets: `{', '.join(current_missing_or_partial_assets)}`",
            "",
            "## Next Assets To Fill In Order",
            "",
            f"- next_assets_to_fill_in_order: `{', '.join(next_assets_to_fill_in_order)}`",
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for key, value in current_claim_boundary.items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def _build_status_md(
    *,
    asset_rows: list[dict[str, Any]],
    goal_files: list[str],
    progress_files: list[str],
    current_missing_or_partial_assets: list[str],
    next_assets_to_fill_in_order: list[str],
    current_claim_boundary: dict[str, Any],
) -> str:
    lines = [
        "# OpenYield SRAM LayoutGen Project Status",
        "",
        "## 1. Current Correct Goal",
        "",
        "在已确认的 M10 source-backed translator v2 与 M11 config/variation 证据基础上，审计并补齐 netlist-to-layout 所需的十项资产，明确哪些可复用、哪些必须废弃、哪些仍待补齐。",
        "",
        "## 2. Current Stage",
        "",
        "- current_stage: `M12`",
        "- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`",
        "- human_klayout_review_required_every_stage: `True`",
        "- can_enter_next_stage_without_human_review: `False`",
        "",
        "## 3. Goal / Progress Files",
        "",
        f"- goal_files: `{'; '.join(goal_files)}`",
        f"- progress_files: `{'; '.join(progress_files)}`",
        "",
        "## 4. Ten Required Assets",
        "",
    ]
    for row in asset_rows:
        lines.append(
            f"- {row['asset_id']}: `{row['status_level']}` evidence=`{'; '.join(row['evidence_paths'])}` next=`{row['next_action']}`"
        )
    lines.extend(
        [
            "",
            "## 5. Current Missing Or Partial Assets",
            "",
            f"- current_missing_or_partial_assets: `{', '.join(current_missing_or_partial_assets)}`",
            f"- next_assets_to_fill_in_order: `{', '.join(next_assets_to_fill_in_order)}`",
            "",
            "## 6. Current Claim Boundary",
            "",
        ]
    )
    for key, value in current_claim_boundary.items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def run_m12_ten_asset_audit(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    openyield_root: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    openyield_root = openyield_root.resolve()
    out_dir = out_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    status = _read_json(status_json)
    m10h = _read_json(repo_root / "docs/M10H_confirm_source_backed_translator_report.json")
    m11 = _read_json(repo_root / "docs/M11_openyield_config_variation_report.json")
    m11h = _optional_json(repo_root / "docs/M11H_confirm_config_aware_translator_report.json")
    module_inventory_rows = _read_csv_rows(repo_root / "docs/mapping/openyield_module_gds_inventory.csv")
    goal_files, progress_files = _discover_goal_progress_files(repo_root)
    workdir_inventory_rows, workdir_counts = _scan_workdir(repo_root)
    asset_rows = _build_asset_rows(
        repo_root=repo_root,
        status=status,
        m10h=m10h,
        m11=m11,
        m11h=m11h,
        module_inventory_rows=module_inventory_rows,
    )

    current_claim_boundary = {
        "can_claim_source_backed_translator_v2": True,
        "can_claim_config_aware_translator_v3": bool(m11h is not None and m11.get("can_claim_config_aware_translator_v3")),
        "can_claim_full_raw_openyield_netlist_compiler": False,
        "can_claim_drc_clean": False,
        "can_claim_lvs_clean": False,
        "can_claim_signoff_ready": False,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
    }
    current_missing_or_partial_assets = [row["asset_id"] for row in asset_rows if row["status_level"] != "COMPLETE"]
    next_plan_rows = [
        {
            "sequence": 1,
            "stage_id": "M11H" if m11h is None else "M11A",
            "why_now": "Clear the config-aware translator claim gate before expanding substitution work." if m11h is None else "Start module GDS qualification immediately after M11 is already source-backed and config-aware enough for reuse.",
            "depends_on": "M11 outputs" if m11h is None else "M11 outputs and M10/M11 reusable artifacts",
            "blocks_assets": "SRAM_CONFIGURATION;VERIFICATION_AND_TRACE" if m11h is None else "PHYSICAL_IMPLEMENTATION_LIBRARY;PIN_BBOX_RAIL_METADATA",
            "entry_condition": "docs/M11H_confirm_config_aware_translator_report.json missing" if m11h is None else "M11H already cleared or waived by existing confirmation file",
        },
        {
            "sequence": 2,
            "stage_id": "M11A",
            "why_now": "Qualify OpenYield module GDS before treating them as hardmacro candidates.",
            "depends_on": "M11H or accepted M11 claim boundary",
            "blocks_assets": "PHYSICAL_IMPLEMENTATION_LIBRARY",
            "entry_condition": "Need per-module qualification and replacement boundary",
        },
        {
            "sequence": 3,
            "stage_id": "M11B",
            "why_now": "Only qualified modules should feed pin/bbox/rail extraction.",
            "depends_on": "M11A",
            "blocks_assets": "PIN_BBOX_RAIL_METADATA;POWER_PLAN",
            "entry_condition": "Qualified module GDS list available",
        },
        {
            "sequence": 4,
            "stage_id": "M11C",
            "why_now": "Selective hardmacro substitution smoke proves floorplan and placement compatibility.",
            "depends_on": "M11A;M11B",
            "blocks_assets": "FLOORPLAN_RULES;PLACEMENT_RULES",
            "entry_condition": "Qualified modules plus verified metadata available",
        },
        {
            "sequence": 5,
            "stage_id": "M12A",
            "why_now": "Generate variation GDS for 4x32_wpr2 and 16x16_wpr1.",
            "depends_on": "M11H;M11C",
            "blocks_assets": "SRAM_CONFIGURATION;ROUTING_RULES",
            "entry_condition": "Variation-aware inputs can be driven through the locked flow extensions",
        },
        {
            "sequence": 6,
            "stage_id": "M12B",
            "why_now": "Adapt routing and power policy to variation and substitution outputs.",
            "depends_on": "M12A",
            "blocks_assets": "ROUTING_RULES;POWER_PLAN",
            "entry_condition": "Variation GDS evidence exists",
        },
        {
            "sequence": 7,
            "stage_id": "M13",
            "why_now": "Only after physical qualification and variation proof should DRC/LVS feasibility and equivalence trace run.",
            "depends_on": "M11A;M11B;M11C;M12A;M12B",
            "blocks_assets": "VERIFICATION_AND_TRACE",
            "entry_condition": "Physical and routing/power deltas materially closed",
        },
    ]
    recommended_next_stage = next_plan_rows[0]["stage_id"]
    next_assets_to_fill_in_order = [row["stage_id"] for row in next_plan_rows]

    backlog_rows = [
        {
            "asset_id": row["asset_id"],
            "asset_name": row["asset_name"],
            "status_level": row["status_level"],
            "blocking_for_next_stage": row["blocking_for_next_stage"],
            "blocking_reason": row["blocking_reason"],
            "next_action": row["next_action"],
            "next_stage_to_fill": row["next_stage_to_fill"],
            "priority": row["priority"],
        }
        for row in asset_rows
        if row["status_level"] != "COMPLETE"
    ]

    asset_matrix_csv_path = out_dir / "M12_ten_required_assets_matrix.csv"
    asset_matrix_md_path = out_dir / "M12_ten_required_assets_matrix.md"
    asset_status_json_path = out_dir / "M12_ten_required_assets_status.json"
    asset_status_md_path = out_dir / "M12_ten_required_assets_status.md"
    inventory_csv_path = out_dir / "M12_workdir_asset_evidence_inventory.csv"
    inventory_md_path = out_dir / "M12_workdir_asset_evidence_inventory.md"
    backlog_csv_path = out_dir / "M12_missing_asset_backlog.csv"
    backlog_md_path = out_dir / "M12_missing_asset_backlog.md"
    next_plan_md_path = out_dir / "M12_next_fill_plan.md"
    reused_md_path = out_dir / "M12_reused_previous_artifacts.md"
    deprecated_md_path = out_dir / "M12_deprecated_artifacts.md"

    write_json(
        asset_status_json_path,
        {
            "asset_count_total": len(asset_rows),
            "asset_complete_count": sum(1 for row in asset_rows if row["status_level"] == "COMPLETE"),
            "asset_partial_count": sum(1 for row in asset_rows if row["status_level"] == "PARTIAL"),
            "asset_missing_count": sum(1 for row in asset_rows if row["status_level"] == "MISSING"),
            "assets": asset_rows,
        },
    )
    write_text(
        asset_status_md_path,
        _render_md(
            "M12 Ten Required Assets Status",
            [f"- `{row['asset_id']}` => `{row['status_level']}` : {row['evidence_summary']}" for row in asset_rows],
        ),
    )
    write_csv(asset_matrix_csv_path, ASSET_FIELDNAMES, asset_rows)
    write_text(asset_matrix_md_path, _render_asset_matrix_md(asset_rows))
    write_csv(inventory_csv_path, WORKDIR_INVENTORY_FIELDNAMES, workdir_inventory_rows)
    write_text(inventory_md_path, _render_inventory_md(workdir_inventory_rows))
    write_csv(backlog_csv_path, BACKLOG_FIELDNAMES, backlog_rows)
    write_text(backlog_md_path, _render_backlog_md(backlog_rows))
    write_text(next_plan_md_path, _render_next_plan_md(next_plan_rows, recommended_next_stage))
    write_text(
        reused_md_path,
        _render_md(
            "M12 Reused Previous Artifacts",
            [
                f"- `{item['artifact']}` path=`{item['path']}` purpose=`{item['reuse_purpose']}`"
                for item in m11["reused_previous_artifacts"]
            ],
        ),
    )
    deprecated_lines = []
    for item in status.get("deprecated_artifacts", []):
        deprecated_lines.append(
            f"- `{item['artifact_name']}` path=`{item['path']}` reason=`{item['deprecated_reason']}`"
        )
    for item in m11["deprecated_previous_artifacts"]:
        deprecated_lines.append(f"- `{item['artifact']}` path=`{item['path']}` reason=`{item['deprecated_reason']}`")
    write_text(deprecated_md_path, _render_md("M12 Deprecated Artifacts", deprecated_lines))

    mapping_dir = repo_root / "docs/mapping"
    write_csv(mapping_dir / "M12_ten_required_assets_matrix.csv", ASSET_FIELDNAMES, asset_rows)
    write_csv(mapping_dir / "M12_workdir_asset_evidence_inventory.csv", WORKDIR_INVENTORY_FIELDNAMES, workdir_inventory_rows)
    write_csv(mapping_dir / "M12_missing_asset_backlog.csv", BACKLOG_FIELDNAMES, backlog_rows)
    write_csv(mapping_dir / "M12_next_fill_plan.csv", NEXT_PLAN_FIELDNAMES, next_plan_rows)

    complete_count = sum(1 for row in asset_rows if row["status_level"] == "COMPLETE")
    partial_count = sum(1 for row in asset_rows if row["status_level"] == "PARTIAL")
    missing_count = sum(1 for row in asset_rows if row["status_level"] == "MISSING")
    invalidated_count = sum(1 for row in asset_rows if row["status_level"] == "INVALIDATED")
    needs_review_count = sum(1 for row in asset_rows if row["status_level"] == "NEEDS_HUMAN_REVIEW")
    blocking_asset_count = sum(1 for row in asset_rows if row["blocking_for_next_stage"])
    remaining_blockers = [
        "Human KLayout review remains required before entering any next stage.",
        "M11H confirmation file is missing; config-aware v3 claim stays below gate." if m11h is None else "M11H gate cleared; proceed with qualification before new claims.",
        "OpenYield module GDS hardmacro substitution is still unqualified.",
        "DRC/LVS/signoff claims remain unavailable.",
    ]

    goal_md_path = repo_root / goal_files[0]
    progress_md_path = repo_root / progress_files[0]
    write_text(goal_md_path, _build_goal_md(asset_rows))
    write_text(
        progress_md_path,
        _build_progress_md(
            asset_rows=asset_rows,
            current_missing_or_partial_assets=current_missing_or_partial_assets,
            next_assets_to_fill_in_order=next_assets_to_fill_in_order,
            current_claim_boundary=current_claim_boundary,
        ),
    )

    status["current_stage"] = "M12"
    status["next_stage"] = "WAIT_HUMAN_KLAYOUT_REVIEW"
    status["human_klayout_review_required_every_stage"] = True
    status["can_enter_next_stage_without_human_review"] = False
    status["goal_files"] = goal_files
    status["progress_files"] = progress_files
    status["ten_required_assets_for_netlist_to_layout"] = [
        {
            "asset_id": row["asset_id"],
            "asset_name": row["asset_name"],
            "status_level": row["status_level"],
            "evidence_paths": row["evidence_paths"],
            "blocking_for_next_stage": row["blocking_for_next_stage"],
            "next_action": row["next_action"],
        }
        for row in asset_rows
    ]
    status["current_missing_or_partial_assets"] = current_missing_or_partial_assets
    status["next_assets_to_fill_in_order"] = next_assets_to_fill_in_order
    status["cannot_claim_until_completed"] = [
        "full raw OpenYield netlist compiler",
        "qualified OpenYield module GDS hardmacro substitution",
        "DRC clean",
        "LVS clean",
        "signoff ready",
    ]
    status["current_claim_boundary"] = current_claim_boundary
    status["last_M12_report"] = {
        "status_file_read": True,
        "status_file_updated": True,
        "reused_previous_artifacts_available": True,
        "deprecated_previous_artifacts_recorded": True,
        "ten_required_assets_added_to_goal": True,
        "ten_required_assets_added_to_progress": True,
        "workdir_scan_completed": True,
        "workdir_root": str(repo_root),
        "openyield_root_checked": str(openyield_root),
        "asset_count_total": len(asset_rows),
        "asset_complete_count": complete_count,
        "asset_partial_count": partial_count,
        "asset_missing_count": missing_count,
        "asset_invalidated_count": invalidated_count,
        "asset_needs_review_count": needs_review_count,
        "blocking_asset_count": blocking_asset_count,
        "missing_or_partial_assets": current_missing_or_partial_assets,
        "next_assets_to_fill_in_order": next_assets_to_fill_in_order,
        "recommended_next_stage": recommended_next_stage,
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_M12_blockers": remaining_blockers,
        "remaining_M12_blockers_count": len(remaining_blockers),
    }
    write_json(status_json, status)
    write_text(
        status_md,
        _build_status_md(
            asset_rows=asset_rows,
            goal_files=goal_files,
            progress_files=progress_files,
            current_missing_or_partial_assets=current_missing_or_partial_assets,
            next_assets_to_fill_in_order=next_assets_to_fill_in_order,
            current_claim_boundary=current_claim_boundary,
        ),
    )

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "reused_previous_artifacts_available": True,
        "deprecated_previous_artifacts_recorded": True,
        "ten_required_assets_added_to_goal": True,
        "ten_required_assets_added_to_progress": True,
        "workdir_scan_completed": True,
        "workdir_root": str(repo_root),
        "openyield_root_checked": str(openyield_root),
        "asset_count_total": len(asset_rows),
        "asset_complete_count": complete_count,
        "asset_partial_count": partial_count,
        "asset_missing_count": missing_count,
        "asset_invalidated_count": invalidated_count,
        "asset_needs_review_count": needs_review_count,
        "blocking_asset_count": blocking_asset_count,
        "missing_or_partial_assets": current_missing_or_partial_assets,
        "next_assets_to_fill_in_order": next_assets_to_fill_in_order,
        "recommended_next_stage": recommended_next_stage,
        "can_claim_source_backed_translator_v2": True,
        "can_claim_config_aware_translator_v3": current_claim_boundary["can_claim_config_aware_translator_v3"],
        "can_claim_full_raw_openyield_netlist_compiler": False,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
        "can_claim_drc_clean": False,
        "can_claim_lvs_clean": False,
        "can_claim_signoff_ready": False,
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_M12_blockers": remaining_blockers,
        "remaining_M12_blockers_count": len(remaining_blockers),
        "goal_files": goal_files,
        "progress_files": progress_files,
        "workdir_scan_file_count_by_root": workdir_counts,
        "m11h_present": m11h is not None,
    }
    write_json(out_json, report)
    write_text(
        out_report,
        _render_md(
            "M12 Ten Asset Audit Report",
            [
                f"- asset_count_total: `{report['asset_count_total']}`",
                f"- asset_complete_count: `{report['asset_complete_count']}`",
                f"- asset_partial_count: `{report['asset_partial_count']}`",
                f"- asset_missing_count: `{report['asset_missing_count']}`",
                f"- blocking_asset_count: `{report['blocking_asset_count']}`",
                f"- recommended_next_stage: `{report['recommended_next_stage']}`",
                f"- can_claim_source_backed_translator_v2: `{report['can_claim_source_backed_translator_v2']}`",
                f"- can_claim_config_aware_translator_v3: `{report['can_claim_config_aware_translator_v3']}`",
                f"- can_claim_full_raw_openyield_netlist_compiler: `{report['can_claim_full_raw_openyield_netlist_compiler']}`",
                f"- can_claim_openyield_module_gds_hardmacro_substitution: `{report['can_claim_openyield_module_gds_hardmacro_substitution']}`",
                f"- human_klayout_review_required: `{report['human_klayout_review_required']}`",
                f"- can_enter_next_stage_before_human_review: `{report['can_enter_next_stage_before_human_review']}`",
            ],
        ),
    )
    write_text(
        repo_root / "docs/evidence/M12_ten_asset_audit_summary.md",
        _render_md(
            "M12 Ten Asset Audit Summary",
            [
                f"- goal_files: `{'; '.join(goal_files)}`",
                f"- progress_files: `{'; '.join(progress_files)}`",
                f"- missing_or_partial_assets: `{', '.join(current_missing_or_partial_assets)}`",
                f"- recommended_next_stage: `{recommended_next_stage}`",
                f"- M11H_present: `{m11h is not None}`",
            ],
        ),
    )
    return report
