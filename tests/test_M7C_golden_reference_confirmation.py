from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M7C_golden_reference_confirmation import run_m7c_golden_reference_confirmation  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M7C_golden_reference_confirmed/current_supported_config"
    out_json = REPO_ROOT / "docs/M7C_golden_reference_confirmation_report.json"
    out_report = REPO_ROOT / "docs/M7C_golden_reference_confirmation_report.md"
    report = run_m7c_golden_reference_confirmation(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        m7_report=REPO_ROOT / "docs/M7_correct_golden_reference_report.json",
        golden_reference=REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        golden_clean_review=REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/golden_reference_clean_review.gds",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["golden_reference_user_confirmed"] is True
    assert report["golden_reference_is_now_locked"] is True
    assert report["current_golden_reference_path"] == "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds"
    assert (
        report["current_golden_reference_clean_review_path"]
        == "outputs/M7_correct_golden_reference/current_supported_config/golden_reference_clean_review.gds"
    )
    assert report["hybrid_openyield_rail_overlap_is_golden"] is False
    assert report["new_uploaded_reference_is_golden"] is True
    assert report["m7_blockers_before_count"] == 2
    assert report["m7_blockers_after_count"] == 0
    assert report["next_stage_allowed"] == "M8_REPRODUCE_UPLOADED_GOLDEN_REFERENCE"
    assert report["can_enter_M8_after_this_gate"] is True
    assert report["human_klayout_review_required_for_M8_output"] is True
    assert report["can_enter_next_stage_without_human_review"] is False
    assert (out_dir / "golden_reference_confirmation_report.json").exists()
    assert (out_dir / "golden_reference_confirmation_report.md").exists()
    assert (out_dir / "review_gds_manifest.json").exists()
    assert (out_dir / "review_gds_manifest.md").exists()
    assert (out_dir / "golden_reference_clean_review.gds").exists()
    assert out_json.exists()
    assert out_report.exists()
    assert (REPO_ROOT / "docs/evidence/M7C_golden_reference_confirmation_summary.md").exists()
    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["golden_reference_user_confirmed"] is True
    assert status["golden_reference_is_now_locked"] is True
    assert status["current_golden_reference_path"] == report["current_golden_reference_path"]
    assert status["current_golden_reference_clean_review_path"] == report["current_golden_reference_clean_review_path"]
    assert status["hybrid_openyield_rail_overlap_is_golden"] is False
    assert status["next_stage_must_reproduce_uploaded_golden_reference"] is True
    assert status["next_stage_allowed"] == "M8_REPRODUCE_UPLOADED_GOLDEN_REFERENCE"
    print("M7C_golden_reference_confirmation_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
