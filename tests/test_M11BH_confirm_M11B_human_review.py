from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M11BH_confirm_M11B_human_review import run_m11bh_confirm_m11b_human_review  # noqa: E402


def main() -> int:
    report = run_m11bh_confirm_m11b_human_review(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m11b_report=REPO_ROOT / "docs/M11B_pin_bbox_rail_metadata_report.json",
        m11b_readiness=REPO_ROOT / "docs/mapping/M11B_substitution_readiness_matrix.csv",
        m11b_pin_metadata=REPO_ROOT / "docs/mapping/M11B_deep_pin_bbox_rail_metadata.csv",
        out_dir=REPO_ROOT / "outputs/M11BH_confirm_M11B_human_review/current_supported_config",
        out_json=REPO_ROOT / "docs/M11BH_confirm_M11B_human_review_report.json",
        out_report=REPO_ROOT / "docs/M11BH_confirm_M11B_human_review_report.md",
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m11b_report_loaded"] is True
    assert report["m11b_machine_verification_loaded"] is True
    assert report["m11b_human_review_completed"] is True
    assert report["sense_amp_visual_review_passed"] is True
    assert report["sense_amp_ready_for_M11C_after_human_review"] is True
    assert report["wordline_driver_excluded_from_M11C"] is True
    assert report["ready_for_M11C_modules_after_human_review"] == ["sense_amp"]
    assert "wordline_driver" in report["not_ready_modules_after_human_review"]
    assert report["M11C_scope"] == "sense_amp_only"
    assert report["M11C_scope_locked"] is True
    assert report["remaining_M11B_blockers_before_count"] == 3
    assert report["remaining_M11B_blockers_after_count"] == 0
    assert report["can_claim_openyield_module_gds_hardmacro_substitution"] is False
    assert report["next_stage_allowed"] == "M11C_SENSE_AMP_ONLY_SMOKE_SUBSTITUTION"
    assert report["can_enter_M11C_after_this_gate"] is True

    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M11BH"
    assert status["next_stage_allowed"] == "M11C_SENSE_AMP_ONLY_SMOKE_SUBSTITUTION"
    assert status["can_enter_next_stage_without_human_review"] is True
    assert status["m11b_human_review_completed"] is True

    for rel in [
        "docs/M11BH_confirm_M11B_human_review_report.json",
        "docs/M11BH_confirm_M11B_human_review_report.md",
        "docs/evidence/M11BH_confirm_M11B_human_review_summary.md",
        "docs/mapping/M11BH_M11C_scope_lock.csv",
        "outputs/M11BH_confirm_M11B_human_review/current_supported_config/M11BH_confirm_M11B_human_review_report.json",
        "outputs/M11BH_confirm_M11B_human_review/current_supported_config/M11BH_confirm_M11B_human_review_report.md",
        "outputs/M11BH_confirm_M11B_human_review/current_supported_config/M11BH_M11C_scope_lock.json",
        "outputs/M11BH_confirm_M11B_human_review/current_supported_config/M11BH_M11C_scope_lock.md",
        "outputs/M11BH_confirm_M11B_human_review/current_supported_config/M11BH_machine_vs_human_verification_summary.md",
    ]:
        assert (REPO_ROOT / rel).exists(), rel
    print("M11BH_confirm_M11B_human_review_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
