from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M11CH_confirm_M11C_human_review import (  # noqa: E402
    NEXT_STAGE_ALLOWED,
    run_m11ch_confirm_m11c_human_review,
)


def main() -> int:
    report = run_m11ch_confirm_m11c_human_review(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m11c_report=REPO_ROOT / "docs/M11C_sense_amp_smoke_substitution_report.json",
        m11c_manifest=REPO_ROOT / "docs/mapping/M11C_sense_amp_substitution_manifest.csv",
        m11c_smoke_check=REPO_ROOT / "docs/mapping/M11C_sense_amp_smoke_check_matrix.csv",
        m11c_diff=REPO_ROOT / "docs/mapping/M11C_sense_amp_diff_matrix.csv",
        out_dir=REPO_ROOT / "outputs/M11CH_confirm_M11C_human_review/current_supported_config",
        out_json=REPO_ROOT / "docs/M11CH_confirm_M11C_human_review_report.json",
        out_report=REPO_ROOT / "docs/M11CH_confirm_M11C_human_review_report.md",
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m11c_report_loaded"] is True
    assert report["m11c_human_review_completed"] is True
    assert report["sense_amp_visual_review_passed"] is True
    assert report["sense_amp_annotation_readable"] is True
    assert report["sense_amp_nearby_power_routing_not_visually_broken"] is True
    assert report["sense_amp_smoke_substitution_attempted"] is True
    assert report["sense_amp_smoke_substitution_passed"] is True
    assert report["sense_amp_smoke_substitution_human_review_passed"] is True
    assert report["substituted_modules"] == ["sense_amp"]
    assert report["excluded_modules_confirmed"] is True
    assert report["remaining_M11C_blockers_before_count"] == 3
    assert report["remaining_M11C_blockers_after_count"] == 0
    assert report["can_claim_sense_amp_smoke_substitution_attempted"] is True
    assert report["can_claim_sense_amp_smoke_substitution_passed"] is True
    assert report["can_claim_openyield_module_gds_hardmacro_substitution"] is False
    assert report["can_claim_drc_clean"] is False
    assert report["can_claim_lvs_clean"] is False
    assert report["can_claim_signoff_ready"] is False
    assert report["next_stage_allowed"] == NEXT_STAGE_ALLOWED
    assert report["can_enter_M11D_after_this_gate"] is True

    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M11CH"
    assert status["next_stage"] == NEXT_STAGE_ALLOWED
    assert status["next_stage_allowed"] == NEXT_STAGE_ALLOWED
    assert status["can_enter_next_stage_without_human_review"] is True
    assert status["m11c_human_review_completed"] is True
    assert status["m11c_sense_amp_visual_review_passed"] is True
    assert status["m11c_sense_amp_annotation_readable"] is True
    assert status["m11c_sense_amp_nearby_power_routing_not_visually_broken"] is True
    assert status["remaining_M11C_blockers_before_count"] == 3
    assert status["remaining_M11C_blockers_after_count"] == 0
    assert status["can_enter_M11D_after_this_gate"] is True

    progress_text = (REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md").read_text(encoding="utf-8")
    assert "## M11CH Human Review Closure" in progress_text
    assert NEXT_STAGE_ALLOWED in progress_text

    for rel in [
        "docs/M11CH_confirm_M11C_human_review_report.json",
        "docs/M11CH_confirm_M11C_human_review_report.md",
        "docs/evidence/M11CH_confirm_M11C_human_review_summary.md",
        "docs/mapping/M11CH_M11D_entry_gate.csv",
        "outputs/M11CH_confirm_M11C_human_review/current_supported_config/M11CH_confirm_M11C_human_review_report.json",
        "outputs/M11CH_confirm_M11C_human_review/current_supported_config/M11CH_confirm_M11C_human_review_report.md",
        "outputs/M11CH_confirm_M11C_human_review/current_supported_config/M11CH_M11D_entry_gate.json",
        "outputs/M11CH_confirm_M11C_human_review/current_supported_config/M11CH_M11D_entry_gate.md",
        "outputs/M11CH_confirm_M11C_human_review/current_supported_config/M11CH_machine_vs_human_verification_summary.md",
    ]:
        assert (REPO_ROOT / rel).exists(), rel
    print("M11CH_confirm_M11C_human_review_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
