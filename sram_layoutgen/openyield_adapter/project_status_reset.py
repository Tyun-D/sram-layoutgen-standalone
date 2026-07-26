from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _md_table(columns: list[str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        values: list[str] = []
        for column in columns:
            value = row.get(column, "")
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            values.append(str(value).replace("\n", "<br>"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def _ordered_columns(rows: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    cols: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                cols.append(key)
    return cols


def _copy_or_mark(src: Path, dst: Path) -> dict[str, Any]:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return {"status": "COPIED", "source_path": str(src), "copied_path": str(dst)}
    return {"status": "NOT_FOUND", "source_path": str(src), "copied_path": ""}


@dataclass(frozen=True)
class ProjectStatusResetConfig:
    repo_root: Path
    out_status_md: Path
    out_status_json: Path
    out_review_dir: Path
    out_report_json: Path
    out_report_md: Path


class ProjectStatusReset:
    def __init__(self, config: ProjectStatusResetConfig) -> None:
        self.config = config

    def run(self) -> dict[str, Any]:
        cfg = self.config
        repo = cfg.repo_root
        mapping_dir = repo / "docs/mapping"
        evidence_dir = repo / "docs/evidence"
        review_dir = cfg.out_review_dir
        review_dir.mkdir(parents=True, exist_ok=True)

        module_root = repo / "outputs/openyield_module_gds"
        module_dirs = sorted([p for p in module_root.iterdir() if p.is_dir()]) if module_root.exists() else []
        first_round_rows: list[dict[str, Any]] = []
        for module_dir in module_dirs:
            gds_path = module_dir / f"{module_dir.name}.gds"
            first_round_rows.append(
                {
                    "module_name": module_dir.name,
                    "module_dir": str(module_dir.relative_to(repo)),
                    "gds_exists": gds_path.exists(),
                    "gds_path": str(gds_path.relative_to(repo)) if gds_path.exists() else "NOT_FOUND",
                    "pins_json": str((module_dir / "pins.json").relative_to(repo)) if (module_dir / "pins.json").exists() else "NOT_FOUND",
                    "bbox_json": str((module_dir / "bbox.json").relative_to(repo)) if (module_dir / "bbox.json").exists() else "NOT_FOUND",
                    "rail_report_json": str((module_dir / "rail_report.json").relative_to(repo)) if (module_dir / "rail_report.json").exists() else "NOT_FOUND",
                    "generator_manifest_json": str((module_dir / "generator_manifest.json").relative_to(repo)) if (module_dir / "generator_manifest.json").exists() else "NOT_FOUND",
                    "classification": "FIRST_ROUND_MODULE_GDS_CANDIDATE",
                    "reuse_decision": "RE-AUDIT_BEFORE_REUSE",
                    "risk": "May be physical module, candidate, or placeholder-equivalent; must be re-audited in L0.",
                }
            )

        reusable_rows = [
            {
                "artifact_name": "layoutgen_generator_code",
                "path": "sram_layoutgen/",
                "artifact_type": "generator_codebase",
                "why_reusable": "This is the correct底座 for real SRAM GDS generation.",
                "reuse_scope": "L0-L4",
                "risk": "Must be re-bound to OpenYield semantics carefully.",
            },
            {
                "artifact_name": "first_round_openyield_module_gds",
                "path": "outputs/openyield_module_gds/",
                "artifact_type": "module_gds_input",
                "why_reusable": "Important input candidates and metadata source.",
                "reuse_scope": "L0-L2",
                "risk": "Not all modules are guaranteed final physical implementations.",
            },
            {
                "artifact_name": "R1_layout_intent",
                "path": "docs/ + outputs/openyield_layout_intent/current_supported_config/",
                "artifact_type": "semantic_intent",
                "why_reusable": "Carries OpenYield layout intent and role mapping.",
                "reuse_scope": "L0-L4",
                "risk": "Intent must be mapped onto real layoutgen generation flow.",
            },
            {
                "artifact_name": "R2_generator_architecture",
                "path": "docs/ + scripts/openyield_R2_generator_architecture_design.py",
                "artifact_type": "architecture",
                "why_reusable": "Defines OpenYield-driven architecture concepts.",
                "reuse_scope": "L0-L4",
                "risk": "Architecture must not be confused with final physical proof.",
            },
            {
                "artifact_name": "C0_to_C6_validation_framework",
                "path": "docs/ + scripts/ + tests/ + outputs/openyield_*",
                "artifact_type": "audit_and_validation",
                "why_reusable": "Provides reusable report schema and regression hooks.",
                "reuse_scope": "L0-L4",
                "risk": "Some report conclusions must be downgraded/reclassified.",
            },
            {
                "artifact_name": "openram_source_and_reference_gds",
                "path": "/data1/qujh/OpenRAM + outputs/layout_prototype/baseline_legacy/",
                "artifact_type": "reference_rule_sample",
                "why_reusable": "Useful as rule/sample/visual reference only.",
                "reuse_scope": "L0-L4",
                "risk": "Must not be mistaken for final OpenYield GDS.",
            },
            {
                "artifact_name": "layoutgen_baseline_reference_gds",
                "path": "outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.complete.gds",
                "artifact_type": "visual_reference_sample",
                "why_reusable": "Useful as review baseline and visual/structural comparator.",
                "reuse_scope": "L0-L4 review",
                "risk": "Do not use as final OpenYield output.",
            },
            {
                "artifact_name": "module_gds_generators_py",
                "path": "sram_layoutgen/openyield_adapter/module_gds_generators.py",
                "artifact_type": "module_generator",
                "why_reusable": "Direct hook into first-round OpenYield module GDS generation.",
                "reuse_scope": "L0-L2",
                "risk": "Must re-audit generated modules before trust.",
            },
        ]

        deprecated_rows = [
            {
                "artifact_name": "openyield_complete_sram_gds_claim",
                "path": "outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds",
                "deprecated_reason": "Reclassified as OpenYield-connected access-view GDS prototype, not real complete SRAM GDS.",
                "do_not_use_as_final": True,
            },
            {
                "artifact_name": "access_module_cells",
                "path": "*_access_module",
                "deprecated_reason": "Cannot serve as SRAM physical implementation主体.",
                "do_not_use_as_final": True,
            },
            {
                "artifact_name": "floorplan_proxy_cells",
                "path": "floorplan_proxy*",
                "deprecated_reason": "Only acceptable for review/floorplan proof, not final physical module hierarchy.",
                "do_not_use_as_final": True,
            },
            {
                "artifact_name": "access_view_route",
                "path": "C4 access-view signal route shapes",
                "deprecated_reason": "Useful as semantic/prototype evidence, not sufficient as physical complete claim basis.",
                "do_not_use_as_final": True,
            },
            {
                "artifact_name": "access_view_power_stitch",
                "path": "C5 access-view power stitch shapes",
                "deprecated_reason": "Useful as prototype geometry evidence, not final physical implementation proof.",
                "do_not_use_as_final": True,
            },
            {
                "artifact_name": "synthesized_pin_complete_claim_support",
                "path": "C2 synthesized pin access",
                "deprecated_reason": "Cannot alone support physical complete claim.",
                "do_not_use_as_final": True,
            },
        ]

        result_rows = [
            {
                "result_name": "First-round OpenYield module GDS generation",
                "path": "outputs/openyield_module_gds/",
                "what_is_valid": "Module GDS files, pins/bbox/rail metadata, and generator manifests exist for 20 modules.",
                "what_is_not_valid": "Not yet proven that every module is the right physical implementation for final SRAM assembly.",
                "can_reuse": True,
                "reuse_scope": "L0-L2 input audit and regeneration",
                "risk": "Must distinguish real module vs candidate vs replaceable artifact.",
            },
            {
                "result_name": "R0 OpenRAM audit",
                "path": "docs/ and OpenRAM source audit artifacts",
                "what_is_valid": "Rule/reference understanding of SRAM physical organization.",
                "what_is_not_valid": "OpenRAM output is not final OpenYield output.",
                "can_reuse": True,
                "reuse_scope": "L0-L4 reference only",
                "risk": "Do not regress into OpenRAM black-box flow.",
            },
            {
                "result_name": "R1 layout intent",
                "path": "outputs/openyield_layout_intent/current_supported_config/",
                "what_is_valid": "OpenYield module/net semantics and intent mapping.",
                "what_is_not_valid": "Intent alone is not physical proof.",
                "can_reuse": True,
                "reuse_scope": "L0-L4 semantic driver",
                "risk": "Must be bound to real layoutgen generation path.",
            },
            {
                "result_name": "R2 generator architecture",
                "path": "scripts/openyield_R2_generator_architecture_design.py + reports",
                "what_is_valid": "Architecture decomposition and generator boundary planning.",
                "what_is_not_valid": "Does not prove final GDS implementation quality.",
                "can_reuse": True,
                "reuse_scope": "L0-L4 planning",
                "risk": "Must reconnect to real layoutgen assembly path.",
            },
            {
                "result_name": "C0 gap audit",
                "path": "outputs/openyield_complete_gds_gap_audit/current_supported_config/",
                "what_is_valid": "Accurate evidence for contract/approximate/missing pin gaps in old prototype route.",
                "what_is_not_valid": "Its closure results must be reinterpreted after route reset.",
                "can_reuse": True,
                "reuse_scope": "L0-L4 risk baseline",
                "risk": "Do not treat old closure counts as sufficient physical completeness proof.",
            },
            {
                "result_name": "C1 physical rule extraction",
                "path": "outputs/openyield_complete_gds_rule_extraction/current_supported_config/",
                "what_is_valid": "Useful rulebook and comparison baseline.",
                "what_is_not_valid": "Not a substitute for real layoutgen generation.",
                "can_reuse": True,
                "reuse_scope": "L0-L4 rule reference",
                "risk": "Must not drift into source-only mimicry.",
            },
            {
                "result_name": "C2 pin access repair",
                "path": "outputs/openyield_pin_access_repair/current_supported_config/",
                "what_is_valid": "Repaired/synthesized pin access metadata and access views.",
                "what_is_not_valid": "Synthesized pin access cannot alone justify physical-complete claim.",
                "can_reuse": True,
                "reuse_scope": "L0-L2 audit input and optional metadata hints",
                "risk": "Must be re-audited against real layoutgen module generation.",
            },
            {
                "result_name": "C3 floorplan reconstruction",
                "path": "outputs/openyield_complete_floorplan/current_supported_config/",
                "what_is_valid": "Useful placement/floorplan intent and review evidence.",
                "what_is_not_valid": "Proxy-floorplan GDS is not final real macro assembly.",
                "can_reuse": True,
                "reuse_scope": "L0-L4 review/reference",
                "risk": "Do not keep floorplan_proxy as implementation hierarchy.",
            },
            {
                "result_name": "C4 signal routing",
                "path": "outputs/openyield_complete_signal_routing/current_supported_config/",
                "what_is_valid": "Geometry-backed semantic routing prototype and validation schema.",
                "what_is_not_valid": "Based on access-view modules, not final physical module hierarchy.",
                "can_reuse": True,
                "reuse_scope": "L0-L4 evidence/reference",
                "risk": "Do not reuse as final physical routing implementation.",
            },
            {
                "result_name": "C5 power stitching",
                "path": "outputs/openyield_complete_power_network/current_supported_config/",
                "what_is_valid": "Geometry-backed semantic power connectivity prototype and validation schema.",
                "what_is_not_valid": "Still layered on access-view hierarchy.",
                "can_reuse": True,
                "reuse_scope": "L0-L4 evidence/reference",
                "risk": "Do not reuse as final physical power implementation.",
            },
            {
                "result_name": "C6 final access-view GDS",
                "path": "outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds",
                "what_is_valid": "A parseable OpenYield-connected access-view GDS prototype with report bundle.",
                "what_is_not_valid": "Cannot be claimed as real complete SRAM GDS anymore.",
                "can_reuse": True,
                "reuse_scope": "Review/reference only",
                "risk": "Must be explicitly downgraded.",
            },
        ]

        code_inventory_rows: list[dict[str, Any]] = []
        code_targets = [
            "sram_layoutgen/openyield_adapter/module_gds_generators.py",
            "sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "sram_layoutgen/openyield_adapter/array_aggregation.py",
            "sram_layoutgen/gds_writer.py",
            "sram_layoutgen/gds_util.py",
            "sram_layoutgen/openyield_adapter/routing_power_pin.py",
            "sram_layoutgen/openyield_adapter/hardcell_power_rail_continuity.py",
            "sram_layoutgen/openyield_adapter/sram_power_planner.py",
            "sram_layoutgen/openyield_adapter/sram_pin_exporter.py",
            "sram_layoutgen/openram_placement.py",
            "sram_layoutgen/openyield_adapter/wordlinedriver_placement.py",
            "sram_layoutgen/openyield_adapter/senseamp_placement.py",
            "sram_layoutgen/openyield_adapter/writedriver_placement.py",
            "sram_layoutgen/openyield_adapter/dff_array_placement.py",
            "sram_layoutgen/openyield_adapter/columnmux_placement.py",
        ]
        for rel in code_targets:
            path = repo / rel
            code_inventory_rows.append(
                {
                    "reference_item": Path(rel).name,
                    "path": rel,
                    "exists": path.exists(),
                    "classification": "LAYOUTGEN_BASE_CAPABILITY" if path.exists() else "NOT_FOUND",
                    "what_it_covers": "generator/power/pin/placement/assembly capability" if path.exists() else "NOT_FOUND",
                    "next_phase_mapping": "L0-L4" if path.exists() else "NOT_FOUND",
                }
            )

        dependency_rows = [
            {
                "next_stage": "L0",
                "depends_on": "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.* + review GDS + module GDS inventory + generator code inventory",
                "why_needed": "Audit real generator path and first-round module validity before any new physical generation.",
                "human_review_required": True,
            },
            {
                "next_stage": "L1",
                "depends_on": "L0 audit results + OpenYield semantics + layoutgen capability map",
                "why_needed": "Bind OpenYield module/net semantics onto real layoutgen generator hooks.",
                "human_review_required": True,
            },
            {
                "next_stage": "L2",
                "depends_on": "L1 bindings + first-round module replacement decisions",
                "why_needed": "Regenerate OpenYield real module GDS through layoutgen-based path.",
                "human_review_required": True,
            },
            {
                "next_stage": "L3",
                "depends_on": "L2 real module GDS + layoutgen top-level assembly path",
                "why_needed": "Generate layoutgen-based OpenYield SRAM top GDS.",
                "human_review_required": True,
            },
            {
                "next_stage": "L4",
                "depends_on": "L3 top GDS + real signal/power integration",
                "why_needed": "Do final real connection, power, validation, and delivery.",
                "human_review_required": True,
            },
        ]

        previous_access_src = repo / "outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds"
        previous_access_dst = review_dir / "previous_access_view_final.gds"
        layoutgen_ref_src = repo / "outputs/layout_prototype/baseline_legacy/sram_8x64_wpr4_fd45.complete.gds"
        layoutgen_ref_dst = review_dir / "layoutgen_reference.gds"
        candidate_src = repo / "outputs/openyield_top_level_assembly/current_supported_config/openyield_top_level_candidate.gds"
        candidate_dst = review_dir / "first_round_openyield_candidate.gds"
        review_entries = [
            {
                "review_name": "previous_access_view_final",
                **_copy_or_mark(previous_access_src, previous_access_dst),
                "top_cell_name": "openyield_complete_sram",
                "what_to_check_in_klayout": "Confirm this looks like access-view/proxy assembly rather than a real SRAM macro.",
                "expected_visual_features": "Access-view style hierarchy, abstract connectivity, smaller GDS footprint.",
                "known_risks": "Cannot be used as final physical SRAM GDS.",
                "can_enter_next_stage_after_user_confirmation": True,
            },
            {
                "review_name": "layoutgen_reference",
                **_copy_or_mark(layoutgen_ref_src, layoutgen_ref_dst),
                "top_cell_name": "sram_8x64_wpr4_fd45" if layoutgen_ref_src.exists() else "NOT_FOUND",
                "what_to_check_in_klayout": "Use as visual/structural comparator for what a real SRAM macro should resemble.",
                "expected_visual_features": "Dense array-centric macro, real periphery organization, more SRAM-like visual structure.",
                "known_risks": "Reference only; not final OpenYield output.",
                "can_enter_next_stage_after_user_confirmation": True,
            },
            {
                "review_name": "first_round_openyield_candidate",
                **_copy_or_mark(candidate_src, candidate_dst),
                "top_cell_name": "openyield_top_level_candidate" if candidate_src.exists() else "NOT_FOUND",
                "what_to_check_in_klayout": "Assess whether first-round top candidate is closer to real physical assembly than the access-view final.",
                "expected_visual_features": "May expose earlier top-level assembly direction and generator limitations.",
                "known_risks": "Candidate only; may not be structurally valid final macro.",
                "can_enter_next_stage_after_user_confirmation": True,
            },
        ]
        review_manifest = {
            "human_klayout_review_required": True,
            "can_enter_L0_before_human_review": False,
            "review_gds": review_entries,
        }
        _json_dump(review_dir / "review_gds_manifest.json", review_manifest)
        _write_text(review_dir / "review_gds_manifest.md", _md_table(_ordered_columns(review_entries), review_entries))

        status_json = {
            "project_goal": "基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。",
            "current_route": [
                "S0：全部成果整理与路线重置",
                "L0：layoutgen 原生成路径与第一轮 OpenYield 模块 GDS 审计",
                "L1：OpenYield module/net → layoutgen generator 绑定",
                "L2：重新生成 OpenYield real module GDS",
                "L3：layoutgen-based OpenYield SRAM top GDS 生成",
                "L4：真实连接、电源、验证与最终交付",
            ],
            "current_stage": "S0",
            "next_stage": "L0",
            "must_read_this_file_before_every_task": True,
            "must_update_this_file_after_every_task": True,
            "human_klayout_review_required_every_stage": True,
            "can_enter_next_stage_without_human_review": False,
            "important_results": result_rows,
            "reusable_artifacts": reusable_rows,
            "deprecated_artifacts": deprecated_rows,
            "cannot_claim": [
                "DRC clean",
                "LVS clean",
                "timing closure",
                "signoff-ready",
                "tapeout-ready",
            ],
            "last_user_correction": "C6 openyield_complete_sram.gds 不能再 claim 为真实完整 SRAM GDS，必须降级为 OpenYield-connected access-view GDS prototype，并将路线重置为 layoutgen-based OpenYield route。",
            "current_wrong_route_to_avoid": "不要继续把 *_access_module / floorplan_proxy / access-view route or power stitch 当作真实 SRAM physical implementation 主体，也不要说以旧 GDS 为底座。",
            "next_task_summary": "S0 完成后进入 L0：layoutgen 原生成路径与第一轮 OpenYield module GDS 审计，但必须先经过人工 KLayout review 确认。",
        }

        status_md_lines = [
            "# OpenYield SRAM LayoutGen Project Status",
            "",
            "## 1. Current Correct Goal",
            "",
            "基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。",
            "",
            "## 2. Current Route",
            "",
            "- S0：全部成果整理与路线重置",
            "- L0：layoutgen 原生成路径与第一轮 OpenYield 模块 GDS 审计",
            "- L1：OpenYield module/net → layoutgen generator 绑定",
            "- L2：重新生成 OpenYield real module GDS",
            "- L3：layoutgen-based OpenYield SRAM top GDS 生成",
            "- L4：真实连接、电源、验证与最终交付",
            "",
            "## 3. Important Results So Far",
            "",
            _md_table(_ordered_columns(result_rows), result_rows).rstrip(),
            "",
            "## 4. Reclassified / Downgraded Results",
            "",
            "`outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds` 从 complete SRAM GDS 降级为 access-view prototype。",
            "",
            "原因：",
            "- top hierarchy 主要是 `*_access_module`。",
            "- 没有真实 bitcell array 主体。",
            "- 没有达到 layoutgen/OpenRAM 的物理完整度。",
            "- 视觉上不像真实 SRAM macro。",
            "- `DRC marker_count = 431`。",
            "- LVS 未运行。",
            "- 不能 claim DRC/LVS/signoff。",
            "",
            "## 5. Reusable Artifacts",
            "",
            _md_table(_ordered_columns(reusable_rows), reusable_rows).rstrip(),
            "",
            "## 6. Deprecated / Do-Not-Use-As-Final Artifacts",
            "",
            _md_table(_ordered_columns(deprecated_rows), deprecated_rows).rstrip(),
            "",
            "## 7. Required Human Review Rule",
            "",
            "每个阶段必须生成 review GDS。每个阶段完成后，不能自动进入下一阶段。必须等待用户在 KLayout 打开 review GDS 并确认。若用户认为视觉/结构路线错误，必须立即停止并纠偏。",
            "",
            "## 8. GDS Review Requirements",
            "",
            _md_table(_ordered_columns(review_entries), review_entries).rstrip(),
            "",
            "## 9. Cannot Claim",
            "",
            "- DRC clean",
            "- LVS clean",
            "- timing closure",
            "- signoff-ready",
            "- tapeout-ready",
            "",
            "除非有真实工具证据。",
            "",
            "## 10. Next Immediate Task",
            "",
            "S0 完成后进入 L0：layoutgen 原生成路径与第一轮 OpenYield module GDS 审计。",
            "",
        ]
        _write_text(cfg.out_status_md, "\n".join(status_md_lines))
        _json_dump(cfg.out_status_json, status_json)

        _json_dump(repo / "docs/project_asset_reclassification_report.json", {
            "S0_project_status_reset_available": True,
            "project_status_md_available": cfg.out_status_md.exists(),
            "project_status_json_available": cfg.out_status_json.exists(),
            "reusable_artifact_inventory_available": True,
            "deprecated_artifact_inventory_available": True,
            "first_round_openyield_module_gds_inventory_available": True,
            "layoutgen_generator_code_inventory_available": True,
            "next_phase_dependency_matrix_available": True,
            "review_gds_manifest_available": True,
            "previous_result_downgraded": True,
            "access_view_gds_reclassified": True,
            "layoutgen_based_route_defined": True,
            "must_read_status_file_before_every_task": True,
            "must_update_status_file_after_every_task": True,
            "human_klayout_review_required_every_stage": True,
            "can_enter_next_stage_without_human_review": False,
            "current_stage": "S0",
            "next_stage": "L0",
            "remaining_S0_blockers": [],
            "remaining_S0_blockers_count": 0,
            "can_claim_S0_project_status_reset_done": True,
            "can_enter_L0_after_human_review": True,
            "reusable_artifact_count": len(reusable_rows),
            "deprecated_artifact_count": len(deprecated_rows),
            "first_round_openyield_module_gds_count": len(first_round_rows),
            "layoutgen_generator_code_inventory_count": len(code_inventory_rows),
        })
        report_payload = json.loads((repo / "docs/project_asset_reclassification_report.json").read_text(encoding="utf-8"))
        _write_text(
            repo / "docs/project_asset_reclassification_report.md",
            "# Project Asset Reclassification Report\n\n"
            + _md_table(_ordered_columns([report_payload]), [report_payload]),
        )

        _write_text(
            repo / "docs/project_result_downgrade_statement.md",
            "# Project Result Downgrade Statement\n\n"
            "`outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds` 不能再 claim 为真实完整 SRAM GDS。\n\n"
            "它现在重新定性为：`OpenYield-connected access-view GDS prototype`，也可描述为 `OpenYield 语义驱动的抽象几何连通原型`。\n\n"
            "正确路线是：以 layoutgen 生成器为底座；layoutgen/OpenRAM 生成的 GDS 只作为参考样本、回归样本和视觉对照。\n",
        )

        next_phase_plan = {
            "route_reset_summary": "以 layoutgen 原版图生成器代码能力为底座，以第一轮 OpenYield module GDS 生成成果为重要输入，以 OpenYield layout intent / net semantics 为驱动，重新接入真实 SRAM GDS 生成主干。",
            "next_phases": dependency_rows,
            "must_wait_for_human_review_before_L0": True,
        }
        _json_dump(repo / "docs/layoutgen_openyield_next_phase_plan.json", next_phase_plan)
        _write_text(
            repo / "docs/layoutgen_openyield_next_phase_plan.md",
            "# LayoutGen OpenYield Next Phase Plan\n\n"
            "正确说法是：以 layoutgen 生成器为底座；layoutgen / OpenRAM 生成的 GDS 只作为参考样本、回归样本和视觉对照。\n\n"
            + _md_table(_ordered_columns(dependency_rows), dependency_rows),
        )

        _write_csv(mapping_dir / "reusable_artifact_inventory.csv", _ordered_columns(reusable_rows), reusable_rows)
        _write_text(mapping_dir / "reusable_artifact_inventory.md", _md_table(_ordered_columns(reusable_rows), reusable_rows))
        _write_csv(mapping_dir / "deprecated_artifact_inventory.csv", _ordered_columns(deprecated_rows), deprecated_rows)
        _write_text(mapping_dir / "deprecated_artifact_inventory.md", _md_table(_ordered_columns(deprecated_rows), deprecated_rows))
        _write_csv(mapping_dir / "first_round_openyield_module_gds_inventory.csv", _ordered_columns(first_round_rows), first_round_rows)
        _write_text(mapping_dir / "first_round_openyield_module_gds_inventory.md", _md_table(_ordered_columns(first_round_rows), first_round_rows))
        _write_csv(mapping_dir / "layoutgen_generator_code_inventory.csv", _ordered_columns(code_inventory_rows), code_inventory_rows)
        _write_text(mapping_dir / "layoutgen_generator_code_inventory.md", _md_table(_ordered_columns(code_inventory_rows), code_inventory_rows))
        _write_csv(mapping_dir / "next_phase_dependency_matrix.csv", _ordered_columns(dependency_rows), dependency_rows)
        _write_text(mapping_dir / "next_phase_dependency_matrix.md", _md_table(_ordered_columns(dependency_rows), dependency_rows))

        _write_text(
            evidence_dir / "S0_project_status_reset_summary.md",
            "# S0 Project Status Reset Summary\n\n"
            "- `openyield_complete_sram.gds` 已降级为 access-view prototype。\n"
            "- 后续路线改为：layoutgen-based OpenYield route。\n"
            "- 每阶段必须先读/更新 `PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md/json`。\n"
            "- 每阶段必须产出 review GDS，并等待人工 KLayout 确认后才能进入下一阶段。\n"
            f"- 本次 review GDS manifest: `{(review_dir / 'review_gds_manifest.json').relative_to(repo)}`\n",
        )

        return report_payload
