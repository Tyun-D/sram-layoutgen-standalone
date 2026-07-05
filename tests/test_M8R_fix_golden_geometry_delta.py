from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M8R_fix_golden_geometry_delta import run_m8r_fix_golden_geometry_delta  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M8R_fix_golden_geometry_delta/current_supported_config"
    out_json = REPO_ROOT / "docs/M8R_fix_golden_geometry_delta_report.json"
    out_report = REPO_ROOT / "docs/M8R_fix_golden_geometry_delta_report.md"
    report = run_m8r_fix_golden_geometry_delta(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        golden_reference=REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        m8_reproduced=REPO_ROOT / "outputs/M8_reproduce_uploaded_golden/current_supported_config/layoutgen_reproduced_from_uploaded_golden.gds",
        m8_raw_dir=REPO_ROOT / "outputs/M8_reproduce_uploaded_golden/current_supported_config/_raw_generation",
        m8_report=REPO_ROOT / "docs/M8_reproduce_uploaded_golden_report.json",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["m8_failure_recorded"] is True
    assert report["raw_gds_candidate_count"] >= 7
    assert report["missing_boundary_count_before"] == 1556
    assert report["missing_boundary_count_after"] == 0
    assert report["fixed_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["fixed_top_cell"] == "sram_8x64_wpr4_fd45"
    assert report["reference_vs_m8_geometry_match"] == "STRUCTURAL_MATCH_WITH_GEOMETRY_DELTA"
    assert report["reference_vs_m8r_geometry_match"] in {"EXACT_MATCH", "NEAR_MATCH"}
    assert report["reference_vs_m8r_geometry_match"] != "MISMATCH"
    assert report["exact_match_achieved"] is True
    assert report["near_match_achieved"] is True
    assert report["column_mux_real_check_passed"] is True
    assert report["power_rail_overlap_real_check_passed"] is True
    assert report["can_use_this_flow_for_next_netlist_translator"] is True
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    for name in [
        "m8r_reproduced_fixed.gds",
        "m8r_reproduced_fixed_clean_review.gds",
        "golden_reference_copy_for_comparison.gds",
        "m8_original_reproduced_copy.gds",
        "M8R_raw_gds_candidate_comparison.json",
        "M8R_raw_gds_candidate_comparison.md",
        "M8R_raw_gds_candidate_comparison.csv",
        "M8R_missing_geometry_delta_report.json",
        "M8R_missing_geometry_delta_report.md",
        "M8R_layer_delta_report.json",
        "M8R_layer_delta_report.md",
        "M8R_generation_output_selection_report.json",
        "M8R_generation_output_selection_report.md",
        "M8R_fixed_reproduction_report.json",
        "M8R_fixed_reproduction_report.md",
        "review_gds_manifest.json",
        "review_gds_manifest.md",
        "missing_in_m8_delta.gds",
        "extra_in_m8_delta.gds",
    ]:
        assert (out_dir / name).exists(), name
    assert out_json.exists()
    assert out_report.exists()
    for name in [
        "docs/evidence/M8R_fix_golden_geometry_delta_summary.md",
        "docs/mapping/M8R_raw_gds_candidate_comparison.csv",
        "docs/mapping/M8R_layer_delta_matrix.csv",
        "docs/mapping/M8R_missing_geometry_classification.csv",
        "docs/mapping/M8R_remaining_gap_matrix.csv",
    ]:
        assert (REPO_ROOT / name).exists(), name
    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M8R"
    assert status["next_stage"] == "WAIT_HUMAN_KLAYOUT_REVIEW"
    assert status["m8_failure_recorded"] is True
    print("M8R_fix_golden_geometry_delta_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
