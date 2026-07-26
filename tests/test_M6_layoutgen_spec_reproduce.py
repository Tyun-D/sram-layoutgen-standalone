from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M6_layoutgen_spec_reproduce import run_m6_layoutgen_spec_reproduce  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M6_layoutgen_spec_reproduce/current_supported_config"
    out_json = REPO_ROOT / "docs/M6_layoutgen_spec_reproduce_report.json"
    out_report = REPO_ROOT / "docs/M6_layoutgen_spec_reproduce_report.md"
    report = run_m6_layoutgen_spec_reproduce(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["locked_spec_available"] is True
    assert report["top_cell_name"] == "layoutgen_optimized_reproduced_sram"
    assert report["gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["power_rail_overlap_restored"] is True
    assert report["column_mux_present"] is True
    assert report["reference_comparison_match"] is True
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    assert report["remaining_M6_blockers_count"] == 0
    assert (out_dir / "layoutgen_optimized_reproduced_sram.gds").exists()
    assert (out_dir / "layoutgen_optimized_reproduced_sram_clean_review.gds").exists()
    assert (out_dir / "layoutgen_optimized_reproduced_sram_spec_annotated.gds").exists()
    assert (out_dir / "SRAM_SPEC.json").exists()
    assert (out_dir / "M6_power_rail_overlap_report.json").exists()
    assert (REPO_ROOT / "docs/mapping/M6_generation_parameter_matrix.csv").exists()
    assert (REPO_ROOT / "docs/mapping/M6_reference_comparison_matrix.csv").exists()
    print("M6_layoutgen_spec_reproduce_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
