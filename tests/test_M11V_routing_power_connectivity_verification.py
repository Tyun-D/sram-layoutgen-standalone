from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M11V_routing_power_connectivity_verification import (  # noqa: E402
    RECOMMENDED_NEXT_STAGE,
    run_m11v_routing_power_connectivity_verification,
)


def main() -> int:
    report = run_m11v_routing_power_connectivity_verification(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m11c2h_report=REPO_ROOT / "docs/M11C2H_confirm_wordline_driver_human_review_report.json",
        m11c2h_gate=REPO_ROOT / "docs/mapping/M11C2H_M11V_entry_gate.csv",
        m11c2h_caveat=REPO_ROOT / "docs/mapping/M11C2H_routing_power_caveat.csv",
        m11c_report=REPO_ROOT / "docs/M11C_sense_amp_smoke_substitution_report.json",
        m11c2_report=REPO_ROOT / "docs/M11C2_wordline_driver_smoke_substitution_report.json",
        baseline_gds=REPO_ROOT / "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds",
        m11c_gds=REPO_ROOT / "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_sense_amp_substituted_sram.gds",
        m11c2_gds=REPO_ROOT / "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_wordline_driver_substituted_sram.gds",
        out_dir=REPO_ROOT / "outputs/M11V_routing_power_connectivity_verification/current_supported_config",
        out_json=REPO_ROOT / "docs/M11V_routing_power_connectivity_verification_report.json",
        out_report=REPO_ROOT / "docs/M11V_routing_power_connectivity_verification_report.md",
    )

    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m11c2h_gate_loaded"] is True
    assert report["can_enter_M11V_from_M11C2H"] is True
    assert report["baseline_gds_parsed"] is True
    assert report["m11c_sense_amp_gds_parsed"] is True
    assert report["m11c2_wordline_driver_gds_parsed"] is True
    assert report["top_bbox_match_status"] == "EXACT_MATCH"
    assert report["baseline_power_risk_level"] == "MEDIUM_BASELINE_LIMITED"
    assert report["baseline_routing_risk_level"] == "HIGH_BASELINE_LIMITED"
    assert report["baseline_not_routing_power_clean_proven"] is True
    assert report["sense_amp_incremental_power_risk"] == "NO_NEW_POWER_RISK_DETECTED"
    assert report["sense_amp_incremental_routing_risk"] == "NO_NEW_ROUTING_RISK_DETECTED"
    assert report["sense_amp_incremental_risk_level"] == "LOW_INCREMENTAL_RISK"
    assert report["wordline_driver_incremental_power_risk"] == "NO_NEW_POWER_RISK_DETECTED"
    assert report["wordline_driver_incremental_routing_risk"] == "NO_NEW_ROUTING_RISK_DETECTED_WITH_BASELINE_LIMITATION"
    assert report["wordline_driver_incremental_risk_level"] == "LOW_INCREMENTAL_RISK"
    assert report["sense_amp_connectivity_heuristic_status"] == "PASS"
    assert report["wordline_driver_connectivity_heuristic_status"] == "INCONCLUSIVE_BASELINE_LIMITED"
    assert report["new_power_risk_introduced_by_sense_amp"] is False
    assert report["new_routing_risk_introduced_by_sense_amp"] is False
    assert report["new_power_risk_introduced_by_wordline_driver"] is False
    assert report["new_routing_risk_introduced_by_wordline_driver"] is False
    assert report["unexpected_non_target_change_count_m11c"] == 0
    assert report["unexpected_non_target_change_count_m11c2"] == 0
    assert report["access_module_used"] is False
    assert report["floorplan_proxy_used"] is False
    assert report["arbitrary_scatter_used"] is False
    assert report["unauthorized_module_substitution_detected"] is False
    assert report["drc_feasibility_run"] is True
    assert report["drc_marker_count_compared"] in (True, False)
    if report["drc_marker_count_compared"] is True:
        drc_report = json.loads(
            (
                REPO_ROOT
                / "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_drc_feasibility_report.json"
            ).read_text(encoding="utf-8")
        )
        assert len(drc_report["runs"]) == 3
        assert all(run["returncode"] == 0 for run in drc_report["runs"])
        assert all(run["marker_count"] is not None for run in drc_report["runs"])
    else:
        assert report["drc_feasibility_not_run_reason"]
    assert report["machine_verified_item_count"] > 20
    assert report["human_review_required_item_count"] == 0
    assert report["human_review_required_items"] == []
    assert report["verification_status"] == "INCONCLUSIVE"
    assert report["verification_risk_level"] == "MEDIUM"
    assert report["recommended_next_stage"] == RECOMMENDED_NEXT_STAGE
    assert report["can_claim_sense_amp_smoke_substitution_passed"] is True
    assert report["can_claim_wordline_driver_smoke_substitution_passed"] is True
    assert report["can_claim_openyield_module_gds_hardmacro_substitution"] is False
    assert report["can_claim_routing_clean"] is False
    assert report["can_claim_power_clean"] is False
    assert report["can_claim_drc_clean"] is False
    assert report["can_claim_lvs_clean"] is False
    assert report["can_claim_signoff_ready"] is False
    assert report["review_gds_generated"] is True
    assert report["review_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["human_klayout_review_required"] is False
    assert report["can_enter_next_stage_before_human_review"] is True

    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M11V"
    assert status["next_stage"] == RECOMMENDED_NEXT_STAGE
    assert status["next_stage_allowed"] == RECOMMENDED_NEXT_STAGE
    assert status["can_enter_next_stage_without_human_review"] is True
    assert status["human_klayout_review_required"] is False
    assert status["can_enter_next_stage_before_human_review"] is True

    progress_text = (REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md").read_text(encoding="utf-8")
    assert "## M11V Routing Power Connectivity Verification" in progress_text
    assert RECOMMENDED_NEXT_STAGE in progress_text

    required_paths = [
        "docs/M11V_routing_power_connectivity_verification_report.json",
        "docs/M11V_routing_power_connectivity_verification_report.md",
        "docs/evidence/M11V_routing_power_connectivity_verification_summary.md",
        "docs/mapping/M11V_baseline_vs_substitution_risk_matrix.csv",
        "docs/mapping/M11V_power_rail_heuristic_matrix.csv",
        "docs/mapping/M11V_connectivity_heuristic_matrix.csv",
        "docs/mapping/M11V_drc_feasibility_matrix.csv",
        "docs/mapping/M11V_next_stage_decision.csv",
        "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_routing_power_connectivity_report.json",
        "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_baseline_risk_report.json",
        "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_sense_amp_incremental_risk_report.json",
        "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_wordline_driver_incremental_risk_report.json",
        "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_power_rail_heuristic_report.json",
        "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_connectivity_heuristic_report.json",
        "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_drc_feasibility_report.json",
        "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_next_stage_decision.json",
        "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_machine_verification_report.json",
        "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_human_review_required_items.md",
        "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_routing_power_connectivity_review.gds",
        "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_routing_power_connectivity_clean_review.gds",
        "outputs/M11V_routing_power_connectivity_verification/current_supported_config/M11V_routing_power_connectivity_annotated_debug.gds",
    ]
    for rel in required_paths:
        assert (REPO_ROOT / rel).exists(), rel
    print("M11V_routing_power_connectivity_verification_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
