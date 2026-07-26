from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.control_candidate_gds_inventory import scan_candidate_gds  # noqa: E402


def main() -> int:
    report = json.loads((REPO_ROOT / "docs/M12C2_control_logic_physical_library_qualification_report.json").read_text(encoding="utf-8"))
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["goal_file_read"] is True
    assert report["goal_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m12c_report_loaded"] is True
    assert report["m12c_gate_passed"] is True
    assert report["can_enter_M12C2_from_M12C"] is True
    assert report["openyield_version_verified"] is True
    assert report["device_model_reclassification_completed"] is True
    assert report["device_model_reference_count"] == 2
    assert report["device_models_removed_from_missing_hardmacro_count"] == 2
    assert report["candidate_gds_scan_completed"] is True
    assert report["candidate_gds_file_count"] == 20
    assert report["candidate_gds_cell_count"] >= 20
    assert report["logical_alias_variant_analysis_completed"] is True
    assert report["size_alias_collision_count"] >= 4
    assert report["qualification_matrix_generated"] is True
    assert report["qualified_manifest_generated"] is True
    assert report["review_gds_generated"] is True
    assert report["review_gds_parsed"] is True
    assert report["time_candidate_qualification_status"] == "CONNECTIVITY_UNPROVEN"
    assert report["transmission_gate_qualification_status"] == "MISSING_REQUIRES_GENERATOR"
    assert report["dff_qualification_status"] == "QUALIFIED_REFERENCE_ONLY"
    assert report["delay_chain_qualification_status"] == "QUALIFIED_FIXED_VARIANT_ONLY"
    assert report["can_claim_control_logic_physical_ready"] is False
    assert report["can_claim_custom_netlist_driven_layout_generation"] is False
    assert report["can_claim_drc_clean"] is False
    assert report["can_claim_lvs_clean"] is False
    assert report["can_claim_signoff_ready"] is False
    assert report["recommended_next_stage"] in {
        "M12C2H_CONTROL_LIBRARY_VISUAL_REVIEW",
        "M12C2R_REPAIR_CANDIDATE_LIBRARY_METADATA_OR_GENERATION",
        "M12C3_CONTROL_LOGIC_PRIMITIVE_LAYOUT_GENERATOR_PLAN",
        "M12F_CONTROL_LOGIC_FLOORPLAN_PROTOTYPE_PLAN",
    }
    assert report["recommended_next_stage"] == "M12C3_CONTROL_LOGIC_PRIMITIVE_LAYOUT_GENERATOR_PLAN"
    assert report["human_review_required"] is False
    assert report["can_enter_next_stage_before_human_review"] is True
    for rel in [
        "outputs/M12C2_control_logic_physical_library_qualification/current_supported_config/M12C2_device_model_reclassification.csv",
        "outputs/M12C2_control_logic_physical_library_qualification/current_supported_config/M12C2_logical_alias_physical_variant_matrix.csv",
        "outputs/M12C2_control_logic_physical_library_qualification/current_supported_config/M12C2_candidate_gds_inventory.csv",
        "outputs/M12C2_control_logic_physical_library_qualification/current_supported_config/M12C2_candidate_cell_hierarchy.csv",
        "outputs/M12C2_control_logic_physical_library_qualification/current_supported_config/M12C2_control_physical_qualification_matrix.csv",
        "outputs/M12C2_control_logic_physical_library_qualification/current_supported_config/M12C2_qualified_control_physical_library_manifest.json",
        "outputs/M12C2_control_logic_physical_library_qualification/current_supported_config/M12C2_candidate_cell_drc_report.json",
        "outputs/M12C2_control_logic_physical_library_qualification/current_supported_config/M12C2_control_library_qualification_atlas.gds",
        "outputs/M12C2_control_logic_physical_library_qualification/current_supported_config/M12C2_control_library_qualification_clean.gds",
        "outputs/M12C2_control_logic_physical_library_qualification/current_supported_config/M12C2_control_library_qualification_annotated.gds",
        "docs/M12C2_control_logic_physical_library_qualification_report.json",
        "docs/M12C2_control_logic_physical_library_qualification_report.md",
        "docs/evidence/M12C2_control_logic_physical_library_qualification_summary.md",
        "docs/mapping/M12C2_control_physical_qualification_matrix.csv",
        "docs/mapping/M12C2_quarantined_candidates.csv",
    ]:
        assert (REPO_ROOT / rel).exists(), rel
    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M12C2"
    assert status["next_stage"] == "M12C3_CONTROL_LOGIC_PRIMITIVE_LAYOUT_GENERATOR_PLAN"
    assert status["can_claim_control_logic_physical_ready"] is False
    inventory = scan_candidate_gds(REPO_ROOT / "outputs/openyield_module_gds")
    assert inventory["candidate_gds_file_count"] == 20
    print("M12C2_control_logic_physical_library_qualification_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
