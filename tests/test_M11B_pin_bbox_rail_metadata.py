from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M11B_pin_bbox_rail_metadata import run_m11b_pin_bbox_rail_metadata  # noqa: E402


def main() -> int:
    report = run_m11b_pin_bbox_rail_metadata(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m11ar_report=REPO_ROOT / "docs/M11AR_human_review_correction_report.json",
        m11ar_decision=REPO_ROOT / "docs/mapping/M11AR_corrected_hardmacro_substitution_decision.csv",
        module_gds_dir=REPO_ROOT / "outputs/openyield_module_gds",
        golden_reference=REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        m11a_pin_metadata=REPO_ROOT / "docs/mapping/M11A_pin_bbox_rail_metadata.csv",
        m11a_comparison=REPO_ROOT / "docs/mapping/M11A_module_vs_golden_leaf_comparison.csv",
        out_dir=REPO_ROOT / "outputs/M11B_pin_bbox_rail_metadata/current_supported_config",
        out_json=REPO_ROOT / "docs/M11B_pin_bbox_rail_metadata_report.json",
        out_report=REPO_ROOT / "docs/M11B_pin_bbox_rail_metadata_report.md",
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m11ar_gate_loaded"] is True
    assert report["candidate_modules_from_M11AR"] == ["sense_amp", "wordline_driver"]
    assert report["candidate_modules_processed"] == ["sense_amp", "wordline_driver"]
    assert report["module_count_processed"] == 2
    assert report["sense_amp_metadata_extracted"] is True
    assert report["wordline_driver_metadata_extracted"] is True
    assert report["pin_metadata_entry_count"] == 14
    assert report["rail_metadata_entry_count"] == 4
    assert report["machine_verified_item_count"] == 42
    assert report["human_review_required_item_count"] == 3
    assert report["sense_amp_ready_for_M11C"] is True
    assert report["wordline_driver_ready_for_M11C"] is False
    assert report["ready_for_M11C_modules"] == ["sense_amp"]
    assert report["not_ready_modules"] == ["wordline_driver"]
    assert report["requires_wrapper_count"] == 1
    assert report["contract_pin_count"] == 0
    assert report["verified_physical_pin_count"] == 11
    assert report["review_gds_generated"] is True
    assert report["review_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["can_claim_openyield_module_gds_hardmacro_substitution"] is False
    assert report["can_enter_M11C_after_this_gate"] is True
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False

    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M11B"
    assert status["can_claim_openyield_module_gds_hardmacro_substitution"] is False

    for rel in [
        "docs/M11B_pin_bbox_rail_metadata_report.json",
        "docs/M11B_pin_bbox_rail_metadata_report.md",
        "docs/evidence/M11B_pin_bbox_rail_metadata_summary.md",
        "docs/mapping/M11B_deep_pin_bbox_rail_metadata.csv",
        "docs/mapping/M11B_golden_alignment_matrix.csv",
        "docs/mapping/M11B_substitution_readiness_matrix.csv",
        "docs/mapping/M11B_wrapper_requirement_matrix.csv",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_deep_pin_bbox_rail_metadata.json",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_deep_pin_bbox_rail_metadata.csv",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_deep_pin_bbox_rail_metadata.md",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_sense_amp_metadata_report.json",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_sense_amp_metadata_report.md",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_wordline_driver_metadata_report.json",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_wordline_driver_metadata_report.md",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_golden_alignment_report.json",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_golden_alignment_report.md",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_wrapper_requirement_report.json",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_wrapper_requirement_report.md",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_substitution_readiness_report.json",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_substitution_readiness_report.md",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_machine_verification_report.json",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_machine_verification_report.md",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_human_review_required_items.md",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_review_gds_manifest.json",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_review_gds_manifest.md",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_pin_bbox_rail_metadata_review.gds",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_pin_bbox_rail_metadata_clean_review.gds",
        "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_pin_bbox_rail_metadata_annotated_debug.gds",
    ]:
        assert (REPO_ROOT / rel).exists(), rel
    print("M11B_pin_bbox_rail_metadata_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
