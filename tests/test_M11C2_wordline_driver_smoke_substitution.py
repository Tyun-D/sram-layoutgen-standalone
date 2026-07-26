from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M11C2_wordline_driver_smoke_substitution import run_m11c2_wordline_driver_smoke_substitution  # noqa: E402


def main() -> None:
    report = run_m11c2_wordline_driver_smoke_substitution(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        goal_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m11w_report=REPO_ROOT / "docs/M11W_wordline_driver_wrapper_pin_repair_report.json",
        m11w_repaired_metadata=REPO_ROOT / "docs/mapping/M11W_wordline_driver_repaired_metadata.csv",
        m11w_readiness=REPO_ROOT / "docs/mapping/M11W_wordline_driver_readiness_matrix.csv",
        m11w_wrapper_manifest=REPO_ROOT / "docs/mapping/M11W_wordline_driver_wrapper_manifest.csv",
        wordline_driver_wrapper=REPO_ROOT / "outputs/M11W_wordline_driver_wrapper_pin_repair/current_supported_config/M11W_wordline_driver_wrapper_candidate.gds",
        baseline_gds=REPO_ROOT / "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds",
        golden_reference=REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        out_dir=REPO_ROOT / "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config",
        out_json=REPO_ROOT / "docs/M11C2_wordline_driver_smoke_substitution_report.json",
        out_report=REPO_ROOT / "docs/M11C2_wordline_driver_smoke_substitution_report.md",
    )

    assert report["m11w_gate_loaded"] is True
    assert report["m11w_wordline_driver_ready"] is True
    assert report["sram_spec_generated"] is True
    assert report["wordline_driver_wrapper_gds_found"] is True
    assert report["wordline_driver_wrapper_gds_parsed"] is True
    assert report["wordline_driver_metadata_loaded_from_M11W"] is True
    assert report["wordline_driver_golden_target_found"] is True
    assert report["substitution_attempted"] is True
    assert report["substituted_modules"] == ["wordline_driver"]
    assert report["excluded_modules_confirmed"] is True
    assert report["sense_amp_substituted"] is False
    assert report["column_mux_substituted"] is False
    assert report["write_driver_substituted"] is False
    assert report["control_logic_substituted"] is False
    assert report["access_module_used"] is False
    assert report["floorplan_proxy_used"] is False
    assert report["arbitrary_scatter_used"] is False
    assert report["output_gds_generated"] is True
    assert report["output_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["top_bbox_match_status"] == "EXACT_MATCH"
    assert report["real_substitution_proof_status"] == "PASS_WRAPPER_DGS_GEOMETRY_MATCH"
    assert report["openyield_wordline_driver_fingerprint_found_in_M11C2"] is True
    assert report["label_only_substitution"] is False
    assert report["outside_placement_substitution"] is False
    assert report["unexpected_non_wordline_driver_change_count"] == 0
    assert report["wordline_driver_substitution_smoke_status"] == "SMOKE_SUBSTITUTION_PASS"
    assert report["can_claim_wordline_driver_smoke_substitution_attempted"] is True
    assert report["can_claim_wordline_driver_smoke_substitution_passed"] is True
    assert report["can_claim_openyield_module_gds_hardmacro_substitution"] is False
    assert report["remaining_M11C2_blockers_count"] == 3
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False

    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M11C2"
    assert status["next_stage_allowed"] == "M11C2H_CONFIRM_M11C2_HUMAN_REVIEW"
    assert status["can_claim_wordline_driver_smoke_substitution_attempted"] is True
    assert status["can_claim_wordline_driver_smoke_substitution_passed"] is True

    progress = (REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md").read_text(encoding="utf-8")
    assert "## M11C2 Wordline Driver Smoke Substitution" in progress

    required_paths = [
        "docs/M11C2_wordline_driver_smoke_substitution_report.json",
        "docs/M11C2_wordline_driver_smoke_substitution_report.md",
        "docs/evidence/M11C2_wordline_driver_smoke_substitution_summary.md",
        "docs/mapping/M11C2_wordline_driver_substitution_manifest.csv",
        "docs/mapping/M11C2_wordline_driver_smoke_check_matrix.csv",
        "docs/mapping/M11C2_wordline_driver_diff_matrix.csv",
        "docs/mapping/M11C2_real_substitution_proof.csv",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/SRAM_SPEC.json",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/SRAM_SPEC.md",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_wordline_driver_substituted_sram.gds",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_wordline_driver_substituted_sram_clean_review.gds",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_wordline_driver_substituted_sram_annotated_debug.gds",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_wordline_driver_substitution_manifest.json",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_wordline_driver_substitution_manifest.md",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_wordline_driver_substitution_diff_report.json",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_wordline_driver_substitution_diff_report.md",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_wordline_driver_smoke_check_report.json",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_wordline_driver_smoke_check_report.md",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_real_substitution_proof.json",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_real_substitution_proof.md",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_machine_verification_report.json",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_machine_verification_report.md",
        "outputs/M11C2_wordline_driver_smoke_substitution/current_supported_config/M11C2_human_review_required_items.md",
    ]
    for rel in required_paths:
        assert (REPO_ROOT / rel).exists(), rel

    print("M11C2_wordline_driver_smoke_substitution_ok")


if __name__ == "__main__":
    main()
