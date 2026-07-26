from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M12C_control_logic_gap_definition import EXPECTED_SHA, run_m12c  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M12C_control_logic_gap_definition/current_supported_config"
    out_json = REPO_ROOT / "docs/M12C_control_logic_gap_definition_report.json"
    out_report = REPO_ROOT / "docs/M12C_control_logic_gap_definition_report.md"
    report = run_m12c(
        repo_root=REPO_ROOT,
        openyield_root=Path("/data1/qujh/work/external/OpenYield"),
        openram_root=Path("/data1/qujh/OpenRAM"),
        openram_reference_dir=REPO_ROOT / "external_references/openram_full_reference",
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        goal_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m12n2r_report=REPO_ROOT / "docs/M12N2R_correct_time_role_report.json",
        m12n2_clean_report=REPO_ROOT / "docs/M12N2_clean_openyield_sram_top_report.json",
        clean_top_graph=REPO_ROOT / "outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_graph.json",
        layoutgen_golden=REPO_ROOT / "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds",
        openyield_module_gds_dir=REPO_ROOT / "outputs/openyield_module_gds",
        m12o_gap_matrix=REPO_ROOT / "docs/mapping/M12O_three_way_module_gap_matrix.csv",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["goal_file_read"] is True
    assert report["goal_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m12n2r_report_loaded"] is True
    assert report["m12n2r_gate_passed"] is True
    assert report["can_enter_M12C_from_M12N2R"] is True
    assert report["openyield_version_verified"] is True
    assert report["openyield_sha"] == EXPECTED_SHA
    assert report["time_hierarchy_extracted"] is True
    assert report["time_module_count"] > 0
    assert report["time_primitive_count"] > 0
    assert report["read_topology_generated"] is True
    assert report["write_topology_generated"] is True
    assert report["read_write_topology_generated"] is True
    assert report["operation_topology_diff_generated"] is True
    assert report["operation_topology_status"] == "READ_WRITE_SUPERSET_CANONICAL"
    assert report["canonical_physical_operation_topology"] == "READ_WRITE_SUPERSET"
    assert report["canonical_operation_topology_locked"] is True
    assert report["operation_topology_requires_team_confirmation"] is False
    assert report["physical_mapping_matrix_generated"] is True
    assert report["physical_module_total_count"] > 0
    assert report["physical_ready_for_qualification_count"] > 0
    assert report["physical_partial_count"] > 0
    assert report["physical_reference_only_count"] > 0
    assert report["parameterized_transistor_layout_required_count"] > 0
    assert report["existing_openyield_control_primitive_gds_count"] > 0
    assert report["existing_layoutgen_control_cell_count"] > 0
    assert report["openram_control_reference_region_found"] is True
    assert report["floorplan_interface_plan_generated"] is True
    assert report["candidate_control_region_defined"] is True
    assert report["review_gds_generated"] is True
    assert report["review_gds_parsed"] is True
    assert report["can_claim_control_logic_source_locked"] is True
    assert report["can_claim_control_logic_physical_ready"] is False
    assert report["can_claim_custom_netlist_driven_layout_generation"] is False
    assert report["can_claim_routing_clean"] is False
    assert report["can_claim_power_clean"] is False
    assert report["can_claim_drc_clean"] is False
    assert report["can_claim_lvs_clean"] is False
    assert report["can_claim_signoff_ready"] is False
    assert report["recommended_next_stage"] == "M12C2_CONTROL_LOGIC_PHYSICAL_LIBRARY_QUALIFICATION"
    assert report["recommended_next_stage_reason"]
    assert report["human_review_required"] is False
    assert report["can_enter_next_stage_before_human_review"] is True
    for name in [
        "M12C_time_hierarchy_inventory.csv",
        "M12C_time_hierarchy_inventory.md",
        "M12C_operation_topology_read.json",
        "M12C_operation_topology_write.json",
        "M12C_operation_topology_read_write.json",
        "M12C_operation_topology_diff.csv",
        "M12C_operation_topology_diff.md",
        "M12C_control_logic_physical_mapping_matrix.csv",
        "M12C_control_logic_physical_mapping_matrix.md",
        "M12C_control_logic_parameter_physical_impact.csv",
        "M12C_control_logic_parameter_physical_impact.md",
        "M12C_control_logic_floorplan_interface_plan.json",
        "M12C_control_logic_floorplan_interface_plan.md",
        "M12C_control_logic_interface_nets.csv",
        "M12C_control_logic_gap_review.gds",
        "M12C_control_logic_gap_clean_review.gds",
        "M12C_control_logic_gap_annotated_debug.gds",
        "M12C_external_dependency_blockers.csv",
        "M12C_external_dependency_blockers.md",
        "M12C_machine_verification_report.json",
        "M12C_machine_verification_report.md",
        "M12C_human_review_required_items.md",
        "M12C_next_stage_decision.json",
        "M12C_next_stage_decision.md",
    ]:
        assert (out_dir / name).exists(), name
    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M12C"
    assert status["next_stage"] == "M12C2_CONTROL_LOGIC_PHYSICAL_LIBRARY_QUALIFICATION"
    print("M12C_control_logic_gap_definition_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
