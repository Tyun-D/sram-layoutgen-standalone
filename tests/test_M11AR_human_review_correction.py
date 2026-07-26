from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M11AR_human_review_correction import run_m11ar_human_review_correction  # noqa: E402


def main() -> int:
    report = run_m11ar_human_review_correction(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m11a_report=REPO_ROOT / "docs/M11A_module_gds_qualification_report.json",
        m11a_decision=REPO_ROOT / "docs/mapping/M11A_hardmacro_substitution_decision.csv",
        m11a_pin_metadata=REPO_ROOT / "docs/mapping/M11A_pin_bbox_rail_metadata.csv",
        m11a_comparison=REPO_ROOT / "docs/mapping/M11A_module_vs_golden_leaf_comparison.csv",
        out_dir=REPO_ROOT / "outputs/M11AR_human_review_correction/current_supported_config",
        out_json=REPO_ROOT / "docs/M11AR_human_review_correction_report.json",
        out_report=REPO_ROOT / "docs/M11AR_human_review_correction_report.md",
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["human_review_applied"] is True
    assert report["unknown_golden_region_markers_are_real_modules"] is False
    assert report["direct_hardmacro_replace_count_before"] == 4
    assert report["direct_hardmacro_replace_count_after"] == 2
    assert report["first_substitution_candidates_after"] == ["sense_amp", "wordline_driver"]
    assert "column_mux" in report["downgraded_modules"]
    assert "write_driver" in report["downgraded_modules"]
    assert report["control_logic_human_review_result"] == "SEMANTIC_REFERENCE_ONLY"
    assert report["safe_to_attempt_selective_substitution_scope"] == ["sense_amp", "wordline_driver"]
    assert report["must_run_M11B_before_substitution"] is True
    assert report["can_claim_openyield_module_gds_hardmacro_substitution"] is False
    assert report["next_stage_allowed"] == "M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION_FOR_SENSE_AMP_AND_WORDLINE_DRIVER"
    assert report["can_enter_M11B_after_this_gate"] is True
    assert report["can_enter_next_stage_without_human_review"] is False

    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M11AR"
    assert status["next_stage_allowed"] == "M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION_FOR_SENSE_AMP_AND_WORDLINE_DRIVER"
    assert status["can_claim_openyield_module_gds_hardmacro_substitution"] is False

    for path in [
        REPO_ROOT / "docs/M11AR_human_review_correction_report.json",
        REPO_ROOT / "docs/M11AR_human_review_correction_report.md",
        REPO_ROOT / "docs/evidence/M11AR_human_review_correction_summary.md",
        REPO_ROOT / "docs/mapping/M11AR_corrected_hardmacro_substitution_decision.csv",
        REPO_ROOT / "docs/mapping/M11AR_corrected_first_substitution_plan.csv",
        REPO_ROOT / "outputs/M11AR_human_review_correction/current_supported_config/M11AR_human_review_correction_report.json",
        REPO_ROOT / "outputs/M11AR_human_review_correction/current_supported_config/M11AR_human_review_correction_report.md",
        REPO_ROOT / "outputs/M11AR_human_review_correction/current_supported_config/M11AR_corrected_hardmacro_substitution_decision.csv",
        REPO_ROOT / "outputs/M11AR_human_review_correction/current_supported_config/M11AR_corrected_hardmacro_substitution_decision.md",
        REPO_ROOT / "outputs/M11AR_human_review_correction/current_supported_config/M11AR_corrected_first_substitution_plan.csv",
        REPO_ROOT / "outputs/M11AR_human_review_correction/current_supported_config/M11AR_corrected_first_substitution_plan.md",
        REPO_ROOT / "outputs/M11AR_human_review_correction/current_supported_config/review_gds_manifest.json",
        REPO_ROOT / "outputs/M11AR_human_review_correction/current_supported_config/review_gds_manifest.md",
    ]:
        assert path.exists(), path
    print("M11AR_human_review_correction_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
