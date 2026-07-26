from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    report = json.loads((REPO_ROOT / "docs/M12C3_control_logic_primitive_layout_generator_plan_report.json").read_text(encoding="utf-8"))
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["goal_file_read"] is True
    assert report["goal_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m12c2_report_loaded"] is True
    assert report["m12c2_gate_passed"] is True
    assert report["can_enter_M12C3_from_M12C2"] is True
    assert report["qualification_audit_complete"] is True
    assert report["control_physical_library_reuse_ready"] is False
    assert report["raw_candidate_drc_marker_count"] == 6661
    assert report["duplicate_drc_artifact_detected"] is True
    assert report["unique_candidate_drc_marker_count"] == 3422
    assert report["existing_generator_scan_completed"] is True
    assert report["trusted_device_generator_found"] is True
    assert report["trusted_gate_generator_found"] is True
    assert report["contact_via_generator_found"] is True
    assert report["well_implant_generation_supported"] is True
    assert report["parameterized_width_supported"] is True
    assert report["parameterized_length_supported"] is False
    assert report["physical_tech_contract_generated"] is True
    assert report["physical_tech_contract_status"] == "LOCKED_FREEPDK45_V1"
    assert report["primitive_requirement_matrix_generated"] is True
    assert report["generator_architecture_decision"] == "OPENRAM_FREEPDK45_DEVICE_CONTACT_ADAPTER"
    assert report["primitive_smoke_generation_allowed"] is False
    assert report["primitive_smoke_generation_attempted"] is False
    assert report["primitive_smoke_drc_run"] is False
    assert report["can_claim_control_physical_library_qualification_audit_complete"] is True
    assert report["can_claim_control_physical_library_reuse_ready"] is False
    assert report["can_claim_parameterized_primitive_generator_implemented"] is False
    assert report["can_claim_primitive_smoke_drc_clean"] is False
    assert report["can_claim_control_logic_physical_ready"] is False
    assert report["can_claim_custom_netlist_driven_layout_generation"] is False
    assert report["can_claim_lvs_clean"] is False
    assert report["can_claim_signoff_ready"] is False
    assert report["recommended_next_stage"] == "M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR"
    assert report["human_review_required"] is False
    assert report["can_enter_next_stage_before_human_review"] is True
    for rel in [
        "outputs/M12C3_control_logic_primitive_layout_generator_plan/current_supported_config/M12C3_existing_layout_generator_inventory.csv",
        "outputs/M12C3_control_logic_primitive_layout_generator_plan/current_supported_config/M12C3_openram_generator_capability_report.json",
        "outputs/M12C3_control_logic_primitive_layout_generator_plan/current_supported_config/M12C3_freepdk45_physical_tech_contract.json",
        "outputs/M12C3_control_logic_primitive_layout_generator_plan/current_supported_config/M12C3_freepdk45_layer_map.csv",
        "outputs/M12C3_control_logic_primitive_layout_generator_plan/current_supported_config/M12C3_primitive_generator_requirement_matrix.csv",
        "outputs/M12C3_control_logic_primitive_layout_generator_plan/current_supported_config/M12C3_parameterized_cell_naming_contract.json",
        "outputs/M12C3_control_logic_primitive_layout_generator_plan/current_supported_config/M12C3_generator_architecture_decision.json",
        "outputs/M12C3_control_logic_primitive_layout_generator_plan/current_supported_config/M12C3_candidate_drc_deduplication_report.json",
        "outputs/M12C3_control_logic_primitive_layout_generator_plan/current_supported_config/M12C3_primitive_smoke_generation_report.json",
        "outputs/M12C3_control_logic_primitive_layout_generator_plan/current_supported_config/M12C3_external_dependency_blockers.csv",
        "docs/M12C3_control_logic_primitive_layout_generator_plan_report.json",
        "docs/evidence/M12C3_control_logic_primitive_layout_generator_plan_summary.md",
        "docs/mapping/M12C3_existing_layout_generator_inventory.csv",
        "docs/mapping/M12C3_next_stage_decision.csv",
    ]:
        assert (REPO_ROOT / rel).exists(), rel
    original_contract = json.loads((REPO_ROOT / "outputs/M12C3_control_logic_primitive_layout_generator_plan/current_supported_config/M12C3_parameterized_cell_naming_contract.json").read_text(encoding="utf-8"))
    assert any("NW0" in row["canonical_cell_name"] or "PW0" in row["canonical_cell_name"] or "L0" in row["canonical_cell_name"] for row in original_contract["examples"])
    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] in {"M12C3", "M12C3R"}
    assert status["next_stage"] in {
        "M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR",
        "M12C3R2_RESOLVE_SOURCE_VARIANT_AMBIGUITY",
        "M12C3R3_OPENRAM_ADAPTER_BOOTSTRAP_FIX",
        "M12C3T_FREEPDK45_TECH_CONTRACT_COMPLETION",
    }
    print("M12C3_control_logic_primitive_layout_generator_plan_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
