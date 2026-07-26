from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M8_reproduce_uploaded_golden import run_m8_reproduce_uploaded_golden  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M8_reproduce_uploaded_golden/current_supported_config"
    out_json = REPO_ROOT / "docs/M8_reproduce_uploaded_golden_report.json"
    out_report = REPO_ROOT / "docs/M8_reproduce_uploaded_golden_report.md"
    report = run_m8_reproduce_uploaded_golden(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        golden_reference=REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        golden_clean_review=REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/golden_reference_clean_review.gds",
        m7_extracted_dir=REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/extracted",
        m7c_report=REPO_ROOT / "docs/M7C_golden_reference_confirmation_report.json",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["m7c_confirmation_loaded"] is True
    assert report["golden_reference_found"] is True
    assert report["sram_spec_available"] is True
    assert report["generation_entry_found"] is True
    assert report["generated_from_layoutgen_source"] is True
    assert report["reference_file_copied_as_output"] is False
    assert report["reproduced_gds_generated"] is True
    assert report["reproduced_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["reproduced_top_cell"] == "sram_8x64_wpr4_fd45"
    assert report["column_mux_real_check_passed"] is True
    assert report["power_rail_overlap_real_check_passed"] is True
    assert report["reference_vs_reproduced_geometry_match"] in {
        "EXACT_MATCH",
        "NEAR_MATCH",
        "STRUCTURAL_MATCH_WITH_GEOMETRY_DELTA",
    }
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    for name in [
        "layoutgen_reproduced_from_uploaded_golden.gds",
        "layoutgen_reproduced_from_uploaded_golden_clean_review.gds",
        "layoutgen_reproduced_from_uploaded_golden_spec_annotated.gds",
        "golden_reference_copy_for_comparison.gds",
        "SRAM_SPEC.json",
        "SRAM_SPEC.md",
        "M8_generation_entry_trace.json",
        "M8_generation_entry_trace.md",
        "M8_reference_geometry_diff_report.json",
        "M8_reference_geometry_diff_report.md",
        "M8_power_rail_overlap_real_check.json",
        "M8_power_rail_overlap_real_check.md",
        "M8_column_mux_real_check.json",
        "M8_column_mux_real_check.md",
        "M8_reproduction_status_report.json",
        "M8_reproduction_status_report.md",
        "review_gds_manifest.json",
        "review_gds_manifest.md",
    ]:
        assert (out_dir / name).exists(), name
    assert out_json.exists()
    assert out_report.exists()
    assert (REPO_ROOT / "docs/evidence/M8_reproduce_uploaded_golden_summary.md").exists()
    for name in [
        "docs/mapping/M8_generation_parameter_matrix.csv",
        "docs/mapping/M8_reference_geometry_comparison_matrix.csv",
        "docs/mapping/M8_power_rail_overlap_matrix.csv",
        "docs/mapping/M8_column_mux_matrix.csv",
        "docs/mapping/M8_remaining_gap_matrix.csv",
    ]:
        assert (REPO_ROOT / name).exists(), name
    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M8"
    assert status["next_stage"] == "WAIT_HUMAN_KLAYOUT_REVIEW"
    print("M8_reproduce_uploaded_golden_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
