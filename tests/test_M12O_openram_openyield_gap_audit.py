from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M12O_openram_openyield_gap_audit import (  # noqa: E402
    RECOMMENDED_NEXT_STAGE,
    run_m12o_openram_openyield_gap_audit,
)


def main() -> int:
    report = run_m12o_openram_openyield_gap_audit(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        goal_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m11v_report=REPO_ROOT / "docs/M11V_routing_power_connectivity_verification_report.json",
        openram_root=Path("/data1/qujh/OpenRAM"),
        openyield_root=Path("/data1/qujh/work/external/OpenYield"),
        openram_reference_dir=REPO_ROOT / "external_references/openram_full_reference",
        layoutgen_golden=REPO_ROOT / "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds",
        sense_amp_smoke_gds=REPO_ROOT / "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_sense_amp_substituted_sram.gds",
        wordline_driver_smoke_gds=REPO_ROOT / "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_wordline_driver_substituted_sram.gds",
        out_dir=REPO_ROOT / "outputs/M12O_openram_openyield_gap_audit/current_supported_config",
        out_json=REPO_ROOT / "docs/M12O_openram_openyield_gap_audit_report.json",
        out_report=REPO_ROOT / "docs/M12O_openram_openyield_gap_audit_report.md",
    )

    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["goal_file_read"] is True
    assert report["goal_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m11v_report_loaded"] is True
    assert report["m11v_recommended_next_stage_before_M12O"] == "M11V2_DEEPER_CONNECTIVITY_EXTRACTION"
    assert report["openram_root_found"] is True
    assert report["openram_file_scan_completed"] is True
    assert report["openram_reference_gds_found"] is True
    assert report["openram_reference_gds_parsed"] is True
    assert report["openram_reference_top_cell"] == "sram_1rw_32x16_freepdk45"
    assert report["openyield_root_found"] is True
    assert report["openyield_file_scan_completed"] is True
    assert report["openyield_netlist_candidate_count"] > 0
    assert report["openyield_config_candidate_count"] > 0
    assert report["openyield_entrypoint_candidate_count"] >= 3
    assert report["openyield_single_authoritative_netlist_proven"] is False
    assert report["openyield_complete_sram_netlist_found"] is False
    assert report["openyield_control_logic_source_found"] is True
    assert report["openyield_parameterization_supported"] is True
    assert report["layoutgen_golden_loaded"] is True
    assert report["layoutgen_golden_parsed"] is True
    assert report["three_way_gap_matrix_generated"] is True
    assert report["module_gap_count"] > 0
    assert report["control_logic_gap_status"] == "OPENRAM_PRESENT_LAYOUTGEN_MISSING_OPENYIELD_PHYSICAL_UNQUALIFIED"
    assert report["layoutgen_missing_control_logic"] is True
    assert report["openyield_control_logic_physical_ready"] is False
    assert report["configurable_sram_spec_template_generated"] is True
    assert report["parameterization_blockers_count"] >= 4
    assert report["external_dependency_blockers_count"] >= 6
    assert report["can_claim_custom_netlist_driven_layout_generation"] is False
    assert report["can_claim_openyield_authoritative_netlist_locked"] is False
    assert report["can_claim_full_openyield_module_gds_hardmacro_substitution"] is False
    assert report["can_claim_drc_clean"] is False
    assert report["can_claim_lvs_clean"] is False
    assert report["can_claim_signoff_ready"] is False
    assert report["review_gds_generated"] is True
    assert report["review_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["recommended_next_stage"] == RECOMMENDED_NEXT_STAGE
    assert report["remaining_M12O_blockers_count"] >= 4
    assert report["human_klayout_review_required"] is False
    assert report["can_enter_next_stage_before_human_review"] is True

    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M12O"
    assert status["next_stage"] == RECOMMENDED_NEXT_STAGE
    assert status["next_stage_allowed"] == RECOMMENDED_NEXT_STAGE
    assert status["can_claim_custom_netlist_driven_layout_generation"] is False

    goal_text = (REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_GOAL.md").read_text(encoding="utf-8")
    assert "## Current OpenRAM / OpenYield Alignment Stage" in goal_text
    assert RECOMMENDED_NEXT_STAGE in goal_text

    progress_text = (REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md").read_text(encoding="utf-8")
    assert "## M12O OpenRAM OpenYield Gap Audit" in progress_text
    assert RECOMMENDED_NEXT_STAGE in progress_text

    required_paths = [
        "docs/M12O_openram_openyield_gap_audit_report.json",
        "docs/M12O_openram_openyield_gap_audit_report.md",
        "docs/evidence/M12O_openram_openyield_gap_audit_summary.md",
        "docs/mapping/M12O_openram_reference_inventory.csv",
        "docs/mapping/M12O_openyield_netlist_authority_inventory.csv",
        "docs/mapping/M12O_three_way_module_gap_matrix.csv",
        "docs/mapping/M12O_configurable_sram_spec_plan.csv",
        "docs/mapping/M12O_next_route_decision.csv",
        "docs/mapping/M12O_external_dependency_blockers.csv",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_openram_reference_inventory.csv",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_openyield_netlist_authority_inventory.csv",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_three_way_module_gap_matrix.csv",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_configurable_sram_spec_plan.json",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/SRAM_SPEC_TEMPLATE.json",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_external_dependency_blockers.md",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_next_route_decision.json",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_machine_verification_report.json",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_human_review_required_items.md",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_openram_vs_layoutgen_gap_review.gds",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_openram_vs_layoutgen_gap_clean_review.gds",
        "outputs/M12O_openram_openyield_gap_audit/current_supported_config/M12O_openram_vs_layoutgen_gap_annotated_debug.gds",
    ]
    for rel in required_paths:
        assert (REPO_ROOT / rel).exists(), rel
    print("M12O_openram_openyield_gap_audit_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
