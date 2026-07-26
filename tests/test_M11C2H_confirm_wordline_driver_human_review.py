from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M11C2H_confirm_wordline_driver_human_review import (  # noqa: E402
    NEXT_STAGE_ALLOWED,
    run_m11c2h_confirm_wordline_driver_human_review,
)


def main() -> int:
    report = run_m11c2h_confirm_wordline_driver_human_review(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m11c2_report=REPO_ROOT / "docs/M11C2_wordline_driver_smoke_substitution_report.json",
        m11c2_manifest=REPO_ROOT / "docs/mapping/M11C2_wordline_driver_substitution_manifest.csv",
        m11c2_smoke_check=REPO_ROOT / "docs/mapping/M11C2_wordline_driver_smoke_check_matrix.csv",
        m11c2_diff=REPO_ROOT / "docs/mapping/M11C2_wordline_driver_diff_matrix.csv",
        m11c2_proof=REPO_ROOT / "docs/mapping/M11C2_real_substitution_proof.csv",
        out_dir=REPO_ROOT / "outputs/M11C2H_confirm_wordline_driver_human_review/current_supported_config",
        out_json=REPO_ROOT / "docs/M11C2H_confirm_wordline_driver_human_review_report.json",
        out_report=REPO_ROOT / "docs/M11C2H_confirm_wordline_driver_human_review_report.md",
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m11c2_report_loaded"] is True
    assert report["m11c2_human_review_completed"] is True
    assert report["wordline_driver_visual_review_passed"] is True
    assert report["wordline_driver_annotation_readable"] is True
    assert report["wordline_driver_nearby_power_routing_review_status"] == "INCONCLUSIVE_BASELINE_ROUTING_LIMITED"
    assert report["wordline_driver_nearby_power_routing_visually_confirmed_clean"] is False
    assert report["no_obvious_new_break_reported_by_human"] is True
    assert report["routing_clean_cannot_be_claimed"] is True
    assert report["power_clean_cannot_be_claimed"] is True
    assert report["wordline_driver_smoke_substitution_human_review_accepted_with_caveat"] is True
    assert report["substituted_modules"] == ["wordline_driver"]
    assert report["excluded_modules_confirmed"] is True
    assert report["remaining_M11C2_blockers_before_count"] == 3
    assert report["remaining_M11C2_blockers_after_count"] == 0
    assert report["can_claim_wordline_driver_smoke_substitution_attempted"] is True
    assert report["can_claim_wordline_driver_smoke_substitution_passed"] is True
    assert report["can_claim_openyield_module_gds_hardmacro_substitution"] is False
    assert report["can_claim_routing_clean"] is False
    assert report["can_claim_power_clean"] is False
    assert report["can_claim_drc_clean"] is False
    assert report["can_claim_lvs_clean"] is False
    assert report["can_claim_signoff_ready"] is False
    assert report["recommended_next_stage"] == NEXT_STAGE_ALLOWED
    assert report["next_stage_allowed"] == NEXT_STAGE_ALLOWED
    assert report["can_enter_M11V_after_this_gate"] is True

    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M11C2H"
    assert status["next_stage"] == NEXT_STAGE_ALLOWED
    assert status["next_stage_allowed"] == NEXT_STAGE_ALLOWED
    assert status["can_enter_next_stage_without_human_review"] is True
    assert status["m11c2_human_review_completed"] is True
    assert status["m11c2_wordline_driver_visual_review_passed"] is True
    assert status["m11c2_wordline_driver_annotation_readable"] is True
    assert status["m11c2_wordline_driver_nearby_power_routing_review_status"] == "INCONCLUSIVE_BASELINE_ROUTING_LIMITED"
    assert status["m11c2_no_obvious_new_break_reported_by_human"] is True
    assert status["m11c2_nearby_power_routing_visually_confirmed_clean"] is False
    assert status["remaining_M11C2_blockers_before_count"] == 3
    assert status["remaining_M11C2_blockers_after_count"] == 0
    assert status["can_enter_M11V_after_this_gate"] is True

    progress_text = (REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md").read_text(encoding="utf-8")
    assert "## M11C2H Human Review Closure" in progress_text
    assert NEXT_STAGE_ALLOWED in progress_text

    for rel in [
        "docs/M11C2H_confirm_wordline_driver_human_review_report.json",
        "docs/M11C2H_confirm_wordline_driver_human_review_report.md",
        "docs/evidence/M11C2H_confirm_wordline_driver_human_review_summary.md",
        "docs/mapping/M11C2H_M11V_entry_gate.csv",
        "docs/mapping/M11C2H_routing_power_caveat.csv",
        "outputs/M11C2H_confirm_wordline_driver_human_review/current_supported_config/M11C2H_confirm_wordline_driver_human_review_report.json",
        "outputs/M11C2H_confirm_wordline_driver_human_review/current_supported_config/M11C2H_confirm_wordline_driver_human_review_report.md",
        "outputs/M11C2H_confirm_wordline_driver_human_review/current_supported_config/M11C2H_routing_power_caveat.json",
        "outputs/M11C2H_confirm_wordline_driver_human_review/current_supported_config/M11C2H_routing_power_caveat.md",
        "outputs/M11C2H_confirm_wordline_driver_human_review/current_supported_config/M11C2H_M11V_entry_gate.json",
        "outputs/M11C2H_confirm_wordline_driver_human_review/current_supported_config/M11C2H_M11V_entry_gate.md",
        "outputs/M11C2H_confirm_wordline_driver_human_review/current_supported_config/M11C2H_machine_vs_human_verification_summary.md",
    ]:
        assert (REPO_ROOT / rel).exists(), rel
    print("M11C2H_confirm_wordline_driver_human_review_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
