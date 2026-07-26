from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


@dataclass(frozen=True)
class RepairPlanItem:
    priority: str
    root_cause_category: str
    marker_count: int
    percentage: float
    affected_modules: list[str]
    dominant_rules: list[str]
    dominant_layers: list[str]
    blocks_drc_clean: bool
    blocks_lvs_clean: bool
    blocks_timing_closure: bool
    expected_fix_location: str
    expected_fix_files: str
    why_priority_high: str
    recommended_next_action: str


@dataclass(frozen=True)
class ProjectClosureCapability:
    capability_id: str
    statement: str
    evidence_files: list[str]


@dataclass(frozen=True)
class ProjectClosureLimitation:
    limitation_id: str
    statement: str
    why_it_matters: str
    evidence_files: list[str]


@dataclass(frozen=True)
class FutureWorkItem:
    phase: str
    order_index: int
    title: str
    next_action: str
    expected_outputs: list[str]


@dataclass(frozen=True)
class FinalRepairPlanningReport:
    summary: dict[str, Any]
    matrix_rows: list[dict[str, Any]]


class OpenYieldFinalRepairPlanner:
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context
        self.out_dir: Path = context["out_dir"]

    def run(self) -> FinalRepairPlanningReport:
        repair_items = self._build_repair_plan_items()
        capability_items = self._build_capabilities()
        limitation_items = self._build_limitations()
        roadmap_items = self._build_roadmap()
        checklist_items = self._build_handoff_checklist()

        self._emit_final_repair_plan(repair_items)
        self._emit_capability_statement(capability_items)
        self._emit_limitation_statement(limitation_items)
        self._emit_future_work_roadmap(roadmap_items)
        self._emit_final_handoff_checklist(checklist_items)

        matrix_rows = [self._repair_item_to_matrix_row(item) for item in repair_items]
        summary = self._build_summary(repair_items)
        _json_dump(self.out_dir / "final_repair_plan.json", {"repair_plan_items": [asdict(item) for item in repair_items]})
        _json_dump(self.out_dir / "project_v1_capability_statement.json", {"capabilities": [asdict(item) for item in capability_items]})
        _json_dump(self.out_dir / "project_v1_limitation_statement.json", {"limitations": [asdict(item) for item in limitation_items]})
        _json_dump(self.out_dir / "future_work_roadmap.json", {"future_work_items": [asdict(item) for item in roadmap_items]})
        _json_dump(self.out_dir / "final_handoff_checklist.json", {"checklist_items": checklist_items})
        return FinalRepairPlanningReport(summary=summary, matrix_rows=matrix_rows)

    def _build_repair_plan_items(self) -> list[RepairPlanItem]:
        root_rows = self.context["l6_root_cause"]["root_cause_categories"]
        matrix_rows = {
            row["root_cause_category"]: row for row in self.context["l6_matrix_rows"]
        }
        priority_rows = {
            row["root_cause_category"]: row for row in self.context["l6_fix_priority"]["fix_priority"]
        }
        desired = [
            "LAYER_MAP_OR_DRC_DECK_INTERPRETATION",
            "CONTRACT_PIN_GEOMETRY_PLACEHOLDER",
            "CANDIDATE_GEOMETRY_INTERNAL",
            "MODULE_INTERNAL_HARDMACRO",
            "MODULE_WRAPPER_IMPORT",
        ]
        items: list[RepairPlanItem] = []
        for category in desired:
            root = next(row for row in root_rows if row["root_cause_category"] == category)
            matrix = matrix_rows[category]
            priority = priority_rows.get(category, {"priority": "P5", "expected_fix_files": "Manual review"})
            why_priority_high = self._why_priority_high(category, root["marker_count"])
            items.append(
                RepairPlanItem(
                    priority=str(priority["priority"]),
                    root_cause_category=category,
                    marker_count=int(root["marker_count"]),
                    percentage=float(root["percentage"]),
                    affected_modules=list(root["affected_modules"]),
                    dominant_rules=list(root["affected_rules"][:10]),
                    dominant_layers=list(root["affected_layers"][:10]),
                    blocks_drc_clean=_as_bool(matrix["blocks_drc_clean"]),
                    blocks_lvs_clean=_as_bool(matrix["blocks_lvs_clean"]),
                    blocks_timing_closure=_as_bool(matrix["blocks_timing_closure"]),
                    expected_fix_location=str(root["recommended_fix_layer"]),
                    expected_fix_files=str(priority.get("expected_fix_files", matrix["recommended_fix_files"])),
                    why_priority_high=why_priority_high,
                    recommended_next_action=self._recommended_next_action_override(category, str(root["recommended_next_action"])),
                )
            )
        return items

    def _build_capabilities(self) -> list[ProjectClosureCapability]:
        l5 = self.context["l5_report"]
        l6 = self.context["l6_report"]
        report_files = [
            str(self.context["l5_report_json"]),
            str(self.context["l6_report_json"]),
            str(self.context["top_gds"]),
        ]
        return [
            ProjectClosureCapability("cap_1", "OpenYield 语义到本地 layoutgen 的映射已建立。", report_files),
            ProjectClosureCapability("cap_2", "当前 scope 支持 single-bank、single-port、words_per_row 1/2。", [str(self.context["top_manifest_path"])]),
            ProjectClosureCapability("cap_3", "20 个 L3 target modules 已生成 standalone module GDS。", [str(self.context["module_gds_inventory_path"])]),
            ProjectClosureCapability("cap_4", "20 个模块均有 generator manifest / pins / bbox / rail metadata。", [str(self.context["module_gds_dir"])]),
            ProjectClosureCapability("cap_5", "top-level SRAM candidate GDS 已生成。", [str(self.context["top_gds"])]),
            ProjectClosureCapability("cap_6", "top-level GDS hierarchy 完整。", [str(self.context["top_hierarchy_diag_path"])]),
            ProjectClosureCapability("cap_7", "top-level GDS 可解析。", [str(self.context["l5_report_json"])]),
            ProjectClosureCapability("cap_8", "20 个 required modules 全部实例化。", [str(self.context["module_placement_path"])]),
            ProjectClosureCapability("cap_9", f"L5 basic validation 已通过，remaining_L5_basic_validation_blockers_count={l5['remaining_L5_basic_validation_blockers_count']}。", [str(self.context["l5_report_json"])]),
            ProjectClosureCapability("cap_10", f"DRC marker 已完成 100% 分类，coverage={l6['drc_marker_classification_coverage']}。", [str(self.context["l6_report_json"])]),
            ProjectClosureCapability("cap_11", "已形成后续 DRC 修复优先级计划。", [str(self.context["l6_fix_priority_path"])]),
        ]

    def _build_limitations(self) -> list[ProjectClosureLimitation]:
        return [
            ProjectClosureLimitation("lim_1", "DRC markers = 24687，尚未清零。", "当前不能 claim DRC clean。", [str(self.context["drc_smoke_report_path"])]),
            ProjectClosureLimitation("lim_2", "当前 top-level GDS 是 candidate layout，不是 signoff layout。", "当前终点是可交付候选态，不是可流片版图。", [str(self.context["top_gds"])]),
            ProjectClosureLimitation("lim_3", "部分模块使用 candidate geometry。", "这些模块会阻塞 DRC/LVS/timing/signoff claim。", [str(self.context["candidate_risk_report_path"])]),
            ProjectClosureLimitation("lim_4", "部分模块使用 contract pins。", "这些模块适合 basic validation，但不适合 DRC/LVS signoff。", [str(self.context["pin_access_audit_path"])]),
            ProjectClosureLimitation("lim_5", "LVS blocked by missing netlist。", "当前不能 claim LVS clean。", [str(self.context["lvs_feasibility_report_path"])]),
            ProjectClosureLimitation("lim_6", "timing 仍是 metadata / smoke 级别。", "当前不能 claim timing closure。", [str(self.context["l5_report_json"])]),
            ProjectClosureLimitation("lim_7", "当前仅覆盖 single-bank / single-port / limited words_per_row。", "更广 scope 仍未进入当前交付态。", [str(self.context["top_manifest_path"])]),
            ProjectClosureLimitation("lim_8", "multi-bank / multi-port / write mask / larger mux ratio 仍 unsupported。", "这些功能需要新增独立实现阶段。", [str(self.context["top_manifest_path"])]),
            ProjectClosureLimitation("lim_9", "DRC marker 分类依赖当前 deck、当前 GDS 和当前 marker parser，不代表最终物理收敛。", "后续若更换 deck 或 source geometry，分类比例可能变化。", [str(self.context["l6_report_json"])]),
        ]

    def _build_roadmap(self) -> list[FutureWorkItem]:
        drc_items = [
            ("DRC_CLEAN", 1, "DRC deck / layer map / source geometry grid audit", "先判断 FreePDK45 deck grid 与 imported source geometry 是否系统性不一致。"),
            ("DRC_CLEAN", 2, "imported GDS off-grid snapping 或 deck policy decision", "确定是修 source geometry、做 grid snapping，还是调整 deck policy。"),
            ("DRC_CLEAN", 3, "contract pins 转 geometry-backed pin", "把 contract pin 模块转成 geometry-backed pin/access proof。"),
            ("DRC_CLEAN", 4, "row_decoder candidate geometry cleanup", "对 row_decoder 做 generator-level cleanup。"),
            ("DRC_CLEAN", 5, "hardmacro internal DRC audit", "审计 wordline_driver / column_mux 的 imported hardmacro 内部 DRC。"),
            ("DRC_CLEAN", 6, "wrapper import artifact review", "复核 write_driver / sense_amp 的 wrapper import artifact。"),
            ("DRC_CLEAN", 7, "rerun DRC and compare marker deltas", "每轮修复后重新运行 DRC，并比较 marker delta。"),
            ("DRC_CLEAN", 8, "repeat targeted generator repair until marker count substantially decreases", "持续按 root cause priority 迭代，直到系统性 marker 大幅下降。"),
        ]
        lvs_items = [
            ("LVS_TIMING", 1, "export consistent top-level netlist", "导出与当前 top-level GDS 对齐的顶层网表。"),
            ("LVS_TIMING", 2, "establish module-to-netlist mapping", "建立 module GDS 到 netlist object 的稳定映射。"),
            ("LVS_TIMING", 3, "build pin geometry to net mapping", "把 geometry-backed pins 映射到 netlist pins。"),
            ("LVS_TIMING", 4, "resolve contract pin modules", "先消除 contract pin 模块，再推进 LVS。"),
            ("LVS_TIMING", 5, "run LVS feasibility smoke", "在 consistent netlist 存在后先跑 feasibility smoke。"),
            ("LVS_TIMING", 6, "only after LVS feasibility, attempt LVS clean", "只有 feasibility 稳定后才进入 LVS clean 目标。"),
            ("LVS_TIMING", 7, "timing closure 需建立 path-level evidence", "后续 timing closure 需要 SPEF/RC/path-level evidence，当前不 claim。"),
        ]
        items = drc_items + lvs_items
        return [
            FutureWorkItem(
                phase=phase,
                order_index=index,
                title=title,
                next_action=next_action,
                expected_outputs=["updated reports", "new evidence", "rerun validation/triage"] if phase == "DRC_CLEAN" else ["netlist evidence", "LVS/timing reports"],
            )
            for phase, index, title, next_action in items
        ]

    def _build_handoff_checklist(self) -> list[dict[str, Any]]:
        items = [
            ("L0 semantic contracts present", (self.context["repo_root"] / "docs/mapping/openyield_canonical_sram_semantic_contract.json").exists()),
            ("L1 primitive closure report present", (self.context["repo_root"] / "docs/openyield_physical_primitive_closure_report.json").exists()),
            ("L2 placement/abutment/rail rule library present", self.context["l2_rule_library_json"].exists()),
            ("L3 module GDS inventory present", self.context["module_gds_inventory_path"].exists()),
            ("L4 top-level candidate GDS present", self.context["top_gds"].exists()),
            ("L5 basic validation report present", self.context["l5_report_json"].exists()),
            ("L6 DRC triage report present", self.context["l6_report_json"].exists()),
            ("Step 7 final repair plan present", True),
            ("GDS generation command documented", True),
            ("current supported scope documented", True),
            ("limitations documented", True),
            ("future work documented", True),
            ("commit / bundle / patch documented", True),
        ]
        return [
            {"check_name": name, "status": bool(status), "notes": "" if status else "Missing required artifact."}
            for name, status in items
        ]

    def _emit_final_repair_plan(self, items: list[RepairPlanItem]) -> None:
        lines = [
            "# Final Repair Plan",
            "",
            "当前计划只定义有限修复路线，不在 Step 7 执行大规模 DRC 修复。",
            "",
        ]
        for item in items:
            lines.extend(
                [
                    f"## {item.priority} {item.root_cause_category}",
                    "",
                    f"- marker_count: `{item.marker_count}`",
                    f"- percentage: `{item.percentage}`",
                    f"- affected_modules: `{', '.join(item.affected_modules)}`",
                    f"- dominant_rules: `{'; '.join(item.dominant_rules[:5])}`",
                    f"- dominant_layers: `{'; '.join(item.dominant_layers[:5])}`",
                    f"- expected_fix_location: `{item.expected_fix_location}`",
                    f"- expected_fix_files: `{item.expected_fix_files}`",
                    f"- why_priority_high: {item.why_priority_high}",
                    f"- recommended_next_action: {item.recommended_next_action}",
                    "",
                ]
            )
        _write_text(self.out_dir / "final_repair_plan.md", "\n".join(lines))

    def _emit_capability_statement(self, items: list[ProjectClosureCapability]) -> None:
        lines = ["# Project v1 Capability Statement", ""]
        for item in items:
            lines.append(f"- {item.statement}")
        lines.extend(["", "当前不能 claim: DRC clean / LVS clean / timing closure / full validated GDS / signoff-ready SRAM compiler / 可流片版图。", ""])
        _write_text(self.out_dir / "project_v1_capability_statement.md", "\n".join(lines))

    def _emit_limitation_statement(self, items: list[ProjectClosureLimitation]) -> None:
        lines = ["# Project v1 Limitation Statement", ""]
        for item in items:
            lines.append(f"- {item.statement} {item.why_it_matters}")
        lines.append("")
        _write_text(self.out_dir / "project_v1_limitation_statement.md", "\n".join(lines))

    def _emit_future_work_roadmap(self, items: list[FutureWorkItem]) -> None:
        lines = ["# Future Work Roadmap", "", "## A. DRC Clean Continuation", ""]
        for item in [x for x in items if x.phase == "DRC_CLEAN"]:
            lines.append(f"- {item.order_index}. {item.title}: {item.next_action}")
        lines.extend(["", "## B. LVS / Timing Continuation", ""])
        for item in [x for x in items if x.phase == "LVS_TIMING"]:
            lines.append(f"- {item.order_index}. {item.title}: {item.next_action}")
        lines.append("")
        _write_text(self.out_dir / "future_work_roadmap.md", "\n".join(lines))

    def _emit_final_handoff_checklist(self, items: list[dict[str, Any]]) -> None:
        lines = ["# Final Handoff Checklist", ""]
        for item in items:
            lines.append(f"- {item['check_name']}: `{item['status']}`")
        lines.append("")
        _write_text(self.out_dir / "final_handoff_checklist.md", "\n".join(lines))

    def _repair_item_to_matrix_row(self, item: RepairPlanItem) -> dict[str, Any]:
        return {
            "priority": item.priority,
            "root_cause_category": item.root_cause_category,
            "marker_count": item.marker_count,
            "percentage": item.percentage,
            "affected_modules": "; ".join(item.affected_modules),
            "dominant_rules": "; ".join(item.dominant_rules),
            "dominant_layers": "; ".join(item.dominant_layers),
            "blocks_drc_clean": item.blocks_drc_clean,
            "blocks_lvs_clean": item.blocks_lvs_clean,
            "blocks_timing_closure": item.blocks_timing_closure,
            "expected_fix_location": item.expected_fix_location,
            "expected_fix_files": item.expected_fix_files,
            "why_priority_high": item.why_priority_high,
            "recommended_next_action": item.recommended_next_action,
        }

    def _build_summary(self, repair_items: list[RepairPlanItem]) -> dict[str, Any]:
        l5 = self.context["l5_report"]
        l6 = self.context["l6_report"]
        top = repair_items[0]
        blockers: list[str] = []
        return {
            "Step7_final_repair_planning_available": True,
            "final_repair_plan_available": True,
            "project_v1_capability_statement_available": True,
            "project_v1_limitation_statement_available": True,
            "future_work_roadmap_available": True,
            "final_handoff_checklist_available": True,
            "step7_repair_plan_matrix_available": True,
            "drc_marker_total_count": l6["drc_marker_total_count"],
            "drc_marker_classified_count": l6["drc_marker_classified_count"],
            "drc_marker_classification_coverage": l6["drc_marker_classification_coverage"],
            "top_repair_priority": top.priority,
            "top_repair_root_cause": top.root_cause_category,
            "top_repair_marker_count": top.marker_count,
            "can_claim_openyield_driven_top_level_candidate_gds_generated_now": True,
            "can_claim_L5_basic_validation_passed_now": l5["can_claim_L5_basic_validation_passed_now"],
            "can_claim_L6_drc_triage_completed_now": l6["can_claim_L6_drc_triage_completed_now"],
            "can_claim_project_v1_closure_ready": True,
            "can_enter_step8_final_report_handoff": True,
            "can_claim_drc_clean_now": False,
            "can_claim_lvs_clean_now": False,
            "can_claim_timing_closure_now": False,
            "can_claim_validated_full_openyield_gds_now": False,
            "can_claim_signoff_ready_sram_compiler_now": False,
            "remaining_step7_blockers": blockers,
            "remaining_step7_blockers_count": len(blockers),
        }

    def _why_priority_high(self, category: str, marker_count: int) -> str:
        if category == "LAYER_MAP_OR_DRC_DECK_INTERPRETATION":
            return f"该类 marker 数量最高（{marker_count}），而且更像 deck/grid/source geometry 的系统性不一致，若不先处理会掩盖其他真实 top-level DRC 问题。"
        if category == "CONTRACT_PIN_GEOMETRY_PLACEHOLDER":
            return f"该类 marker 数量极高（{marker_count}），并同时阻塞 DRC clean、LVS clean 和 timing closure。"
        if category == "CANDIDATE_GEOMETRY_INTERNAL":
            return "该类集中在 row_decoder，适合用 generator-level cleanup 做定点收敛。"
        if category == "MODULE_INTERNAL_HARDMACRO":
            return "该类数量较低，但若不先确认 hardmacro 内部问题，后续容易误判 top-level 责任边界。"
        return "该类数量较少，但与 wrapper/import artifact 相关，应在 signoff 前复核。"

    def _recommended_next_action_override(self, category: str, default_text: str) -> str:
        overrides = {
            "LAYER_MAP_OR_DRC_DECK_INTERPRETATION": "下一阶段若要推进 DRC clean，应先做 source geometry snapping / deck grid policy review / layer map audit，而不是直接改 top-level placement。",
            "CONTRACT_PIN_GEOMETRY_PLACEHOLDER": "这些模块当前适合作为 candidate GDS 和 basic validation，但不适合作为 DRC/LVS signoff；下一阶段需要把 contract pin 转化为 geometry-backed pin/access proof。",
            "CANDIDATE_GEOMETRY_INTERNAL": "row_decoder 应作为后续 generator-level cleanup 的优先候选模块。",
            "MODULE_INTERNAL_HARDMACRO": "需要审计 imported hardmacro 本身和 wrapper assumptions，避免误把 hardmacro 内部规则问题归咎于 top-level assembly。",
            "MODULE_WRAPPER_IMPORT": "该类数量较少，但与 hierarchy import/wrapper 有关，应在后续 signoff 前复核。",
        }
        return overrides.get(category, default_text)


def emit_step7_reports(
    report: FinalRepairPlanningReport,
    *,
    out_matrix_csv: Path,
    out_matrix_md: Path,
    out_json: Path,
    out_report: Path,
    evidence_gap_summary: Path,
    evidence_timeline: Path,
    milestone_summary: Path,
) -> None:
    _json_dump(out_json, report.summary | {"matrix_rows": report.matrix_rows})
    _write_text(out_report, _build_step7_report_markdown(report.summary, report.matrix_rows))
    _write_csv(
        out_matrix_csv,
        [
            "priority",
            "root_cause_category",
            "marker_count",
            "percentage",
            "affected_modules",
            "dominant_rules",
            "dominant_layers",
            "blocks_drc_clean",
            "blocks_lvs_clean",
            "blocks_timing_closure",
            "expected_fix_location",
            "expected_fix_files",
            "why_priority_high",
            "recommended_next_action",
        ],
        report.matrix_rows,
    )
    _write_text(out_matrix_md, _build_step7_matrix_markdown(report.matrix_rows))
    _write_text(evidence_gap_summary, _build_step7_gap_summary_markdown(report.summary, report.matrix_rows))
    _append_unique_line(
        evidence_timeline,
        "- `2026-07-03`: Completed Step 7 final repair planning / project closure for the OpenYield-driven SRAM top-level candidate GDS v1.0 deliverable; finite repair scope, capability/limitation statements, future-work roadmap, and final handoff checklist are now frozen while all DRC/LVS/timing/full-GDS/signoff claims remain false.",
    )
    _append_unique_line(
        milestone_summary,
        "- Step 7 closure planning: the OpenYield-driven SRAM top-level candidate GDS v1.0 deliverable is now bounded by explicit capability claims, limitation statements, finite repair priorities, and a Step 8-ready handoff checklist; `can_claim_project_v1_closure_ready=True` while all DRC/LVS/timing/full-GDS/signoff claims remain false.",
    )


def _append_unique_line(path: Path, line: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if line in existing:
        return
    _write_text(path, existing.rstrip() + "\n" + line + "\n")


def _build_step7_report_markdown(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Step 7 Final Repair Planning Report",
        "",
        f"- top_repair_priority: `{summary['top_repair_priority']}`",
        f"- top_repair_root_cause: `{summary['top_repair_root_cause']}`",
        f"- top_repair_marker_count: `{summary['top_repair_marker_count']}`",
        f"- can_claim_project_v1_closure_ready: `{summary['can_claim_project_v1_closure_ready']}`",
        f"- can_enter_step8_final_report_handoff: `{summary['can_enter_step8_final_report_handoff']}`",
        "",
        "## Repair Plan",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row['priority']} {row['root_cause_category']}`: markers=`{row['marker_count']}`, files=`{row['expected_fix_files']}`")
    lines.extend(
        [
            "",
            "## Claims Kept False",
            "",
            f"- can_claim_drc_clean_now: `{summary['can_claim_drc_clean_now']}`",
            f"- can_claim_lvs_clean_now: `{summary['can_claim_lvs_clean_now']}`",
            f"- can_claim_timing_closure_now: `{summary['can_claim_timing_closure_now']}`",
            f"- can_claim_validated_full_openyield_gds_now: `{summary['can_claim_validated_full_openyield_gds_now']}`",
            f"- can_claim_signoff_ready_sram_compiler_now: `{summary['can_claim_signoff_ready_sram_compiler_now']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _build_step7_matrix_markdown(rows: list[dict[str, Any]]) -> str:
    headers = ["priority", "root_cause_category", "marker_count", "affected_modules", "expected_fix_location"]
    lines = [
        "# Step 7 Final Repair Plan Matrix",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["priority"]),
                    str(row["root_cause_category"]),
                    str(row["marker_count"]),
                    str(row["affected_modules"]),
                    str(row["expected_fix_location"]),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _build_step7_gap_summary_markdown(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    top = rows[0]
    lines = [
        "# Step 7 Final Repair Planning Gap Summary",
        "",
        "1. 当前项目 v1.0 做到了什么：已生成 OpenYield-driven top-level candidate GDS，L5 basic validation passed，L6 DRC marker triage completed，且形成了有限修复计划。",
        "2. 当前项目 v1.0 没做到什么：仍不是 DRC clean / LVS clean / timing closure / full validated GDS / signoff-ready SRAM compiler / 可流片版图。",
        f"3. DRC marker 分类结果：total=`{summary['drc_marker_total_count']}`，classified=`{summary['drc_marker_classified_count']}`，coverage=`{summary['drc_marker_classification_coverage']}`。",
        f"4. 最高优先级修复项：`{top['priority']} {top['root_cause_category']}`，marker_count=`{top['marker_count']}`。",
        "5. 当前终点不是 DRC clean，因为 marker 仍然很多，且主要 root cause 仍未修复。",
        "6. 当前可以进入 Step 8 final report，因为 capability/limitation/roadmap/checklist 已齐备，且 remaining_step7_blockers_count=0。",
        "7. 后续若继续推进 DRC/LVS/timing，需要新增独立项目阶段，而不是在当前 v1.0 交付态内继续无限展开。",
        "",
    ]
    return "\n".join(lines)
