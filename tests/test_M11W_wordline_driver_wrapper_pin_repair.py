from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M11W_wordline_driver_wrapper_pin_repair import (  # noqa: E402
    M11W_SCOPE,
    NEXT_STAGE_ALLOWED,
    REPAIR_STRATEGY_USED,
    run_m11w_wordline_driver_wrapper_pin_repair,
)


def main() -> int:
    report = run_m11w_wordline_driver_wrapper_pin_repair(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m11d_report=REPO_ROOT / "docs/M11D_post_sense_amp_analysis_report.json",
        m11d_next=REPO_ROOT / "docs/mapping/M11D_next_stage_decision.csv",
        m11b_report=REPO_ROOT / "docs/M11B_pin_bbox_rail_metadata_report.json",
        m11b_pin_metadata=REPO_ROOT / "docs/mapping/M11B_deep_pin_bbox_rail_metadata.csv",
        m11b_readiness=REPO_ROOT / "docs/mapping/M11B_substitution_readiness_matrix.csv",
        m11b_wrapper=REPO_ROOT / "docs/mapping/M11B_wrapper_requirement_matrix.csv",
        m11a_pin_metadata=REPO_ROOT / "docs/mapping/M11A_pin_bbox_rail_metadata.csv",
        m11a_comparison=REPO_ROOT / "docs/mapping/M11A_module_vs_golden_leaf_comparison.csv",
        module_gds_dir=REPO_ROOT / "outputs/openyield_module_gds",
        golden_reference=REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        baseline_gds=REPO_ROOT / "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds",
        out_dir=REPO_ROOT / "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config",
        out_json=REPO_ROOT / "docs/M11W_wordline_driver_wrapper_pin_repair_report.json",
        out_report=REPO_ROOT / "docs/M11W_wordline_driver_wrapper_pin_repair_report.md",
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m11d_report_loaded"] is True
    assert report["m11d_recommended_next_stage"] == "M11W_WORDLINE_DRIVER_WRAPPER_PIN_REPAIR"
    assert report["m11w_scope"] == M11W_SCOPE
    assert report["wordline_driver_openyield_gds_found"] is True
    assert report["wordline_driver_openyield_gds_parsed"] is True
    assert report["golden_wordline_driver_target_found"] is True
    assert report["repair_strategy_attempted"] is True
    assert report["repair_strategy_used"] == REPAIR_STRATEGY_USED
    assert report["dgs_pins_resolved"] is True
    assert report["unresolved_pin_count"] == 0
    assert report["unresolved_pins"] == []
    assert report["wrapper_required_before"] is True
    assert report["wrapper_generated"] is True
    assert report["wrapper_gds_parsed"] is True
    assert report["wrapper_required_after"] is False
    assert report["pin_metadata_entry_count_before"] == 8
    assert report["pin_metadata_entry_count_after"] == 8
    assert report["placement_safe_after_repair"] is True
    assert report["routing_safe_after_repair"] is True
    assert report["power_safe_after_repair"] is True
    assert report["wordline_driver_ready_for_smoke_substitution"] is True
    assert report["machine_verified_item_count"] >= 22
    assert report["human_review_required_item_count"] == 0
    assert report["human_review_required_items"] == []
    assert report["can_claim_wordline_driver_pin_repair_completed"] is True
    assert report["can_claim_wordline_driver_smoke_substitution_ready"] is True
    assert report["can_claim_openyield_module_gds_hardmacro_substitution"] is False
    assert report["can_claim_drc_clean"] is False
    assert report["can_claim_lvs_clean"] is False
    assert report["can_claim_signoff_ready"] is False
    assert report["review_gds_generated"] is True
    assert report["review_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["remaining_M11W_blockers_count"] == 0
    assert report["human_klayout_review_required"] is False
    assert report["can_enter_next_stage_before_human_review"] is True
    assert report["next_stage_allowed"] == NEXT_STAGE_ALLOWED

    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M11W"
    assert status["next_stage"] == NEXT_STAGE_ALLOWED
    assert status["next_stage_allowed"] == NEXT_STAGE_ALLOWED
    assert status["wordline_driver_dgs_pins_resolved"] is True
    assert status["wordline_driver_ready_for_smoke_substitution"] is True
    assert status["can_claim_wordline_driver_pin_repair_completed"] is True
    assert status["can_claim_wordline_driver_smoke_substitution_ready"] is True

    progress_text = (REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md").read_text(encoding="utf-8")
    assert "## M11W Wordline Driver Repair" in progress_text
    assert NEXT_STAGE_ALLOWED in progress_text

    for rel in [
        "docs/M11W_wordline_driver_wrapper_pin_repair_report.json",
        "docs/M11W_wordline_driver_wrapper_pin_repair_report.md",
        "docs/evidence/M11W_wordline_driver_wrapper_pin_repair_summary.md",
        "docs/mapping/M11W_wordline_driver_repaired_metadata.csv",
        "docs/mapping/M11W_wordline_driver_pin_alignment_matrix.csv",
        "docs/mapping/M11W_wordline_driver_readiness_matrix.csv",
        "docs/mapping/M11W_wordline_driver_wrapper_manifest.csv",
        "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config/M11W_wordline_driver_pin_repair_report.json",
        "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config/M11W_wordline_driver_original_metadata.json",
        "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config/M11W_wordline_driver_repaired_metadata.csv",
        "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config/M11W_wordline_driver_wrapper_requirement_report.json",
        "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config/M11W_wordline_driver_readiness_report.json",
        "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config/M11W_machine_verification_report.json",
        "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config/M11W_human_review_required_items.md",
        "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config/M11W_wordline_driver_wrapper_candidate.gds",
        "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config/M11W_wordline_driver_wrapper_candidate_clean_review.gds",
        "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config/M11W_wordline_driver_wrapper_candidate_annotated_debug.gds",
        "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config/M11W_wordline_driver_wrapper_manifest.json",
        "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config/M11W_wordline_driver_wrapper_manifest.md",
    ]:
        assert (REPO_ROOT / rel).exists(), rel

    print("M11W_wordline_driver_wrapper_pin_repair_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
