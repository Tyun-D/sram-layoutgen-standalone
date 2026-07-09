from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.M11C_sense_amp_smoke_substitution import run_m11c_sense_amp_smoke_substitution  # noqa: E402


def main() -> int:
    report = run_m11c_sense_amp_smoke_substitution(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        goal_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        progress_md=REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        m11bh_report=REPO_ROOT / "docs/M11BH_confirm_M11B_human_review_report.json",
        m11bh_scope=REPO_ROOT / "docs/mapping/M11BH_M11C_scope_lock.csv",
        m11b_report=REPO_ROOT / "docs/M11B_pin_bbox_rail_metadata_report.json",
        m11b_pin_metadata=REPO_ROOT / "docs/mapping/M11B_deep_pin_bbox_rail_metadata.csv",
        m11b_readiness=REPO_ROOT / "docs/mapping/M11B_substitution_readiness_matrix.csv",
        module_gds_dir=REPO_ROOT / "outputs/openyield_module_gds",
        baseline_gds=REPO_ROOT / "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds",
        golden_reference=REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        out_dir=REPO_ROOT / "outputs/M11C_sense_amp_smoke_substitution/current_supported_config",
        out_json=REPO_ROOT / "docs/M11C_sense_amp_smoke_substitution_report.json",
        out_report=REPO_ROOT / "docs/M11C_sense_amp_smoke_substitution_report.md",
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["progress_file_updated"] is True
    assert report["m11bh_gate_loaded"] is True
    assert report["m11c_scope_from_M11BH"] == "sense_amp_only"
    assert report["allowed_modules_from_M11BH"] == ["sense_amp"]
    assert report["sram_spec_generated"] is True
    assert report["sense_amp_openyield_gds_found"] is True
    assert report["sense_amp_openyield_gds_parsed"] is True
    assert report["sense_amp_metadata_loaded_from_M11B"] is True
    assert report["sense_amp_golden_target_found"] is True
    assert report["substitution_attempted"] is True
    assert report["substituted_modules"] == ["sense_amp"]
    assert report["excluded_modules_confirmed"] is True
    assert report["wordline_driver_substituted"] is False
    assert report["column_mux_substituted"] is False
    assert report["write_driver_substituted"] is False
    assert report["control_logic_substituted"] is False
    assert report["access_module_used"] is False
    assert report["floorplan_proxy_used"] is False
    assert report["arbitrary_scatter_used"] is False
    assert report["output_gds_generated"] is True
    assert report["output_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    assert report["can_claim_sense_amp_smoke_substitution_attempted"] is True
    assert report["can_claim_sense_amp_smoke_substitution_passed"] is True
    assert report["can_claim_openyield_module_gds_hardmacro_substitution"] is False
    assert report["top_bbox_match_status"] == "EXACT_MATCH"
    assert report["sense_amp_substitution_smoke_status"] == "SMOKE_SUBSTITUTION_PASS"

    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M11C"
    assert status["next_stage_allowed"] == "M11CH_CONFIRM_M11C_HUMAN_REVIEW"
    assert status["can_enter_next_stage_without_human_review"] is False

    for rel in [
        "docs/M11C_sense_amp_smoke_substitution_report.json",
        "docs/M11C_sense_amp_smoke_substitution_report.md",
        "docs/evidence/M11C_sense_amp_smoke_substitution_summary.md",
        "docs/mapping/M11C_sense_amp_substitution_manifest.csv",
        "docs/mapping/M11C_sense_amp_smoke_check_matrix.csv",
        "docs/mapping/M11C_sense_amp_diff_matrix.csv",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/SRAM_SPEC.json",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/SRAM_SPEC.md",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_sense_amp_substituted_sram.gds",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_sense_amp_substituted_sram_clean_review.gds",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_sense_amp_substituted_sram_annotated_debug.gds",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_sense_amp_substitution_manifest.json",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_sense_amp_substitution_manifest.md",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_sense_amp_substitution_diff_report.json",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_sense_amp_substitution_diff_report.md",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_sense_amp_smoke_check_report.json",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_sense_amp_smoke_check_report.md",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_machine_verification_report.json",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_machine_verification_report.md",
        "outputs/M11C_sense_amp_smoke_substitution/current_supported_config/M11C_human_review_required_items.md",
    ]:
        assert (REPO_ROOT / rel).exists(), rel
    print("M11C_sense_amp_smoke_substitution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
