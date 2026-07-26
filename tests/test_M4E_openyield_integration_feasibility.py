from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M4E_openyield_integration_feasibility import (  # noqa: E402
    run_m4e_openyield_integration_feasibility,
)


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M4E_openyield_integration_eval/current_supported_config"
    out_json = REPO_ROOT / "docs/M4E_openyield_integration_feasibility_report.json"
    out_report = REPO_ROOT / "docs/M4E_openyield_integration_feasibility_report.md"
    report = run_m4e_openyield_integration_feasibility(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        m3f_dir=REPO_ROOT / "outputs/M3F_optimized_layoutgen_restore/current_supported_config",
        m3f_report=REPO_ROOT / "docs/M3F_optimized_layoutgen_restore_report.json",
        openyield_intent_dir=REPO_ROOT / "outputs/openyield_layout_intent/current_supported_config",
        openyield_module_gds_dir=REPO_ROOT / "outputs/openyield_module_gds",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["m3f_review_recorded"] is True
    assert report["evaluation_only_once_enforced"] is True
    assert report["no_more_evaluation_allowed_after_M4E"] is True
    assert report["review_gds_generated"] is True
    assert report["review_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["openyield_module_count"] == 20
    assert report["layoutgen_baseline_module_count"] == 16
    assert report["module_type_mismatch_count"] == 12
    assert report["net_mapping_count"] == 34
    assert report["net_mapping_gap_count"] == 0
    assert report["direct_generator_binding_count"] == 3
    assert report["parameterized_generator_binding_count"] == 6
    assert report["real_cell_wrapper_count"] == 5
    assert report["layoutgen_fallback_with_openyield_semantics_count"] == 6
    assert report["not_implementable_now_count"] == 0
    assert report["floorplan_change_required"] is True
    assert report["placement_change_required"] is True
    assert report["routing_change_required"] is True
    assert report["power_change_required"] is True
    assert report["go_nogo_decision"] == "PARTIAL_GO_WITH_DEFINED_SCOPE"
    assert report["allowed_next_stage"] == "M5_IMPLEMENT_OPENYIELD_LAYOUTGEN_INTEGRATION"
    assert report["remaining_M4E_blockers_count"] == 0
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    assert Path(report["review_gds_path"]).exists()
    assert (out_dir / "M4E_openyield_integration_feasibility_report.json").exists()
    assert (out_dir / "M4E_openyield_integration_feasibility_report.md").exists()
    assert (out_dir / "M4E_openyield_to_layoutgen_implementation_binding.csv").exists()
    assert (out_dir / "M4E_floorplan_modification_plan.csv").exists()
    assert (out_dir / "M4E_placement_modification_plan.csv").exists()
    assert (out_dir / "M4E_routing_modification_plan.csv").exists()
    assert (out_dir / "M4E_power_modification_plan.csv").exists()
    assert (out_dir / "M4E_direct_implementation_plan.md").exists()
    assert (out_dir / "M4E_no_more_evaluation_statement.md").exists()
    print("M4E_openyield_integration_feasibility_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
