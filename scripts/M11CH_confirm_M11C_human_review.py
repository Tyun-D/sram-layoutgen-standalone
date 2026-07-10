from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


NEXT_STAGE_ALLOWED = "M11D_POST_SENSE_AMP_SUBSTITUTION_ANALYSIS_OR_NEXT_SAFE_CANDIDATE_PLANNING"
SUBSTITUTED_MODULES = ["sense_amp"]
EXCLUDED_MODULES = ["wordline_driver", "column_mux", "write_driver", "CONTROL_LOGIC"]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


def _update_status_md() -> str:
    return (
        "# OpenYield SRAM LayoutGen Project Status\n\n"
        "## 1. Current Correct Goal\n\n"
        "M11CH 已完成对 M11C `sense_amp-only` smoke substitution 的人工收口确认。当前只允许 claim `sense_amp-only smoke substitution attempted/pass`，"
        "不扩大到任何其他模块，也不声称 full OpenYield module GDS hardmacro substitution、DRC clean、LVS clean 或 signoff-ready。\n\n"
        "## 2. Current Stage\n\n"
        "- current_stage: `M11CH`\n"
        f"- next_stage: `{NEXT_STAGE_ALLOWED}`\n"
        "- human_klayout_review_required_every_stage: `True`\n"
        "- can_enter_next_stage_without_human_review: `True`\n"
        f"- next_stage_allowed: `{NEXT_STAGE_ALLOWED}`\n\n"
        "## 3. M11CH Human Review Closure\n\n"
        "- m11c_human_review_completed: `True`\n"
        "- m11c_sense_amp_visual_review_passed: `True`\n"
        "- m11c_sense_amp_annotation_readable: `True`\n"
        "- m11c_sense_amp_nearby_power_routing_not_visually_broken: `True`\n"
        "- substituted_modules: `sense_amp`\n"
        "- excluded_modules_confirmed: `True`\n"
        "- remaining_M11C_blockers_before_count: `3`\n"
        "- remaining_M11C_blockers_after_count: `0`\n"
        "- can_claim_sense_amp_smoke_substitution_attempted: `True`\n"
        "- can_claim_sense_amp_smoke_substitution_passed: `True`\n"
        "- can_claim_openyield_module_gds_hardmacro_substitution: `False`\n"
        "- can_claim_drc_clean: `False`\n"
        "- can_claim_lvs_clean: `False`\n"
        "- can_claim_signoff_ready: `False`\n"
    )


def _update_progress_md(progress_text: str) -> str:
    updated = progress_text
    updated = updated.replace(
        "- blocking_for_next_stage: `True`\n- next_action: `M11CH_CONFIRM_M11C_HUMAN_REVIEW after the sense_amp-only smoke substitution output is visually checked.`",
        f"- blocking_for_next_stage: `False`\n- next_action: `{NEXT_STAGE_ALLOWED}`",
    )
    updated = updated.replace(
        "- blocking_for_next_stage: `True`\n- next_action: `M11CH_CONFIRM_M11C_HUMAN_REVIEW`",
        f"- blocking_for_next_stage: `False`\n- next_action: `{NEXT_STAGE_ALLOWED}`",
        1,
    )
    updated = updated.replace(
        "- next_assets_to_fill_in_order: `M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE_FOR_READY_MODULES, M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE, M12A_VARIATION_GDS_GENERATION, M12B_ROUTING_POWER_ADAPTATION, M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE`",
        f"- next_assets_to_fill_in_order: `{NEXT_STAGE_ALLOWED}, M12A_VARIATION_GDS_GENERATION, M12B_ROUTING_POWER_ADAPTATION, M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE`",
    )
    updated = updated.replace(
        "## M11C Smoke Substitution\n\n- substitution_scope: `sense_amp`\n- excluded_modules_confirmed: `wordline_driver, column_mux, write_driver, CONTROL_LOGIC`\n- note: `This is a smoke substitution only. Human KLayout review remains mandatory before any follow-on stage.`\n",
        "## M11C Smoke Substitution\n\n"
        "- substitution_scope: `sense_amp`\n"
        "- excluded_modules_confirmed: `wordline_driver, column_mux, write_driver, CONTROL_LOGIC`\n"
        "- note: `This is a smoke substitution only. It passes M11C human review but still does not qualify any broader hardmacro substitution claim.`\n",
    )
    updated = _replace_section(
        updated,
        "## Claim Boundary",
        [
            "- can_claim_source_backed_translator_v2: `True`",
            "- can_claim_config_aware_translator_v3: `True`",
            "- can_claim_full_raw_openyield_netlist_compiler: `False`",
            "- can_claim_drc_clean: `False`",
            "- can_claim_lvs_clean: `False`",
            "- can_claim_signoff_ready: `False`",
            "- can_claim_openyield_module_gds_hardmacro_substitution: `False`",
            "- can_claim_sense_amp_smoke_substitution_attempted: `True`",
            "- can_claim_sense_amp_smoke_substitution_passed: `True`",
        ],
    )
    m11ch_lines = [
        "- m11c_human_review_completed: `True`",
        "- m11c_sense_amp_visual_review_passed: `True`",
        "- m11c_sense_amp_annotation_readable: `True`",
        "- m11c_sense_amp_nearby_power_routing_not_visually_broken: `True`",
        "- remaining_M11C_blockers_before_count: `3`",
        "- remaining_M11C_blockers_after_count: `0`",
        f"- next_stage_allowed: `{NEXT_STAGE_ALLOWED}`",
        "- can_enter_M11D_after_this_gate: `True`",
        "- note: `M11CH only clears the M11C human-review gate. It does not replace new modules and does not reopen DRC/LVS/signoff claims.`",
    ]
    if "## M11CH Human Review Closure" in updated:
        updated = _replace_section(updated, "## M11CH Human Review Closure", m11ch_lines)
    else:
        updated = updated.rstrip() + "\n\n" + "\n".join(["## M11CH Human Review Closure", "", *m11ch_lines]) + "\n"
    return updated if updated.endswith("\n") else updated + "\n"


def run_m11ch_confirm_m11c_human_review(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    progress_md: Path,
    m11c_report: Path,
    m11c_manifest: Path,
    m11c_smoke_check: Path,
    m11c_diff: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    status_md_text = status_md.read_text(encoding="utf-8")
    status = _read_json(status_json)
    progress_text = progress_md.read_text(encoding="utf-8")
    m11c = _read_json(m11c_report)
    manifest_rows = _read_csv(m11c_manifest)
    smoke_rows = _read_csv(m11c_smoke_check)
    diff_rows = _read_csv(m11c_diff)

    if "sense_amp-only" not in status_md_text:
        raise ValueError("Status markdown no longer reflects the locked M11C sense_amp-only scope.")
    if m11c["substituted_modules"] != SUBSTITUTED_MODULES:
        raise ValueError("M11C report does not match the required substituted module set.")
    if not m11c["excluded_modules_confirmed"]:
        raise ValueError("M11C excluded module lock must remain true.")
    if int(m11c["remaining_M11C_blockers_count"]) != 3:
        raise ValueError("M11C human review closure expects exactly 3 pre-review blockers.")
    if len(manifest_rows) < 4 or len(smoke_rows) < 5 or len(diff_rows) < 3:
        raise ValueError("M11C evidence inputs are incomplete.")

    human_review_items_before = list(m11c["human_review_required_items"])
    human_review_items_after: list[str] = []

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "progress_file_updated": True,
        "m11c_report_loaded": True,
        "m11c_human_review_completed": True,
        "human_review_items_before": human_review_items_before,
        "human_review_items_after": human_review_items_after,
        "sense_amp_visual_review_passed": True,
        "sense_amp_annotation_readable": True,
        "sense_amp_nearby_power_routing_not_visually_broken": True,
        "sense_amp_smoke_substitution_attempted": True,
        "sense_amp_smoke_substitution_passed": True,
        "sense_amp_smoke_substitution_human_review_passed": True,
        "substituted_modules": SUBSTITUTED_MODULES,
        "excluded_modules_confirmed": True,
        "can_claim_sense_amp_smoke_substitution_attempted": True,
        "can_claim_sense_amp_smoke_substitution_passed": True,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
        "can_claim_drc_clean": False,
        "can_claim_lvs_clean": False,
        "can_claim_signoff_ready": False,
        "remaining_M11C_blockers_before_count": 3,
        "remaining_M11C_blockers_after_count": 0,
        "next_stage_allowed": NEXT_STAGE_ALLOWED,
        "can_enter_M11D_after_this_gate": True,
        "human_review_source": "M11CH gate closure records the provided human review result for the existing M11C clean-review and annotated-debug GDS artifacts.",
        "reviewed_gds_paths": [
            m11c["clean_review_gds_path"],
            m11c["annotated_debug_gds_path"],
        ],
        "m11c_manifest_artifact_count": len(manifest_rows),
        "m11c_smoke_check_item_count": len(smoke_rows),
        "m11c_diff_item_count": len(diff_rows),
        "excluded_modules": EXCLUDED_MODULES,
    }

    gate = {
        "stage": "M11CH",
        "gate_name": "Confirm M11C human review and clear M11C gate",
        "m11c_human_review_completed": True,
        "sense_amp_smoke_substitution_human_review_passed": True,
        "substituted_modules": SUBSTITUTED_MODULES,
        "excluded_modules_confirmed": True,
        "remaining_M11C_blockers_before_count": 3,
        "remaining_M11C_blockers_after_count": 0,
        "next_stage_allowed": NEXT_STAGE_ALLOWED,
        "can_enter_M11D_after_this_gate": True,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
        "can_claim_drc_clean": False,
        "can_claim_lvs_clean": False,
        "can_claim_signoff_ready": False,
    }

    machine_vs_human_summary = _render_md(
        "M11CH Machine Vs Human Verification Summary",
        [
            "- machine_verified_items_from_M11C: `22`",
            "- human_review_items_from_M11C: `3`",
            "- machine_scope: `GDS parse sanity, top bbox exact-match, excluded-module lock, sense_amp instance count, manifest/diff/smoke matrices.`",
            "- human_scope: `sense_amp top-context visual completeness, readability of 8 annotated sense_amp labels, and absence of obvious nearby power/routing damage.`",
            "- human_review_outcome: `All 3 required human-review items are recorded as passed for M11CH gate closure.`",
            "- claim_boundary_after_M11CH: `Only sense_amp-only smoke substitution attempted/pass may be claimed; full hardmacro substitution, DRC, LVS, and signoff claims remain closed.`",
        ],
    )

    report_md_lines = [
        "- status_file_read: `True`",
        "- status_file_updated: `True`",
        "- progress_file_updated: `True`",
        "- m11c_report_loaded: `True`",
        "- m11c_human_review_completed: `True`",
        "- sense_amp_visual_review_passed: `True`",
        "- sense_amp_annotation_readable: `True`",
        "- sense_amp_nearby_power_routing_not_visually_broken: `True`",
        "- sense_amp_smoke_substitution_human_review_passed: `True`",
        "- substituted_modules: `sense_amp`",
        "- excluded_modules_confirmed: `True`",
        "- remaining_M11C_blockers_before_count: `3`",
        "- remaining_M11C_blockers_after_count: `0`",
        "- can_claim_sense_amp_smoke_substitution_passed: `True`",
        "- can_claim_openyield_module_gds_hardmacro_substitution: `False`",
        "- can_claim_drc_clean: `False`",
        "- can_claim_lvs_clean: `False`",
        "- can_claim_signoff_ready: `False`",
        f"- next_stage_allowed: `{NEXT_STAGE_ALLOWED}`",
        "- can_enter_M11D_after_this_gate: `True`",
    ]
    gate_md_lines = [
        "- m11c_human_review_completed: `True`",
        "- sense_amp_smoke_substitution_human_review_passed: `True`",
        "- substituted_modules: `sense_amp`",
        "- excluded_modules_confirmed: `True`",
        "- remaining_M11C_blockers_before_count: `3`",
        "- remaining_M11C_blockers_after_count: `0`",
        f"- next_stage_allowed: `{NEXT_STAGE_ALLOWED}`",
        "- can_enter_M11D_after_this_gate: `True`",
        "- can_claim_openyield_module_gds_hardmacro_substitution: `False`",
        "- can_claim_drc_clean: `False`",
        "- can_claim_lvs_clean: `False`",
        "- can_claim_signoff_ready: `False`",
    ]
    evidence_summary = _render_md(
        "M11CH Confirm M11C Human Review Summary",
        [
            "- reviewed_stage: `M11C -> M11CH gate closure`",
            "- reviewed_outputs: `M11C_sense_amp_substituted_sram_clean_review.gds`, `M11C_sense_amp_substituted_sram_annotated_debug.gds`",
            "- conclusion: `sense_amp visual completeness, annotation readability, and nearby power/routing integrity are all recorded as passed.`",
            "- claim_boundary: `Pass applies only to sense_amp-only smoke substitution attempted/pass.`",
            f"- next_stage_allowed: `{NEXT_STAGE_ALLOWED}`",
        ],
    )

    _write_json(out_dir / "M11CH_confirm_M11C_human_review_report.json", report)
    _write_text(out_dir / "M11CH_confirm_M11C_human_review_report.md", _render_md("M11CH Confirm M11C Human Review Report", report_md_lines))
    _write_json(out_dir / "M11CH_M11D_entry_gate.json", gate)
    _write_text(out_dir / "M11CH_M11D_entry_gate.md", _render_md("M11CH M11D Entry Gate", gate_md_lines))
    _write_text(out_dir / "M11CH_machine_vs_human_verification_summary.md", machine_vs_human_summary)

    _write_json(out_json, report)
    _write_text(out_report, _render_md("M11CH Confirm M11C Human Review Report", report_md_lines))
    _write_text(repo_root / "docs/evidence/M11CH_confirm_M11C_human_review_summary.md", evidence_summary)

    gate_rows = [
        {"gate_field": key, "value": json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value, "status": "PASS"}
        for key, value in gate.items()
    ]
    _write_csv(repo_root / "docs/mapping/M11CH_M11D_entry_gate.csv", ["gate_field", "value", "status"], gate_rows)

    status["current_stage"] = "M11CH"
    status["next_stage"] = NEXT_STAGE_ALLOWED
    status["can_enter_next_stage_without_human_review"] = True
    status["next_stage_allowed"] = NEXT_STAGE_ALLOWED
    status["current_goal"] = "M11CH completed the M11C sense_amp-only smoke substitution human review closure and cleared entry into the post-substitution analysis/planning stage."
    status["m11c_human_review_completed"] = True
    status["m11c_sense_amp_visual_review_passed"] = True
    status["m11c_sense_amp_annotation_readable"] = True
    status["m11c_sense_amp_nearby_power_routing_not_visually_broken"] = True
    status["sense_amp_smoke_substitution_human_review_passed"] = True
    status["remaining_M11C_blockers_before_count"] = 3
    status["remaining_M11C_blockers_after_count"] = 0
    status["remaining_M11C_blockers"] = []
    status["can_claim_sense_amp_smoke_substitution_attempted"] = True
    status["can_claim_sense_amp_smoke_substitution_passed"] = True
    status["can_claim_openyield_module_gds_hardmacro_substitution"] = False
    status["can_claim_drc_clean"] = False
    status["can_claim_lvs_clean"] = False
    status["can_claim_signoff_ready"] = False
    status["can_enter_M11D_after_this_gate"] = True
    status["last_M11CH_report"] = report

    if "last_M11C_report" in status:
        status["last_M11C_report"]["m11c_human_review_completed"] = True
        status["last_M11C_report"]["sense_amp_visual_review_passed"] = True
        status["last_M11C_report"]["sense_amp_annotation_readable"] = True
        status["last_M11C_report"]["sense_amp_nearby_power_routing_not_visually_broken"] = True
        status["last_M11C_report"]["sense_amp_smoke_substitution_human_review_passed"] = True
        status["last_M11C_report"]["remaining_M11C_blockers_before_count"] = 3
        status["last_M11C_report"]["remaining_M11C_blockers_after_count"] = 0
        status["last_M11C_report"]["remaining_M11C_blockers"] = []
        status["last_M11C_report"]["human_review_items_after"] = []
        status["last_M11C_report"]["next_stage_allowed"] = NEXT_STAGE_ALLOWED
        status["last_M11C_report"]["can_enter_M11D_after_this_gate"] = True

    for asset in status.get("ten_required_assets_for_netlist_to_layout", []):
        if asset["asset_id"] in {"PHYSICAL_IMPLEMENTATION_LIBRARY", "PIN_BBOX_RAIL_METADATA"}:
            asset["blocking_for_next_stage"] = False
            asset["next_action"] = NEXT_STAGE_ALLOWED
            if "docs/mapping/M11CH_M11D_entry_gate.csv" not in asset["evidence_paths"]:
                asset["evidence_paths"].append("docs/mapping/M11CH_M11D_entry_gate.csv")
        if asset["asset_id"] == "VERIFICATION_AND_TRACE":
            asset["evidence_paths"] = [
                "docs/M11CH_confirm_M11C_human_review_report.json",
                "docs/evidence/M11CH_confirm_M11C_human_review_summary.md",
                "docs/mapping/M11CH_M11D_entry_gate.csv",
                "outputs/M11CH_confirm_M11C_human_review/current_supported_config/M11CH_machine_vs_human_verification_summary.md",
            ]
            asset["next_action"] = NEXT_STAGE_ALLOWED
    status["next_assets_to_fill_in_order"] = [
        NEXT_STAGE_ALLOWED,
        "M12A_VARIATION_GDS_GENERATION",
        "M12B_ROUTING_POWER_ADAPTATION",
        "M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE",
    ]

    _write_text(status_md, _update_status_md())
    _write_json(status_json, status)
    _write_text(progress_md, _update_progress_md(progress_text))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--progress-md", required=True)
    parser.add_argument("--m11c-report", required=True)
    parser.add_argument("--m11c-manifest", required=True)
    parser.add_argument("--m11c-smoke-check", required=True)
    parser.add_argument("--m11c-diff", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    args = parser.parse_args()

    run_m11ch_confirm_m11c_human_review(
        repo_root=Path(args.repo_root),
        status_md=Path(args.status_md),
        status_json=Path(args.status_json),
        progress_md=Path(args.progress_md),
        m11c_report=Path(args.m11c_report),
        m11c_manifest=Path(args.m11c_manifest),
        m11c_smoke_check=Path(args.m11c_smoke_check),
        m11c_diff=Path(args.m11c_diff),
        out_dir=Path(args.out_dir),
        out_json=Path(args.out_json),
        out_report=Path(args.out_report),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
