from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M7_correct_golden_reference import run_m7_correct_golden_reference  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config"
    out_json = REPO_ROOT / "docs/M7_correct_golden_reference_report.json"
    out_report = REPO_ROOT / "docs/M7_correct_golden_reference_report.md"
    report = run_m7_correct_golden_reference(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        zip_path=REPO_ROOT / "external_references/full_layout_collection.zip",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["uploaded_zip_found"] is True
    assert report["zip_extracted"] is True
    assert report["gds_candidate_count"] >= 1
    assert report["golden_reference_selected"] is True
    assert report["golden_reference_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["hybrid_openyield_rail_overlap_is_golden"] is False
    assert report["new_uploaded_reference_is_golden"] is True
    assert report["old_reference_comparison_available"] is True
    assert report["next_repair_target_defined"] is True
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    assert (out_dir / "golden_reference.gds").exists()
    assert (out_dir / "golden_reference_clean_review.gds").exists()
    assert (out_dir / "M7_correct_golden_reference_selection_report.json").exists()
    assert (out_dir / "M7_compare_old_references_report.json").exists()
    assert (REPO_ROOT / "docs/mapping/M7_zip_inventory.csv").exists()
    assert (REPO_ROOT / "docs/mapping/M7_gds_candidate_inventory.csv").exists()
    assert (REPO_ROOT / "docs/mapping/M7_old_vs_new_reference_comparison.csv").exists()
    assert (REPO_ROOT / "docs/mapping/M7_next_repair_target_matrix.csv").exists()
    print("M7_correct_golden_reference_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
