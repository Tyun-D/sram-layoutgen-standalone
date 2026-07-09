from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def _manifest(repo_root: Path, paths: list[Path]) -> list[dict[str, Any]]:
    items = []
    for path in paths:
        items.append(
            {
                "path": str(path.relative_to(repo_root)),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return items


def _update_progress(progress_text: str) -> str:
    replacements = {
        "M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION after M11A qualification; first guarded candidates are sense_amp, write_driver.":
        "M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION_FOR_SENSE_AMP_AND_WORDLINE_DRIVER after M11AR correction; only sense_amp and wordline_driver remain guarded substitution candidates.",
        "- next_action: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION`":
        "- next_action: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION_FOR_SENSE_AMP_AND_WORDLINE_DRIVER`",
        "- next_assets_to_fill_in_order: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION, M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE, M12A_VARIATION_GDS_GENERATION, M12B_ROUTING_POWER_ADAPTATION, M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE`":
        "- next_assets_to_fill_in_order: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION_FOR_SENSE_AMP_AND_WORDLINE_DRIVER, M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE, M12A_VARIATION_GDS_GENERATION, M12B_ROUTING_POWER_ADAPTATION, M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE`",
        "- first_substitution_candidates: `sense_amp, write_driver`":
        "- first_substitution_candidates: `sense_amp, wordline_driver`",
    }
    updated = progress_text
    for old, new in replacements.items():
        updated = updated.replace(old, new)

    marker = "## M11A Qualification"
    if marker in updated and "## M11AR Human Review Correction" not in updated:
        updated = (
            updated.rstrip()
            + "\n\n## M11AR Human Review Correction\n\n"
            + "- human_review_applied: `True`\n"
            + "- unknown_golden_region_markers_are_real_modules: `False`\n"
            + "- direct_hardmacro_replace_count_after: `2`\n"
            + "- first_substitution_candidates_after: `sense_amp, wordline_driver`\n"
            + "- downgraded_modules: `column_mux, write_driver`\n"
            + "- note: `M11B is limited to deep pin/bbox/rail validation for sense_amp and wordline_driver only.`\n"
        )
    return updated if updated.endswith("\n") else updated + "\n"


def _status_md_text() -> str:
    return _render_md(
        "OpenYield SRAM LayoutGen Project Status",
        [
            "## 1. Current Correct Goal",
            "",
            "M11AR 已把 M11A 的人工 review 修正收敛进 hardmacro 资格结果。当前只保留 `sense_amp` 与 `wordline_driver` 作为进入 M11B 的优先候选，`column_mux` 与 `write_driver` 已降级，不能直接进行模块替换。",
            "",
            "## 2. Current Stage",
            "",
            "- current_stage: `M11AR`",
            "- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`",
            "- human_klayout_review_required_every_stage: `True`",
            "- can_enter_next_stage_without_human_review: `False`",
            "- next_stage_allowed: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION_FOR_SENSE_AMP_AND_WORDLINE_DRIVER`",
            "",
            "## 3. Latest M11AR Result",
            "",
            "- human_review_applied: `True`",
            "- unknown_golden_region_markers_are_real_modules: `False`",
            "- direct_hardmacro_replace_count_before: `4`",
            "- direct_hardmacro_replace_count_after: `2`",
            "- first_substitution_candidates_after: `sense_amp, wordline_driver`",
            "- downgraded_modules: `column_mux, write_driver`",
            "- can_claim_openyield_module_gds_hardmacro_substitution: `False`",
            "- next_stage_allowed: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION_FOR_SENSE_AMP_AND_WORDLINE_DRIVER`",
        ],
    )


def run_m11ar_human_review_correction(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    progress_md: Path,
    m11a_report: Path,
    m11a_decision: Path,
    m11a_pin_metadata: Path,
    m11a_comparison: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    status = _read_json(status_json)
    m11a = _read_json(m11a_report)
    decision_rows = _read_csv(m11a_decision)
    pin_rows = _read_csv(m11a_pin_metadata)
    comparison_rows = _read_csv(m11a_comparison)
    progress_text = progress_md.read_text(encoding="utf-8")

    pin_counts: dict[str, int] = {}
    for row in pin_rows:
        pin_counts[row["openyield_module"]] = pin_counts.get(row["openyield_module"], 0) + 1
    comparison_map = {row["openyield_module"]: row for row in comparison_rows}
    decision_map = {row["openyield_module"]: dict(row) for row in decision_rows}

    before_count = int(m11a["direct_hardmacro_replace_count"])
    before_candidates = list(m11a["first_substitution_candidates"])

    if "human_review_passed" not in decision_rows[0]:
        fieldnames = list(decision_rows[0].keys()) + ["human_review_passed", "human_review_notes"]
    else:
        fieldnames = list(decision_rows[0].keys())
    if "human_review_notes" not in fieldnames:
        fieldnames.append("human_review_notes")

    downgraded_modules = ["column_mux", "write_driver"]

    for module, row in decision_map.items():
        row["human_review_passed"] = "False"
        row["human_review_notes"] = ""
        if module == "sense_amp":
            row["decision"] = "DIRECT_HARDMACRO_REPLACE"
            row["decision_reason"] = (
                "Wrapper macro has a real golden leaf counterpart, non-contract pin geometry, and compatible rails/bbox for a guarded selective substitution trial. "
                "human_review_confirmed: visible geometry appears complete and close to the golden comparison target."
            )
            row["first_substitution_priority"] = "P0"
            row["human_review_passed"] = "True"
            row["human_review_notes"] = "Retained as a priority M11B candidate after human KLayout review."
        elif module == "wordline_driver":
            row["decision"] = "DIRECT_HARDMACRO_REPLACE"
            row["decision_reason"] = (
                "Wrapper macro has a real golden leaf counterpart, non-contract pin geometry, and compatible rails/bbox for a guarded selective substitution trial. "
                "human_review_confirmed: visible geometry appears complete and close to the golden comparison target."
            )
            row["first_substitution_priority"] = "P0"
            row["human_review_passed"] = "True"
            row["human_review_notes"] = "Retained as a priority M11B candidate after human KLayout review."
        elif module in {"column_mux", "write_driver"}:
            row["decision"] = "CONSTRAINT_EXTRACTION_ONLY" if pin_counts.get(module, 0) > 0 else "SEMANTIC_REFERENCE_ONLY"
            row["decision_reason"] = "downgraded_by_human_review: visible geometry appears incomplete."
            row["first_substitution_priority"] = "P1" if row["decision"] == "CONSTRAINT_EXTRACTION_ONLY" else "P2"
            row["human_review_notes"] = "Removed from direct replacement candidates; metadata may still be reused."
        elif module == "CONTROL_LOGIC":
            row["decision"] = "SEMANTIC_REFERENCE_ONLY"
            row["decision_reason"] = (
                "Current flow still relies on layoutgen fallback or regenerated layoutgen composites for this role; module GDS remains semantic/reference evidence only. "
                "human_review: gate-like candidate geometry exists but no complete verified connection; not suitable for hardmacro replacement."
            )
            row["first_substitution_priority"] = "P2"
            row["human_review_notes"] = "Human review confirmed semantic-only status."

    ordered_modules = [row["openyield_module"] for row in decision_rows]
    corrected_rows = [decision_map[module] for module in ordered_modules]
    after_count = sum(1 for row in corrected_rows if row["decision"] == "DIRECT_HARDMACRO_REPLACE")
    after_candidates = ["sense_amp", "wordline_driver"]
    safe_scope = ["sense_amp", "wordline_driver"]

    corrected_plan_rows = []
    for index, module in enumerate(after_candidates, start=1):
        row = decision_map[module]
        corrected_plan_rows.append(
            {
                "sequence": index,
                "module": module,
                "decision": row["decision"],
                "priority": row["first_substitution_priority"],
                "human_review_passed": row["human_review_passed"],
                "next_action": "M11B deep pin/bbox/rail metadata verification",
            }
        )

    corrected_md_lines = [
        f"- `{row['openyield_module']}` => `{row['decision']}` human_review_passed=`{row['human_review_passed']}` reason=`{row['decision_reason']}`"
        for row in corrected_rows
    ]
    plan_md_lines = [
        f"- `{row['module']}` priority=`{row['priority']}` human_review_passed=`{row['human_review_passed']}` next_action=`{row['next_action']}`"
        for row in corrected_plan_rows
    ]

    output_decision_csv = out_dir / "M11AR_corrected_hardmacro_substitution_decision.csv"
    output_decision_md = out_dir / "M11AR_corrected_hardmacro_substitution_decision.md"
    output_plan_csv = out_dir / "M11AR_corrected_first_substitution_plan.csv"
    output_plan_md = out_dir / "M11AR_corrected_first_substitution_plan.md"

    _write_csv(output_decision_csv, fieldnames, corrected_rows)
    _write_text(output_decision_md, _render_md("M11AR Corrected Hardmacro Substitution Decision", corrected_md_lines))
    _write_csv(
        output_plan_csv,
        ["sequence", "module", "decision", "priority", "human_review_passed", "next_action"],
        corrected_plan_rows,
    )
    _write_text(output_plan_md, _render_md("M11AR Corrected First Substitution Plan", plan_md_lines))

    # Overwrite M11A decision views with corrected human-reviewed content.
    m11a_output_dir = repo_root / "outputs/M11A_module_gds_qualification/current_supported_config"
    _write_csv(repo_root / "docs/mapping/M11A_hardmacro_substitution_decision.csv", fieldnames, corrected_rows)
    _write_text(
        repo_root / "docs/mapping/M11A_hardmacro_substitution_decision.md",
        _render_md("M11A Hardmacro Substitution Decision", corrected_md_lines),
    )
    _write_csv(m11a_output_dir / "M11A_hardmacro_substitution_decision.csv", fieldnames, corrected_rows)
    _write_text(
        m11a_output_dir / "M11A_hardmacro_substitution_decision.md",
        _render_md("M11A Hardmacro Substitution Decision", corrected_md_lines),
    )

    _write_csv(repo_root / "docs/mapping/M11AR_corrected_hardmacro_substitution_decision.csv", fieldnames, corrected_rows)
    _write_csv(
        repo_root / "docs/mapping/M11AR_corrected_first_substitution_plan.csv",
        ["sequence", "module", "decision", "priority", "human_review_passed", "next_action"],
        corrected_plan_rows,
    )

    annotated_debug_gds = repo_root / "outputs/M11A_module_gds_qualification/current_supported_config/module_gds_qualification_annotated_debug.gds"
    clean_review_gds = repo_root / "outputs/M11A_module_gds_qualification/current_supported_config/module_gds_qualification_clean_review.gds"
    manifest = _manifest(repo_root, [annotated_debug_gds, clean_review_gds])
    _write_json(out_dir / "review_gds_manifest.json", manifest)
    _write_text(
        out_dir / "review_gds_manifest.md",
        _render_md("M11AR Review GDS Manifest", [f"- `{item['path']}` size={item['size_bytes']} sha256=`{item['sha256']}`" for item in manifest]),
    )

    updated_progress = _update_progress(progress_text)
    _write_text(progress_md, updated_progress)

    next_stage_allowed = "M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION_FOR_SENSE_AMP_AND_WORDLINE_DRIVER"
    status["current_stage"] = "M11AR"
    status["next_stage"] = "WAIT_HUMAN_KLAYOUT_REVIEW"
    status["next_stage_allowed"] = next_stage_allowed
    status["can_enter_next_stage_without_human_review"] = False
    status["current_goal"] = (
        "M11AR applied the human review correction to M11A and narrowed the only allowed M11B deep metadata verification scope to sense_amp and wordline_driver."
    )
    status["can_claim_openyield_module_gds_hardmacro_substitution"] = False
    status["last_M11AR_report"] = {
        "status_file_read": True,
        "status_file_updated": True,
        "progress_file_updated": True,
        "m11a_report_loaded": True,
        "m11a_decision_matrix_loaded": True,
        "human_review_applied": True,
        "debug_marker_layer": "295/0",
        "debug_marker_cell": "module_gds_qualification_debug",
        "unknown_golden_region_markers_are_real_modules": False,
        "control_logic_human_review_result": "SEMANTIC_REFERENCE_ONLY",
        "sense_amp_human_review_result": "DIRECT_HARDMACRO_REPLACE",
        "wordline_driver_human_review_result": "DIRECT_HARDMACRO_REPLACE",
        "column_mux_human_review_result": decision_map["column_mux"]["decision"],
        "write_driver_human_review_result": decision_map["write_driver"]["decision"],
        "direct_hardmacro_replace_count_before": before_count,
        "direct_hardmacro_replace_count_after": after_count,
        "first_substitution_candidates_before": before_candidates,
        "first_substitution_candidates_after": after_candidates,
        "downgraded_modules": downgraded_modules,
        "downgrade_reason": "downgraded_by_human_review: visible geometry appears incomplete.",
        "safe_to_attempt_selective_substitution": True,
        "safe_to_attempt_selective_substitution_scope": safe_scope,
        "must_run_M11B_before_substitution": True,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
        "next_stage_allowed": next_stage_allowed,
        "can_enter_M11B_after_this_gate": True,
        "human_klayout_review_required_for_M11B_output": True,
        "can_enter_next_stage_without_human_review": False,
        "remaining_M11AR_blockers": [
            "M11B deep pin/bbox/rail metadata verification is limited to sense_amp and wordline_driver.",
            "Human KLayout review is still required for any M11B output before continuing.",
            "OpenYield module GDS hardmacro substitution still cannot be claimed complete.",
        ],
        "remaining_M11AR_blockers_count": 3,
    }
    for asset in status.get("ten_required_assets_for_netlist_to_layout", []):
        if asset["asset_id"] == "PHYSICAL_IMPLEMENTATION_LIBRARY":
            asset["evidence_paths"] = [
                "docs/mapping/M11AR_corrected_hardmacro_substitution_decision.csv",
                "docs/mapping/M11A_hardmacro_substitution_decision.csv",
                "outputs/M11AR_human_review_correction/current_supported_config/M11AR_corrected_first_substitution_plan.csv",
            ]
            asset["next_action"] = next_stage_allowed
            asset["blocking_for_next_stage"] = True
        elif asset["asset_id"] == "PIN_BBOX_RAIL_METADATA":
            asset["evidence_paths"] = [
                "docs/mapping/M11A_pin_bbox_rail_metadata.csv",
                "docs/mapping/M11AR_corrected_first_substitution_plan.csv",
                "outputs/M11AR_human_review_correction/current_supported_config/M11AR_corrected_hardmacro_substitution_decision.csv",
            ]
            asset["next_action"] = next_stage_allowed
            asset["blocking_for_next_stage"] = True
    status["next_assets_to_fill_in_order"] = [
        next_stage_allowed,
        "M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE",
        "M12A_VARIATION_GDS_GENERATION",
        "M12B_ROUTING_POWER_ADAPTATION",
        "M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE",
    ]
    _write_json(status_json, status)
    _write_text(status_md, _status_md_text())

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "progress_file_updated": True,
        "m11a_report_loaded": True,
        "m11a_decision_matrix_loaded": True,
        "human_review_applied": True,
        "debug_marker_layer": "295/0",
        "debug_marker_cell": "module_gds_qualification_debug",
        "unknown_golden_region_markers_are_real_modules": False,
        "control_logic_human_review_result": "SEMANTIC_REFERENCE_ONLY",
        "sense_amp_human_review_result": "DIRECT_HARDMACRO_REPLACE",
        "wordline_driver_human_review_result": "DIRECT_HARDMACRO_REPLACE",
        "column_mux_human_review_result": decision_map["column_mux"]["decision"],
        "write_driver_human_review_result": decision_map["write_driver"]["decision"],
        "direct_hardmacro_replace_count_before": before_count,
        "direct_hardmacro_replace_count_after": after_count,
        "first_substitution_candidates_before": before_candidates,
        "first_substitution_candidates_after": after_candidates,
        "downgraded_modules": downgraded_modules,
        "downgrade_reason": "downgraded_by_human_review: visible geometry appears incomplete.",
        "safe_to_attempt_selective_substitution": True,
        "safe_to_attempt_selective_substitution_scope": safe_scope,
        "must_run_M11B_before_substitution": True,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
        "next_stage_allowed": next_stage_allowed,
        "can_enter_M11B_after_this_gate": True,
        "human_klayout_review_required_for_M11B_output": True,
        "can_enter_next_stage_without_human_review": False,
        "remaining_M11AR_blockers": status["last_M11AR_report"]["remaining_M11AR_blockers"],
        "remaining_M11AR_blockers_count": 3,
    }
    _write_json(out_json, report)
    _write_text(
        out_report,
        _render_md(
            "M11AR Human Review Correction Report",
            [
                "- human_review_applied: `True`",
                "- unknown_golden_region_markers_are_real_modules: `False`",
                f"- direct_hardmacro_replace_count_before: `{before_count}`",
                f"- direct_hardmacro_replace_count_after: `{after_count}`",
                f"- first_substitution_candidates_before: `{', '.join(before_candidates)}`",
                f"- first_substitution_candidates_after: `{', '.join(after_candidates)}`",
                f"- downgraded_modules: `{', '.join(downgraded_modules)}`",
                f"- next_stage_allowed: `{next_stage_allowed}`",
            ],
        ),
    )
    _write_text(
        repo_root / "docs/evidence/M11AR_human_review_correction_summary.md",
        _render_md(
            "M11AR Human Review Correction Summary",
            [
                "- human_review_applied: `True`",
                "- unknown_golden_region_markers_are_real_modules: `False`",
                "- retained_direct_replace_candidates: `sense_amp, wordline_driver`",
                "- downgraded_modules: `column_mux, write_driver`",
                f"- next_stage_allowed: `{next_stage_allowed}`",
            ],
        ),
    )
    _write_json(out_dir / "M11AR_human_review_correction_report.json", report)
    _write_text(
        out_dir / "M11AR_human_review_correction_report.md",
        _render_md(
            "M11AR Human Review Correction Report",
            [
                "- human_review_applied: `True`",
                "- unknown_golden_region_markers_are_real_modules: `False`",
                "- retained_direct_replace_candidates: `sense_amp, wordline_driver`",
                "- downgraded_modules: `column_mux, write_driver`",
            ],
        ),
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply human review correction to M11A module GDS qualification.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--progress-md", required=True)
    parser.add_argument("--m11a-report", required=True)
    parser.add_argument("--m11a-decision", required=True)
    parser.add_argument("--m11a-pin-metadata", required=True)
    parser.add_argument("--m11a-comparison", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    report = run_m11ar_human_review_correction(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        progress_md=(repo_root / args.progress_md).resolve(),
        m11a_report=(repo_root / args.m11a_report).resolve(),
        m11a_decision=(repo_root / args.m11a_decision).resolve(),
        m11a_pin_metadata=(repo_root / args.m11a_pin_metadata).resolve(),
        m11a_comparison=(repo_root / args.m11a_comparison).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    for key in [
        "human_review_applied",
        "direct_hardmacro_replace_count_after",
        "first_substitution_candidates_after",
        "next_stage_allowed",
    ]:
        print(f"{key}={report[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
