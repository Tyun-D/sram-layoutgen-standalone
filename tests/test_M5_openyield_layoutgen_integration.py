from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M5_openyield_layoutgen_integration import (  # noqa: E402
    run_m5_openyield_layoutgen_integration,
)


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M5_openyield_layoutgen_integration/current_supported_config"
    out_json = REPO_ROOT / "docs/M5_openyield_layoutgen_integration_report.json"
    out_report = REPO_ROOT / "docs/M5_openyield_layoutgen_integration_report.md"
    report = run_m5_openyield_layoutgen_integration(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        m3f_dir=REPO_ROOT / "outputs/M3F_optimized_layoutgen_restore/current_supported_config",
        m4e_dir=REPO_ROOT / "outputs/M4E_openyield_integration_eval/current_supported_config",
        m4e_report=REPO_ROOT / "docs/M4E_openyield_integration_feasibility_report.json",
        m4e_binding=REPO_ROOT / "docs/mapping/M4E_openyield_to_layoutgen_implementation_binding.csv",
        m4e_code_matrix=REPO_ROOT / "docs/mapping/M4E_code_modification_matrix.csv",
        openyield_intent_dir=REPO_ROOT / "outputs/openyield_layout_intent/current_supported_config",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["m4e_decision_loaded"] is True
    assert report["no_more_evaluation_performed"] is True
    assert report["integrated_gds_generated"] is True
    assert report["top_cell_name"] == "openyield_layoutgen_integrated_sram"
    assert report["gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["optimized_layoutgen_flow_preserved"] is True
    assert report["optimized_power_rail_stitch_preserved"] is True
    assert report["arbitrary_module_scatter_used"] is False
    assert report["openyield_module_count"] == 20
    assert report["openyield_modules_implemented_count"] == 20
    assert report["openyield_modules_unimplemented_count"] == 0
    assert report["direct_generator_binding_implemented_count"] == 3
    assert report["parameterized_generator_binding_implemented_count"] == 6
    assert report["real_cell_wrapper_implemented_count"] == 5
    assert report["layoutgen_fallback_with_openyield_semantics_implemented_count"] == 6
    assert report["not_implementable_now_count"] == 0
    assert report["openyield_net_count"] == 34
    assert report["openyield_nets_implemented_count"] == 34
    assert report["openyield_nets_unimplemented_count"] == 0
    assert report["floorplan_code_modified"] is True
    assert report["placement_code_modified"] is True
    assert report["routing_code_modified"] is True
    assert report["power_code_modified"] is True
    assert report["module_power_rail_connected_count"] >= 20
    assert report["rail_overlap_or_abutment_evidence_count"] >= 15
    assert report["access_module_as_primary_count"] == 0
    assert report["floorplan_proxy_count"] == 0
    assert report["label_only_binding_as_implementation_count"] == 0
    assert report["temporary_empty_wrapper_count"] == 0
    assert report["large_region_overlay_as_primary_count"] == 0
    assert report["remaining_M5_blockers_count"] == 0
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    assert Path(report["integrated_gds_path"]).exists()
    assert (out_dir / "M5_implementation_report.json").exists()
    assert (out_dir / "M5_module_integration_report.json").exists()
    assert (out_dir / "M5_floorplan_placement_update_report.json").exists()
    assert (out_dir / "M5_routing_update_report.json").exists()
    assert (out_dir / "M5_power_update_report.json").exists()
    assert (out_dir / "M5_openyield_net_binding_implementation_report.json").exists()
    assert (out_dir / "M5_remaining_gap_report.json").exists()
    print("M5_openyield_layoutgen_integration_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
