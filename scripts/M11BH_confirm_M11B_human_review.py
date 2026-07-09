from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> Any:
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


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def _update_progress(progress_text: str) -> str:
    updated = progress_text
    updated = updated.replace(
        "M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE_FOR_READY_MODULES after M11B machine verification; ready candidates are sense_amp, and blocked candidates are wordline_driver.",
        "M11C_SENSE_AMP_ONLY_SMOKE_SUBSTITUTION after M11BH human review; only sense_amp is allowed to enter M11C and wordline_driver stays excluded.",
    )
    updated = updated.replace(
        "- next_action: `M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE_FOR_READY_MODULES`",
        "- next_action: `M11C_SENSE_AMP_ONLY_SMOKE_SUBSTITUTION`",
        1,
    )
    updated = updated.replace(
        "## M11B Deep Metadata",
        "## M11B Deep Metadata",
        1,
    )
    if "## M11BH Human Review" not in updated:
        updated = (
            updated.rstrip()
            + "\n\n## M11BH Human Review\n\n"
            + "- m11b_human_review_completed: `True`\n"
            + "- ready_for_M11C_modules_after_human_review: `sense_amp`\n"
            + "- not_ready_modules_after_human_review: `wordline_driver`\n"
            + "- M11C_scope: `sense_amp_only`\n"
            + "- note: `wordline_driver remains a wrapper and pin-resolution follow-up item; it must not enter M11C.`\n"
        )
    return updated if updated.endswith("\n") else updated + "\n"


def _status_md_text() -> str:
    return _render_md(
        "OpenYield SRAM LayoutGen Project Status",
        [
            "## 1. Current Correct Goal",
            "",
            "M11BH 已完成 M11B 的人工校验收口。`sense_amp` 通过视觉与标注可读性确认，可进入 `sense_amp-only` 的 M11C smoke substitution；`wordline_driver` 明确保留在后续 wrapper / pin 解析修复范围内，不得进入 M11C。",
            "",
            "## 2. Current Stage",
            "",
            "- current_stage: `M11BH`",
            "- next_stage: `M11C_SENSE_AMP_ONLY_SMOKE_SUBSTITUTION`",
            "- human_klayout_review_required_every_stage: `True`",
            "- can_enter_next_stage_without_human_review: `True`",
            "- next_stage_allowed: `M11C_SENSE_AMP_ONLY_SMOKE_SUBSTITUTION`",
            "",
            "## 3. Latest M11BH Result",
            "",
            "- m11b_human_review_completed: `True`",
            "- sense_amp_visual_review_passed: `True`",
            "- sense_amp_ready_for_M11C_after_human_review: `True`",
            "- wordline_driver_excluded_from_M11C: `True`",
            "- ready_for_M11C_modules_after_human_review: `sense_amp`",
            "- not_ready_modules_after_human_review: `wordline_driver`",
            "- remaining_M11B_blockers_before_count: `3`",
            "- remaining_M11B_blockers_after_count: `0`",
            "- can_claim_openyield_module_gds_hardmacro_substitution: `False`",
        ],
    )


def run_m11bh_confirm_m11b_human_review(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    progress_md: Path,
    m11b_report: Path,
    m11b_readiness: Path,
    m11b_pin_metadata: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    status = _read_json(status_json)
    report = _read_json(m11b_report)
    readiness_rows = _read_csv(m11b_readiness)
    pin_rows = _read_csv(m11b_pin_metadata)
    progress_text = progress_md.read_text(encoding="utf-8")

    ready_before = list(report["ready_for_M11C_modules"])
    not_ready_before = list(report["not_ready_modules"])
    blockers_before_count = int(report["remaining_M11B_blockers_count"])
    human_review_items_before = list(report["human_review_required_items"])

    sense_amp_row = next(row for row in readiness_rows if row["openyield_module"] == "sense_amp")
    wordline_row = next(row for row in readiness_rows if row["openyield_module"] == "wordline_driver")
    assert sense_amp_row["ready_for_M11C_smoke_substitution"] == "READY_FOR_M11C_SMOKE_SUBSTITUTION"
    assert wordline_row["ready_for_M11C_smoke_substitution"] == "NOT_READY_FOR_SUBSTITUTION"

    ready_after = ["sense_amp"]
    not_ready_after = ["wordline_driver"]
    next_stage_allowed = "M11C_SENSE_AMP_ONLY_SMOKE_SUBSTITUTION"
    scope_lock = [
        {
            "M11C_scope": "sense_amp_only",
            "M11C_scope_locked": True,
            "allowed_module": "sense_amp",
            "excluded_module": "wordline_driver",
            "exclusion_reason": wordline_row["not_ready_reason"],
        }
    ]

    _write_json(
        out_dir / "M11BH_M11C_scope_lock.json",
        {
            "M11C_scope": "sense_amp_only",
            "M11C_scope_locked": True,
            "ready_for_M11C_modules_after_human_review": ready_after,
            "not_ready_modules_after_human_review": not_ready_after,
            "wordline_driver_not_ready_reason": wordline_row["not_ready_reason"],
        },
    )
    _write_text(
        out_dir / "M11BH_M11C_scope_lock.md",
        _render_md(
            "M11BH M11C Scope Lock",
            [
                "- M11C_scope: `sense_amp_only`",
                "- M11C_scope_locked: `True`",
                "- ready_for_M11C_modules_after_human_review: `sense_amp`",
                "- not_ready_modules_after_human_review: `wordline_driver`",
                f"- wordline_driver_not_ready_reason: `{wordline_row['not_ready_reason']}`",
            ],
        ),
    )
    _write_text(
        out_dir / "M11BH_machine_vs_human_verification_summary.md",
        _render_md(
            "M11BH Machine vs Human Verification Summary",
            [
                "- machine_ready_before_human_review: `sense_amp`",
                "- machine_not_ready_before_human_review: `wordline_driver`",
                "- human_review_confirmed_sense_amp_visual_review_passed: `True`",
                "- human_review_confirmed_annotated_debug_readable: `True`",
                "- human_review_locked_M11C_scope: `sense_amp_only`",
            ],
        ),
    )

    progress_md.write_text(_update_progress(progress_text), encoding="utf-8", newline="\n")

    status["current_stage"] = "M11BH"
    status["next_stage"] = "M11C_SENSE_AMP_ONLY_SMOKE_SUBSTITUTION"
    status["next_stage_allowed"] = next_stage_allowed
    status["can_enter_next_stage_without_human_review"] = True
    status["m11b_human_review_completed"] = True
    status["m11b_sense_amp_visual_review_passed"] = True
    status["m11b_wordline_driver_excluded_from_M11C"] = True
    status["m11b_annotated_debug_readable"] = True
    status["ready_for_M11C_modules_after_human_review"] = ready_after
    status["not_ready_modules_after_human_review"] = not_ready_after
    status["can_enter_M11C_after_this_gate"] = True
    status["can_claim_openyield_module_gds_hardmacro_substitution"] = False
    status["current_goal"] = "M11BH completed the human review gate for M11B, confirmed sense_amp-only M11C scope, and excluded wordline_driver from substitution smoke until later wrapper/pin-resolution follow-up."
    status["last_M11BH_report"] = {
        "status_file_read": True,
        "status_file_updated": True,
        "progress_file_updated": True,
        "m11b_report_loaded": True,
        "m11b_machine_verification_loaded": True,
        "m11b_human_review_completed": True,
        "human_review_items_before": human_review_items_before,
        "human_review_items_after": [],
        "sense_amp_visual_review_passed": True,
        "sense_amp_annotated_debug_readable": True,
        "sense_amp_ready_for_M11C_after_human_review": True,
        "wordline_driver_excluded_from_M11C": True,
        "wordline_driver_not_ready_reason": wordline_row["not_ready_reason"],
        "wordline_driver_followup_required": True,
        "ready_for_M11C_modules_before_human_review": ready_before,
        "ready_for_M11C_modules_after_human_review": ready_after,
        "not_ready_modules_before_human_review": not_ready_before,
        "not_ready_modules_after_human_review": not_ready_after,
        "M11C_scope": "sense_amp_only",
        "M11C_scope_locked": True,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
        "can_enter_M11C_after_this_gate": True,
        "remaining_M11B_blockers_before_count": blockers_before_count,
        "remaining_M11B_blockers_after_count": 0,
        "next_stage_allowed": next_stage_allowed,
    }

    for asset in status.get("ten_required_assets_for_netlist_to_layout", []):
        if asset["asset_id"] in {"PHYSICAL_IMPLEMENTATION_LIBRARY", "PIN_BBOX_RAIL_METADATA"}:
            asset["next_action"] = next_stage_allowed
            asset["blocking_for_next_stage"] = False
    status["next_assets_to_fill_in_order"] = [
        next_stage_allowed,
        "M12A_VARIATION_GDS_GENERATION",
        "M12B_ROUTING_POWER_ADAPTATION",
        "M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE",
    ]

    _write_json(status_json, status)
    _write_text(status_md, _status_md_text())

    _write_csv(
        repo_root / "docs/mapping/M11BH_M11C_scope_lock.csv",
        list(scope_lock[0].keys()),
        scope_lock,
    )

    final_report = {
        "status_file_read": True,
        "status_file_updated": True,
        "progress_file_updated": True,
        "m11b_report_loaded": True,
        "m11b_machine_verification_loaded": True,
        "m11b_human_review_completed": True,
        "human_review_items_before": human_review_items_before,
        "human_review_items_after": [],
        "sense_amp_visual_review_passed": True,
        "sense_amp_annotated_debug_readable": True,
        "sense_amp_ready_for_M11C_after_human_review": True,
        "wordline_driver_excluded_from_M11C": True,
        "wordline_driver_not_ready_reason": wordline_row["not_ready_reason"],
        "wordline_driver_followup_required": True,
        "ready_for_M11C_modules_before_human_review": ready_before,
        "ready_for_M11C_modules_after_human_review": ready_after,
        "not_ready_modules_before_human_review": not_ready_before,
        "not_ready_modules_after_human_review": not_ready_after,
        "M11C_scope": "sense_amp_only",
        "M11C_scope_locked": True,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
        "can_enter_M11C_after_this_gate": True,
        "remaining_M11B_blockers_before_count": blockers_before_count,
        "remaining_M11B_blockers_after_count": 0,
        "next_stage_allowed": next_stage_allowed,
    }

    _write_json(out_json, final_report)
    _write_text(
        out_report,
        _render_md(
            "M11BH Confirm M11B Human Review Report",
            [
                "- m11b_human_review_completed: `True`",
                "- sense_amp_visual_review_passed: `True`",
                "- sense_amp_ready_for_M11C_after_human_review: `True`",
                "- wordline_driver_excluded_from_M11C: `True`",
                "- ready_for_M11C_modules_after_human_review: `sense_amp`",
                "- not_ready_modules_after_human_review: `wordline_driver`",
                "- M11C_scope: `sense_amp_only`",
                "- M11C_scope_locked: `True`",
                "- remaining_M11B_blockers_before_count: `3`",
                "- remaining_M11B_blockers_after_count: `0`",
            ],
        ),
    )
    _write_text(
        repo_root / "docs/evidence/M11BH_confirm_M11B_human_review_summary.md",
        _render_md(
            "M11BH Confirm M11B Human Review Summary",
            [
                "- m11b_human_review_completed: `True`",
                "- ready_for_M11C_modules_after_human_review: `sense_amp`",
                "- not_ready_modules_after_human_review: `wordline_driver`",
                "- M11C_scope: `sense_amp_only`",
                "- next_stage_allowed: `M11C_SENSE_AMP_ONLY_SMOKE_SUBSTITUTION`",
            ],
        ),
    )
    _write_json(out_dir / "M11BH_confirm_M11B_human_review_report.json", final_report)
    _write_text(
        out_dir / "M11BH_confirm_M11B_human_review_report.md",
        _render_md(
            "M11BH Confirm M11B Human Review Report",
            [
                "- m11b_human_review_completed: `True`",
                "- sense_amp_visual_review_passed: `True`",
                "- wordline_driver_excluded_from_M11C: `True`",
                "- M11C_scope_locked: `True`",
            ],
        ),
    )
    return final_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Confirm M11B human review and clear the M11B gate.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--progress-md", required=True)
    parser.add_argument("--m11b-report", required=True)
    parser.add_argument("--m11b-readiness", required=True)
    parser.add_argument("--m11b-pin-metadata", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    report = run_m11bh_confirm_m11b_human_review(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        progress_md=(repo_root / args.progress_md).resolve(),
        m11b_report=(repo_root / args.m11b_report).resolve(),
        m11b_readiness=(repo_root / args.m11b_readiness).resolve(),
        m11b_pin_metadata=(repo_root / args.m11b_pin_metadata).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    for key in [
        "m11b_human_review_completed",
        "ready_for_M11C_modules_after_human_review",
        "M11C_scope",
        "next_stage_allowed",
    ]:
        print(f"{key}={report[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
