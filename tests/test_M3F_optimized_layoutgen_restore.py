from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M3F_optimized_layoutgen_restore import run_m3f_optimized_layoutgen_restore  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M3F_optimized_layoutgen_restore/current_supported_config"
    out_json = REPO_ROOT / "docs/M3F_optimized_layoutgen_restore_report.json"
    out_report = REPO_ROOT / "docs/M3F_optimized_layoutgen_restore_report.md"
    report = run_m3f_optimized_layoutgen_restore(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        m2r_dir=REPO_ROOT / "outputs/M2R_full_sram_regen/current_supported_config",
        m3r_dir=REPO_ROOT / "outputs/M3R_openyield_semantic_bound/current_supported_config",
        openyield_intent_dir=REPO_ROOT / "outputs/openyield_layout_intent/current_supported_config",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["m3r_review_failure_recorded"] is True
    assert report["optimized_layoutgen_flow_found"] is True
    assert report["optimized_layoutgen_reference_gds_found"] is True
    assert report["optimized_layoutgen_code_found"] is True
    assert report["optimized_power_rail_stitch_flow_used"] is True
    assert report["baseline_only_layoutgen_flow_used"] is False
    assert report["full_sram_review_gds_generated"] is True
    assert report["top_cell_name"] == "openyield_optimized_layoutgen_sram"
    assert report["gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["bitcell_array_is_dense_body"] is True
    assert report["access_module_as_primary_count"] == 0
    assert report["floorplan_proxy_count"] == 0
    assert report["large_region_overlay_as_primary_count"] == 0
    assert report["power_rail_stitch_restored"] is True
    assert report["rail_overlap_or_abutment_evidence_count"] > 0
    assert report["module_power_rail_connected_count"] == 20
    assert report["openyield_semantic_binding_present"] is True
    assert report["openyield_label_only_binding_count"] == 0
    assert report["openyield_physical_binding_count"] == 20
    assert report["remaining_M3F_blockers_count"] == 0
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    assert Path(report["full_sram_review_gds_path"]).exists()
    print("M3F_optimized_layoutgen_restore_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
