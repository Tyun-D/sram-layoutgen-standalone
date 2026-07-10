from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M11D_post_sense_amp_analysis import (  # noqa: E402
    REAL_SUBSTITUTION_PROOF_STATUS,
    RECOMMENDED_NEXT_STAGE,
    run_m11d_post_sense_amp_analysis,
)


def main() -> int:
    report = run_m11d_post_sense_amp_analysis(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m11ch_report=REPO_ROOT / "docs/M11CH_confirm_M11C_human_review_report.json",
        m11ch_gate=REPO_ROOT / "docs/mapping/M11CH_M11D_entry_gate.csv",
        m11c_report=REPO_ROOT / "docs/M11C_sense_amp_smoke_substitution_report.json",
        m11c_manifest=REPO_ROOT / "docs/mapping/M11C_sense_amp_substitution_manifest.csv",
        m11c_smoke_check=REPO_ROOT / "docs/mapping/M11C_sense_amp_smoke_check_matrix.csv",
        m11c_diff=REPO_ROOT / "docs/mapping/M11C_sense_amp_diff_matrix.csv",
        m11b_readiness=REPO_ROOT / "docs/mapping/M11B_substitution_readiness_matrix.csv",
        m11b_wrapper=REPO_ROOT / "docs/mapping/M11B_wrapper_requirement_matrix.csv",
        m11ar_decision=REPO_ROOT / "docs/mapping/M11AR_corrected_hardmacro_substitution_decision.csv",
        baseline_gds=REPO_ROOT / "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds",
        m11c_gds=REPO_ROOT / "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_sense_amp_substituted_sram.gds",
        module_gds_dir=REPO_ROOT / "outputs/openyield_module_gds",
        out_dir=REPO_ROOT / "outputs/M11D_post_sense_amp_analysis/current_supported_config",
        out_json=REPO_ROOT / "docs/M11D_post_sense_amp_analysis_report.json",
        out_report=REPO_ROOT / "docs/M11D_post_sense_amp_analysis_report.md",
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m11ch_gate_loaded"] is True
    assert report["can_enter_M11D_from_M11CH"] is True
    assert report["baseline_gds_parsed"] is True
    assert report["m11c_gds_parsed"] is True
    assert report["m11c_scope_confirmed_sense_amp_only"] is True
    assert report["real_substitution_proof_status"] == REAL_SUBSTITUTION_PROOF_STATUS
    assert report["openyield_sense_amp_fingerprint_found_in_M11C"] is True
    assert report["label_only_substitution"] is False
    assert report["outside_placement_substitution"] is False
    assert report["top_bbox_match_status"] == "EXACT_MATCH"
    assert report["hierarchy_delta_status"] == "ONLY_SENSE_AMP_LEAF_FINGERPRINT_CHANGED"
    assert report["sense_amp_instance_count_before"] == 8
    assert report["sense_amp_instance_count_after"] == 8
    assert report["unexpected_non_sense_amp_change_count"] == 0
    assert report["access_module_used"] is False
    assert report["floorplan_proxy_used"] is False
    assert report["arbitrary_scatter_used"] is False
    assert report["wordline_driver_substituted"] is False
    assert report["column_mux_substituted"] is False
    assert report["write_driver_substituted"] is False
    assert report["control_logic_substituted"] is False
    assert report["machine_verified_item_count"] >= 27
    assert report["human_review_required_item_count"] == 0
    assert report["human_review_required_items"] == []
    assert report["sense_amp_substitution_analysis_status"] == "PASS_REAL_SUBSTITUTION_PROVEN"
    assert report["sense_amp_substitution_risk_level"] == "MEDIUM"
    assert report["recommended_next_stage"] == RECOMMENDED_NEXT_STAGE
    assert report["can_claim_sense_amp_smoke_substitution_passed"] is True
    assert report["can_claim_openyield_module_gds_hardmacro_substitution"] is False
    assert report["can_claim_drc_clean"] is False
    assert report["can_claim_lvs_clean"] is False
    assert report["can_claim_signoff_ready"] is False
    assert report["review_gds_generated"] is True
    assert report["review_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["remaining_M11D_blockers_count"] == 0
    assert report["human_klayout_review_required"] is False
    assert report["can_enter_next_stage_before_human_review"] is True

    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M11D"
    assert status["next_stage"] == RECOMMENDED_NEXT_STAGE
    assert status["next_stage_allowed"] == RECOMMENDED_NEXT_STAGE
    assert status["recommended_next_stage"] == RECOMMENDED_NEXT_STAGE
    assert status["real_substitution_proof_status"] == REAL_SUBSTITUTION_PROOF_STATUS
    assert status["remaining_M11D_blockers_count"] == 0
    assert status["can_enter_next_stage_without_human_review"] is True

    progress_text = (REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md").read_text(encoding="utf-8")
    assert "## M11D Post Analysis" in progress_text
    assert RECOMMENDED_NEXT_STAGE in progress_text

    for rel in [
        "docs/M11D_post_sense_amp_analysis_report.json",
        "docs/M11D_post_sense_amp_analysis_report.md",
        "docs/evidence/M11D_post_sense_amp_analysis_summary.md",
        "docs/mapping/M11D_real_substitution_proof.csv",
        "docs/mapping/M11D_baseline_vs_M11C_geometry_delta.csv",
        "docs/mapping/M11D_hierarchy_delta_matrix.csv",
        "docs/mapping/M11D_sense_amp_local_region_delta.csv",
        "docs/mapping/M11D_next_stage_decision.csv",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_post_sense_amp_analysis_report.json",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_post_sense_amp_analysis_report.md",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_real_substitution_proof.json",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_real_substitution_proof.md",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_baseline_vs_M11C_geometry_delta.json",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_baseline_vs_M11C_geometry_delta.md",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_hierarchy_delta_report.json",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_hierarchy_delta_report.md",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_sense_amp_local_region_delta.json",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_sense_amp_local_region_delta.md",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_unexpected_change_report.json",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_unexpected_change_report.md",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_next_stage_decision.json",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_next_stage_decision.md",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_machine_verification_report.json",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_machine_verification_report.md",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_human_review_required_items.md",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_post_sense_amp_analysis_review.gds",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_post_sense_amp_analysis_clean_review.gds",
        "outputs/M11D_post_sense_amp_analysis/current_supported_config/M11D_post_sense_amp_analysis_annotated_debug.gds",
    ]:
        assert (REPO_ROOT / rel).exists(), rel

    print("M11D_post_sense_amp_analysis_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
