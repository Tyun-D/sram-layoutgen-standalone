from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M6R_reference_locked_reproduce import run_m6r_reference_locked_reproduce  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M6R_reference_locked_reproduce/current_supported_config"
    out_json = REPO_ROOT / "docs/M6R_reference_locked_reproduce_report.json"
    out_report = REPO_ROOT / "docs/M6R_reference_locked_reproduce_report.md"
    report = run_m6r_reference_locked_reproduce(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["true_generation_entry_identified"] is True
    assert report["m6_previous_matches_reference"] is False
    assert report["reproduced_matches_reference"] is True
    assert report["byte_identical_reference_vs_reproduced_complete"] is True
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    assert (out_dir / "reference_copy_for_review.gds").exists()
    assert (out_dir / "m6_previous_output_for_review.gds").exists()
    assert (out_dir / "layoutgen_hybrid_reproduced_M6R.gds").exists()
    assert (out_dir / "layoutgen_hybrid_reproduced_M6R_clean_review.gds").exists()
    assert (out_dir / "M6R_reference_geometry_diff_report.json").exists()
    assert (out_dir / "M6R_true_generation_entry_report.json").exists()
    assert (out_dir / "M6R_power_rail_overlap_real_check.json").exists()
    assert (out_dir / "M6R_column_mux_real_check.json").exists()
    assert (out_dir / "M6R_failure_reason_report.md").exists()
    print("M6R_reference_locked_reproduce_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
